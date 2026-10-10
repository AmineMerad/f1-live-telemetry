"""Activities: all side effects live here (network, inference, storage)."""

from temporalio import activity


@activity.defn
async def validate_snapshot(session_id: str) -> str:
    raise NotImplementedError(f"validate_snapshot not implemented: {session_id}")


@activity.defn
async def run_prediction_cycle(session_id: str) -> str:
    raise NotImplementedError(f"run_prediction_cycle not implemented: {session_id}")


@activity.defn
async def finalize_session(session_id: str) -> str:
    return f"finalized:{session_id}"
