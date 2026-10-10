"""Stable idempotency keys for retry-safe prediction writes.

Key format (spec): session_id + driver_pair + snapshot_version + model_version.
Retried inference reuses the captured snapshot, never newer race state.
"""


def prediction_key(
    session_id: str,
    driver_pair: str,
    snapshot_version: str,
    model_version: str,
) -> str:
    return f"{session_id}:{driver_pair}:{snapshot_version}:{model_version}"
