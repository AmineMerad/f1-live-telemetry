# Temporal visibility: Elasticsearch role, resources, failure behavior

Verified 2026-10-10 against our exact pins: server `temporalio/auto-setup:1.22.4`,
UI `temporalio/ui:2.21.0`, `elasticsearch:7.17.9`, `postgres:15-alpine`.

## Role

Elasticsearch is the **visibility store**: it indexes workflow metadata
(default + custom search attributes) and answers list queries
(`DriverPair = 'VER-NOR'`, UI search bar, `/api/workflows`).
It holds no workflow state — history lives in Postgres.

Correction to an earlier claim: since server 1.20, **Postgres 12+ also
supports advanced visibility and custom search attributes** (namespace-scoped;
with ES they are global). ES is not the only path — it is our chosen path
for local learning (distributed-systems objective) and the documented
recommendation at production scale. With `ENABLE_ES=true`, the server
**requires** ES (setup creates the `temporal_visibility_v1_dev` index;
see failure drill below).

Custom attributes (`make temporal-setup`, also in `src/workflows/`):
`SessionId`, `DriverPair`, `ModelVersion`, `SnapshotVersion` (all Keyword).
Demo: `make search-demo`.

## Resources (idle, measured via `docker stats`)

| Container | Memory |
|---|---|
| elasticsearch | ~870 MB (dominant; `ES_JAVA_OPTS=-Xms512m -Xmx512m`) |
| api | ~130 MB |
| temporal | ~120 MB |
| postgres | ~77 MB |
| worker | ~41 MB |
| ingestion | ~16 MB |
| temporal-ui | ~8 MB |

ES is ~65% of the stack's memory. This is the main reason it stays
**local-only** (see AWS note).

## Failure behavior (drilled, not assumed)

1. **ES container stopped**: server keeps `running`; visibility reads fail
   fast with an explicit error (`... lookup elasticsearch ...: no such host`
   surfaced as API 500). UI workflow lists break; executions are unaffected.
2. **Starting a workflow while ES is down**: succeeds (`START_OK`) — the
   execution path does not depend on visibility writes.
3. **ES restarted**: lists work again within ~25s; workflows started during
   the outage appear normally (here: `RUNNING`, then terminated for cleanup).
4. **Writes are eventually consistent**: after completion/upsert, list results
   lag by seconds. `scripts/temporal_search_demo.py` polls for this reason.
   Never use visibility for control flow — operators and dashboards only.
5. **Bad server config is fatal fast**: a wrong `DYNAMIC_CONFIG_FILE_PATH`
   (we shipped one pointing at a file absent from the 1.22.4 image) makes the
   server exit during config validation. Fixed by removing the override.

## AWS note (kept separate per budget constraint)

No decision made; nothing provisioned. ES's ~870MB footprint plus persistence
is hard to fit in a sub-$20/mo single host alongside everything else —
Postgres visibility is the likely production path for the budget, at the cost
of namespace-scoped attributes and pre-allocated columns. Revisit after local
measurements of real prediction-cycle volume. See `infrastructure/aws/README.md`.
