"""Integration: replay preserves event-time order and hides the future."""

from datetime import UTC, datetime

from f1_common.events import NormalizedEvent
from f1_replay import order_for_replay, visible_at


def _evt(eid: str, hour: int) -> NormalizedEvent:
    return NormalizedEvent(
        event_id=eid,
        session_id="s",
        event_type="timing",
        source_timestamp=datetime(2024, 5, 1, hour, tzinfo=UTC),
        received_at=datetime(2024, 5, 1, hour, tzinfo=UTC),
    )


def test_replay_no_future_leak() -> None:
    shuffled = [_evt("c", 14), _evt("a", 12), _evt("b", 13)]
    ordered = order_for_replay(shuffled)
    assert [e.event_id for e in ordered] == ["a", "b", "c"]
    cutoff = datetime(2024, 5, 1, 13, tzinfo=UTC).isoformat()
    assert [e.event_id for e in visible_at(ordered, cutoff)] == ["a", "b"]
