"""Race-state reconstruction with freshness and data-quality indicators."""

from dataclasses import dataclass, field


@dataclass
class RaceState:
    session_id: str
    last_event_time: str | None = None
    gaps: dict[str, float] = field(default_factory=dict)
    freshness: str = "stale"
    quality: str = "unknown"


def apply_event(state: RaceState, event_type: str, source_time: str) -> RaceState:
    """TODO(week 3): fold timing/telemetry/race-control events into state."""
    state.last_event_time = source_time
    return state
