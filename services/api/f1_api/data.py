"""Data routes: sessions lookup, drivers, lap tables, telemetry, plots."""

import os
from pathlib import Path

from f1_ingestion import OpenF1Auth, OpenF1Client, drivers_to_map
from f1_intelligence import clean_laps_by_code, lap_progression_png, speed_trace_png
from fastapi import APIRouter, HTTPException, Response

router = APIRouter(prefix="/api")


def _client() -> OpenF1Client:
    return OpenF1Client(
        auth=OpenF1Auth.from_env(),
        cache_dir=Path(os.environ.get("CACHE_DIR", "data/raw/openf1")),
    )


def _num_by_code(session_key: str, pair: str) -> dict[str, str]:
    client = _client()
    try:
        drivers = client.get("drivers", session_key=session_key)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    finally:
        client.close()
    wanted = pair.split("-")
    num_by_code = {c: n for n, c in drivers_to_map(drivers).items() if c in wanted}
    if len(num_by_code) != 2:
        raise HTTPException(404, f"pair {pair} not found in session {session_key}")
    return num_by_code


@router.get("/sessions")
def sessions(year: int, location: str) -> list[dict]:
    client = _client()
    try:
        rows = client.get("sessions", year=year, location=location)
    finally:
        client.close()
    return [
        {
            "session_key": r["session_key"],
            "session_name": r.get("session_name"),
            "session_type": r.get("session_type"),
            "location": r.get("location"),
            "date_start": r.get("date_start"),
        }
        for r in rows
    ]


@router.get("/session/{session_key}/drivers")
def drivers(session_key: str) -> list[dict]:
    client = _client()
    try:
        rows = client.get("drivers", session_key=session_key)
    finally:
        client.close()
    return [
        {
            "driver_number": r["driver_number"],
            "acronym": r.get("name_acronym"),
            "team": r.get("team_name"),
        }
        for r in rows
    ]


@router.get("/session/{session_key}/laps")
def laps(session_key: str, pair: str) -> dict:
    """Clean-lap table for a pair, with pit-out flags and deltas."""
    num_by_code = _num_by_code(session_key, pair)
    a_code, b_code = pair.split("-")
    client = _client()
    try:
        rows = client.get("laps", session_key=session_key)
    finally:
        client.close()
    by_num: dict[str, dict[int, dict]] = {}
    for lap in rows:
        by_num.setdefault(str(lap["driver_number"]), {})[lap["lap_number"]] = lap
    a_laps = by_num.get(num_by_code[a_code], {})
    b_laps = by_num.get(num_by_code[b_code], {})
    table = []
    for n in sorted(set(a_laps) | set(b_laps)):
        a, b = a_laps.get(n), b_laps.get(n)
        da = a.get("lap_duration") if a and not a.get("is_pit_out_lap") else None
        db = b.get("lap_duration") if b and not b.get("is_pit_out_lap") else None
        table.append(
            {
                "lap_number": n,
                a_code: da,
                b_code: db,
                "delta": round(da - db, 3) if da and db else None,
                "pit_out": bool(
                    (a and a.get("is_pit_out_lap")) or (b and b.get("is_pit_out_lap"))
                ),
            }
        )
    return {"pair": pair, "laps": table}


@router.get("/session/{session_key}/telemetry")
def telemetry(session_key: str, driver_number: str) -> dict:
    client = _client()
    try:
        rows = client.get(
            "car_data", session_key=session_key, driver_number=driver_number
        )
    finally:
        client.close()
    speeds = [r["speed"] for r in rows if r.get("speed") is not None]
    full = sum(1 for r in rows if r.get("throttle") == 100)
    braking = sum(1 for r in rows if (r.get("brake") or 0) > 0)
    return {
        "samples": len(rows),
        "top_speed": max(speeds) if speeds else None,
        "full_throttle_share": round(full / len(rows), 3) if rows else 0,
        "braking_share": round(braking / len(rows), 3) if rows else 0,
    }


@router.get("/session/{session_key}/plot")
def plot(session_key: str, pair: str, kind: str = "laps") -> Response:
    num_by_code = _num_by_code(session_key, pair)
    client = _client()
    try:
        laps = client.get("laps", session_key=session_key)
        if kind == "laps":
            png = lap_progression_png(laps, num_by_code, session_key, pair)
        elif kind == "speed":
            _, fastest = clean_laps_by_code(laps, num_by_code)
            car_by_code = {
                code: client.get(
                    "car_data", session_key=session_key, driver_number=num
                )
                for code, num in num_by_code.items()
            }
            png = speed_trace_png(car_by_code, fastest, pair)
        else:
            raise HTTPException(400, "kind must be laps or speed")
    finally:
        client.close()
    return Response(content=png, media_type="image/png")
