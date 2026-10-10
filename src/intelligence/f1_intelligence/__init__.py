"""Pace-change detection and trace comparison (interpretable first)."""

from f1_intelligence.plots import (
    clean_laps_by_code,
    lap_progression_png,
    speed_trace_png,
)

__all__ = ["clean_laps_by_code", "lap_progression_png", "speed_trace_png"]


def clean_lap_pace(lap_times: list[float]) -> float | None:
    """TODO(week 4): median of clean laps; exclude pit/interrupted laps."""
    raise NotImplementedError("pace intelligence not implemented")
