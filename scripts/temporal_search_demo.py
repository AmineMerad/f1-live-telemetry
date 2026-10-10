"""Practical visibility demo: F1 custom search attributes end to end.

Requires the local stack (make dev) + registered attributes
(make temporal-setup). Starts demo session workflows carrying SessionId /
DriverPair / ModelVersion / SnapshotVersion, advances one snapshot version
mid-run, then answers operator questions via list queries:

- Which sessions are currently running?
- What is driver pair VER-NOR covered by, and at which snapshot?
- Which workflows ran model baseline-v0?

Usage: make search-demo
"""

import asyncio
import os
from datetime import timedelta

from f1_workflows.search_attributes import (
    DriverPair,
    ModelVersion,
    SessionId,
    SnapshotVersion,
)
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import SearchAttributePair, TypedSearchAttributes
from temporalio.worker import Worker


@activity.defn
async def record_snapshot(snapshot_version: str) -> str:
    return snapshot_version


@workflow.defn
class SessionIndexDemo:
    @workflow.run
    async def run(
        self, session_id: str, driver_pair: str, model_version: str
    ) -> str:
        workflow.upsert_search_attributes(
            [
                SessionId.value_set(session_id),
                DriverPair.value_set(driver_pair),
                ModelVersion.value_set(model_version),
                SnapshotVersion.value_set("snap-42"),
            ]
        )
        await workflow.execute_activity(
            record_snapshot,
            "snap-42",
            schedule_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.sleep(timedelta(seconds=8))  # stay Running for queries
        workflow.upsert_search_attributes(
            [SnapshotVersion.value_set("snap-43")]
        )
        return "demo-complete"


async def list_ids(client: Client, query: str) -> list[str]:
    return [wf.id async for wf in client.list_workflows(query=query)]


async def await_visible(
    client: Client, query: str, minimum: int = 1, timeout_s: float = 30.0
) -> list[str]:
    """Poll until ES visibility catches up (writes are eventually consistent)."""
    deadline = asyncio.get_running_loop().time() + timeout_s
    while True:
        ids = await list_ids(client, query)
        if len(ids) >= minimum or asyncio.get_running_loop().time() > deadline:
            return ids
        await asyncio.sleep(1.0)


QUERIES = [
    ("running sessions", "ExecutionStatus = 'Running'"),
    ("pair VER-NOR", "DriverPair = 'VER-NOR'"),
    ("model baseline-v0", "ModelVersion = 'baseline-v0'"),
]


async def main() -> None:
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(address)
    async with Worker(
        client,
        task_queue="f1-demo",
        workflows=[SessionIndexDemo],
        activities=[record_snapshot],
    ):
        handles = [
            await client.start_workflow(
                SessionIndexDemo.run,
                args=["monza-2024", "VER-NOR", "baseline-v0"],
                id="demo-monza-ver-nor",
                task_queue="f1-demo",
                search_attributes=TypedSearchAttributes(
                    [
                        SearchAttributePair(SessionId, "monza-2024"),
                        SearchAttributePair(DriverPair, "VER-NOR"),
                        SearchAttributePair(ModelVersion, "baseline-v0"),
                    ]
                ),
            ),
            await client.start_workflow(
                SessionIndexDemo.run,
                args=["monza-2024", "LEC-PIA", "baseline-v0"],
                id="demo-monza-lec-pia",
                task_queue="f1-demo",
                search_attributes=TypedSearchAttributes(
                    [
                        SearchAttributePair(SessionId, "monza-2024"),
                        SearchAttributePair(DriverPair, "LEC-PIA"),
                        SearchAttributePair(ModelVersion, "baseline-v0"),
                    ]
                ),
            ),
        ]
        await await_visible(client, "ExecutionStatus = 'Running'", minimum=2)
        for label, query in QUERIES:
            print(f"\n-- {label}: {query}")
            for wf_id in await list_ids(client, query):
                print(f"   {wf_id}")
        await asyncio.gather(*(h.result() for h in handles))
        final = [
            (
                "completed monza-2024",
                "ExecutionStatus = 'Completed' AND SessionId = 'monza-2024'",
            ),
            ("advanced snapshot", "SnapshotVersion = 'snap-43'"),
        ]
        for label, query in final:
            print(f"\n-- {label}: {query}")
            for wf_id in await await_visible(client, query, minimum=2):
                print(f"   {wf_id}")


if __name__ == "__main__":
    asyncio.run(main())
