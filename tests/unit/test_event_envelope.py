"""Unit: event envelope carries source vs. arrival time distinctly."""

from datetime import UTC, datetime

from f1_common.events import NormalizedEvent


def test_envelope_source_vs_arrival() -> None:
    e = NormalizedEvent(
        event_id="evt-1",
        session_id="s-2024-test",
        driver_id="VER",
        event_type="telemetry",
        source_timestamp=datetime(2024, 5, 1, 12, 0, 0, tzinfo=UTC),
        received_at=datetime(2024, 5, 1, 12, 0, 3, tzinfo=UTC),
        payload={"speed": 312.0},
    )
    assert e.source_timestamp < e.received_at
    assert e.schema_version == "1"
