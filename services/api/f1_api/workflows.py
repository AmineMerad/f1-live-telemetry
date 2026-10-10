"""Prediction panel backend: list Temporal workflows by F1 search attributes."""

import os

from fastapi import APIRouter, HTTPException
from temporalio.client import Client

router = APIRouter(prefix="/api")


@router.get("/workflows")
async def workflows(session_id: str | None = None, limit: int = 20) -> dict:
    """Workflows for a session (SessionId SA) or the most recent runs."""
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    try:
        client = await Client.connect(address)
    except Exception as e:
        raise HTTPException(
            503, f"temporal unreachable at {address}: {type(e).__name__}"
        ) from e
    query = f"SessionId = '{session_id}'" if session_id else ""
    out = []
    try:
        async for wf in client.list_workflows(query=query):
            out.append(
                {
                    "id": wf.id,
                    "status": wf.status.name if wf.status else "UNKNOWN",
                    "start_time": wf.start_time.isoformat() if wf.start_time else None,
                }
            )
            if len(out) >= limit:
                break
    except Exception as e:
        raise HTTPException(500, f"visibility query failed: {e}") from e
    return {"query": query or "(all)", "workflows": out}
