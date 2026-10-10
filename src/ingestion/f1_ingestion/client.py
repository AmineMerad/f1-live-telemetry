"""OpenF1 REST client with OAuth2 auth, rate-limit politeness, and disk cache.

Auth (verified against https://openf1.org/auth.html, Oct 2026):
- Historical data is free without auth, EXCEPT while a live session is in
  progress — then even past sessions require an authenticated user.
- Authenticated: POST username+password (form-encoded) to /token, use the
  Bearer token for 1h, refresh before expiry. Credentials live in
  OPENF1_USERNAME / OPENF1_PASSWORD env vars only — never in git.

All responses are cached under data/raw/openf1/ so replay and evaluation are
reproducible and don't re-hit rate limits (authed: 6 req/s, 60 req/min).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import httpx

BASE_URL = "https://api.openf1.org"
TOKEN_URL = f"{BASE_URL}/token"
RESTRICTED_MARKER = "Live F1 session in progress"


class OpenF1RestrictedError(RuntimeError):
    """API refused: a live session is in progress, auth required (HTTP 402)."""


class OpenF1Auth:
    def __init__(
        self,
        username: str,
        password: str,
        refresh_margin_s: float = 300.0,
    ) -> None:
        self._username = username
        self._password = password
        self._margin = refresh_margin_s
        self._token = ""
        self._expires_at = 0.0

    @classmethod
    def from_env(cls) -> OpenF1Auth | None:
        user = os.environ.get("OPENF1_USERNAME", "")
        pw = os.environ.get("OPENF1_PASSWORD", "")
        return cls(user, pw) if user and pw else None

    def token(self) -> str:
        if not self._token or time.time() > self._expires_at - self._margin:
            self._refresh()
        return self._token

    def _refresh(self) -> None:
        resp = httpx.post(
            TOKEN_URL,
            data={"username": self._username, "password": self._password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30.0,
        )
        resp.raise_for_status()
        body = resp.json()
        self._token = body["access_token"]
        self._expires_at = time.time() + float(body.get("expires_in", 3600))


def is_restricted_response(body: dict) -> bool:
    return RESTRICTED_MARKER in str(body.get("detail", ""))


class OpenF1Client:
    def __init__(
        self,
        auth: OpenF1Auth | None = None,
        cache_dir: Path = Path("data/raw/openf1"),
    ) -> None:
        self._auth = auth
        self._cache = cache_dir
        self._cache.mkdir(parents=True, exist_ok=True)
        self._http = httpx.Client(base_url=f"{BASE_URL}/v1", timeout=30.0)

    def close(self) -> None:
        self._http.close()

    def _cache_path(self, endpoint: str, params: dict) -> Path:
        key = endpoint + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        digest = hashlib.sha256(key.encode()).hexdigest()[:16]
        safe = endpoint.strip("/").replace("/", "_") or "root"
        return self._cache / f"{safe}_{digest}.json"

    def get(
        self, endpoint: str, offline: bool = False, **params: object
    ) -> list[dict]:
        """GET endpoint with params; file-cached. offline=True never hits network."""
        path = self._cache_path(endpoint, dict(params))
        if path.exists() or offline:
            if not path.exists():
                raise FileNotFoundError(f"no cached response for {endpoint} {params}")
            return json.loads(path.read_text())
        headers = {"accept": "application/json"}
        if self._auth is not None:
            headers["Authorization"] = f"Bearer {self._auth.token()}"
        resp = self._http.get(endpoint, params=params, headers=headers)
        if resp.status_code == 402 or (
            resp.status_code == 200 and is_restricted_response(_try_json(resp))
        ):
            raise OpenF1RestrictedError(
                "OpenF1 restricted global access: live session in progress. "
                "Set OPENF1_USERNAME/OPENF1_PASSWORD or retry after the session."
            )
        resp.raise_for_status()
        data = resp.json()
        path.write_text(json.dumps(data))
        time.sleep(0.2)  # stay far under rate limits
        return data


def _try_json(resp: httpx.Response) -> dict:
    try:
        body = resp.json()
        return body if isinstance(body, dict) else {}
    except ValueError:
        return {}
