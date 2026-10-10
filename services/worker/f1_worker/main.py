"""Temporal worker entrypoint. Ingestion owns its stream + checkpoints;
the worker only runs workflows/activities."""

import asyncio
import os

from f1_workflows import RaceSessionWorkflow
from f1_workflows.activities import (
    finalize_session,
    run_prediction_cycle,
    validate_snapshot,
)
from temporalio.client import Client
from temporalio.worker import Worker


async def run() -> None:
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(address)
    async with Worker(
        client,
        task_queue="f1-session",
        workflows=[RaceSessionWorkflow],
        activities=[validate_snapshot, run_prediction_cycle, finalize_session],
    ):
        await asyncio.Future()  # run until cancelled


if __name__ == "__main__":
    asyncio.run(run())
