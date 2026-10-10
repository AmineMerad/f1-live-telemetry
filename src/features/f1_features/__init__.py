"""Versioned feature snapshot attached to each prediction cycle."""

from pydantic import BaseModel, Field


class FeatureSnapshot(BaseModel):
    snapshot_id: str
    snapshot_version: str
    event_time_cutoff: str
    driver_pair: str
    features: dict = Field(default_factory=dict)
    missingness: dict[str, bool] = Field(default_factory=dict)
    freshness: str = "unknown"
    quality: str = "unknown"
    pipeline_version: str = "v0"
