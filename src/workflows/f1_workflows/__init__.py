"""Temporal workflows + activities.

Reliability rules (spec): workflow code is deterministic — network, inference,
and storage live in activities. Stable workflow IDs, bounded retries,
Continue-As-New when history grows. Snapshots are stored outside history;
activities receive references + versions.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from f1_workflows.activities import (
        finalize_session,
        run_prediction_cycle,
        validate_snapshot,
    )
    from f1_workflows.search_attributes import (
        DriverPair,
        ModelVersion,
        SessionId,
        SnapshotVersion,
    )


@workflow.defn
class RaceSessionWorkflow:
    @workflow.run
    async def run(self, session_id: str) -> str:
        # Index the session before any side effect so operators can find a
        # stuck/running session even if activities never complete. Requires
        # `make temporal-setup` (custom SAs registered) — see docs.
        workflow.upsert_search_attributes(
            [
                SessionId.value_set(session_id),
                DriverPair.value_set("unassigned"),
                ModelVersion.value_set("baseline-v0"),
                SnapshotVersion.value_set("none"),
            ]
        )
        await workflow.execute_activity(
            validate_snapshot,
            session_id,
            schedule_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.execute_activity(
            run_prediction_cycle,
            session_id,
            schedule_to_close_timeout=timedelta(seconds=120),
        )
        return await workflow.execute_activity(
            finalize_session,
            session_id,
            schedule_to_close_timeout=timedelta(seconds=30),
        )
