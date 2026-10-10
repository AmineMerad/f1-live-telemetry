"""Normalized event envelope (spec section: Event and state design)."""

from datetime import datetime

from pydantic import BaseModel, Field


class NormalizedEvent(BaseModel):
    event_id: str
    session_id: str
    driver_id: str | None = None
    event_type: str
    source_timestamp: datetime
    received_at: datetime
    schema_version: str = "1"
    payload: dict = Field(default_factory=dict)
