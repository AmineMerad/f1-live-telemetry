"""Head-to-head plots from OpenF1 lap + car-telemetry rows.

Pure functions over provider dicts (no network, no cache): callers fetch
rows with OpenF1Client and pass them in. Returns PNG bytes.
"""

from datetime import datetime, timedelta
from io import BytesIO

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


def clean_laps_by_code(
    laps: list[dict], num_by_code: dict[str, str]
) -> tuple[dict[str, list[tuple[int, float]]], dict[str, dict]]:
    """Clean laps per driver code + each driver's fastest clean lap row."""
    code_by_num = {v: k for k, v in num_by_code.items()}
    clean: dict[str, list[tuple[int, float]]] = {c: [] for c in num_by_code}
    fastest: dict[str, dict] = {}
    for lap in laps:
        code = code_by_num.get(str(lap["driver_number"]))
        if code is None or lap.get("is_pit_out_lap") or not lap.get("lap_duration"):
            continue
        clean[code].append((lap["lap_number"], lap["lap_duration"]))
        if code not in fastest or lap["lap_duration"] < fastest[code]["lap_duration"]:
            fastest[code] = lap
    for series in clean.values():
        series.sort()
    return clean, fastest


def lap_progression_png(
    laps: list[dict],
    num_by_code: dict[str, str],
    session_key: str,
    pair: str,
) -> bytes:
    clean, _ = clean_laps_by_code(laps, num_by_code)
    fig, ax = plt.subplots(figsize=(10, 4))
    for code, series in clean.items():
        ax.plot(
            [n for n, _ in series],
            [d for _, d in series],
            marker=".",
            label=f"{code} ({len(series)} clean laps)",
        )
    ax.set_xlabel("lap number")
    ax.set_ylabel("lap duration (s)")
    ax.set_title(f"Clean-lap pace: {pair} (session {session_key})")
    ax.legend()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return buf.getvalue()


def speed_trace_png(
    car_by_code: dict[str, list[dict]],
    fastest: dict[str, dict],
    pair: str,
) -> bytes:
    """Speed trace over each driver's fastest clean lap window."""
    fig, ax = plt.subplots(figsize=(10, 4))
    for code, rows in car_by_code.items():
        lap = fastest[code]
        start = _parse_ts(lap["date_start"])
        end = start + timedelta(seconds=lap["lap_duration"])
        window = [
            r
            for r in rows
            if start <= _parse_ts(r["date"]) <= end and r.get("speed") is not None
        ]
        if not window:
            continue
        t0 = _parse_ts(window[0]["date"])
        xs = [(_parse_ts(r["date"]) - t0).total_seconds() for r in window]
        ax.plot(xs, [r["speed"] for r in window], label=f"{code} lap {lap['lap_number']}")
    ax.set_xlabel("seconds into lap")
    ax.set_ylabel("speed (km/h)")
    ax.set_title(f"Speed trace on fastest clean lap: {pair}")
    ax.legend()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return buf.getvalue()
