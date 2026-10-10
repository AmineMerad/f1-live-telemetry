"""Map OpenF1 payloads to the normalized event envelope.

Source-time = provider timestamp (date_start). For historical replay,
received_at = source_timestamp (no delivery delay to model); live ingestion
sets received_at to arrival time so freshness math stays honest.
"""

from datetime import datetime

from f1_common.events import NormalizedEvent


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)  # 3.11+ handles trailing Z


def lap_to_event(session_key: int, lap: dict) -> NormalizedEvent:
    ts = _parse_ts(lap["date_start"])
    return NormalizedEvent(
        event_id=f"lap:{session_key}:{lap['driver_number']}:{lap['lap_number']}",
        session_id=str(session_key),
        driver_id=str(lap["driver_number"]),
        event_type="lap",
        source_timestamp=ts,
        received_at=ts,
        payload={
            "lap_number": lap["lap_number"],
            "lap_duration": lap.get("lap_duration"),
            "sector_1": lap.get("duration_sector_1"),
            "sector_2": lap.get("duration_sector_2"),
            "sector_3": lap.get("duration_sector_3"),
            "is_pit_out_lap": lap.get("is_pit_out_lap", False),
        },
    )


def session_to_event(session: dict) -> NormalizedEvent:
    ts = _parse_ts(session["date_start"])
    return NormalizedEvent(
        event_id=f"session:{session['session_key']}",
        session_id=str(session["session_key"]),
        driver_id=None,
        event_type="session",
        source_timestamp=ts,
        received_at=ts,
        payload={
            "session_name": session.get("session_name"),
            "session_type": session.get("session_type"),
            "location": session.get("location"),
            "date_end": session.get("date_end"),
        },
    )


def drivers_to_map(drivers: list[dict]) -> dict[str, str]:
    """Map driver_number (as str, matching NormalizedEvent.driver_id) to acronym."""
    return {str(d["driver_number"]): d["name_acronym"] for d in drivers}


def car_data_to_event(session_key: int, row: dict) -> NormalizedEvent:
    """One ~3.7Hz car-telemetry sample → event (speed/throttle/brake/gear)."""
    ts = _parse_ts(row["date"])
    return NormalizedEvent(
        event_id=f"tel:{session_key}:{row['driver_number']}:{row['date']}",
        session_id=str(session_key),
        driver_id=str(row["driver_number"]),
        event_type="telemetry",
        source_timestamp=ts,
        received_at=ts,
        payload={
            "speed": row.get("speed"),
            "throttle": row.get("throttle"),
            "brake": row.get("brake"),
            "n_gear": row.get("n_gear"),
            "rpm": row.get("rpm"),
            "drs": row.get("drs"),
        },
    )
