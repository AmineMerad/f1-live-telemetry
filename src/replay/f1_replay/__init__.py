"""Replay reader: event-time ordering with a no-future-leak guard."""

from f1_common.events import NormalizedEvent


def order_for_replay(events: list[NormalizedEvent]) -> list[NormalizedEvent]:
    """Sort by source_timestamp; ties broken by event_id for determinism."""
    return sorted(events, key=lambda e: (e.source_timestamp, e.event_id))


def visible_at(
    ordered: list[NormalizedEvent], cutoff: str
) -> list[NormalizedEvent]:
    """Return only events at or before the prediction cutoff (ISO-8601 string)."""
    return [e for e in ordered if e.source_timestamp.isoformat() <= cutoff]
