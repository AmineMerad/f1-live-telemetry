"""Unit: OpenF1 lap/session normalization (fixture-based, no network)."""

from f1_ingestion import (
    car_data_to_event,
    drivers_to_map,
    lap_to_event,
    session_to_event,
)
from f1_ingestion.client import is_restricted_response

LAP = {
    "date_start": "2024-09-01T13:05:12.345000+00:00",
    "driver_number": 1,
    "lap_number": 12,
    "lap_duration": 91.234,
    "duration_sector_1": 29.1,
    "duration_sector_2": 30.2,
    "duration_sector_3": 31.934,
    "is_pit_out_lap": False,
}

SESSION = {
    "session_key": 9165,
    "session_name": "Race",
    "session_type": "Race",
    "location": "Monza",
    "date_start": "2024-09-01T13:00:00+00:00",
    "date_end": "2024-09-01T14:30:00+00:00",
}


def test_lap_to_event() -> None:
    e = lap_to_event(9165, LAP)
    assert e.event_id == "lap:9165:1:12"
    assert e.session_id == "9165"
    assert e.driver_id == "1"
    assert e.event_type == "lap"
    assert e.source_timestamp.isoformat() == LAP["date_start"]
    assert e.payload["lap_duration"] == 91.234
    assert e.payload["is_pit_out_lap"] is False


def test_session_to_event() -> None:
    e = session_to_event(SESSION)
    assert e.event_id == "session:9165"
    assert e.driver_id is None
    assert e.payload["location"] == "Monza"


def test_restricted_marker_detected() -> None:
    assert is_restricted_response(
        {"detail": "Live F1 session in progress. Global API access restricted."}
    )
    assert not is_restricted_response({"detail": "ok"})
    assert not is_restricted_response({})


def test_drivers_to_map() -> None:
    drivers = [
        {"driver_number": 1, "name_acronym": "VER"},
        {"driver_number": 4, "name_acronym": "NOR"},
    ]
    assert drivers_to_map(drivers) == {"1": "VER", "4": "NOR"}


def test_car_data_to_event() -> None:
    row = {
        "date": "2024-09-01T12:21:09.495000+00:00",
        "driver_number": 1,
        "speed": 300,
        "throttle": 100,
        "brake": 0,
        "n_gear": 8,
        "rpm": 10648,
        "drs": 1,
    }
    e = car_data_to_event(9590, row)
    assert e.event_type == "telemetry"
    assert e.driver_id == "1"
    assert e.payload["speed"] == 300
    assert e.payload["throttle"] == 100
    assert e.payload["brake"] == 0
    assert e.payload["n_gear"] == 8
