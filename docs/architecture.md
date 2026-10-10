# Architecture (scaffold — see f1-live-intelligence.md for the full spec)

```text
OpenF1 live feed / historical replay
              → ingestion (owns stream + checkpoints, outside Temporal)
              → normalized events + race-state engine (freshness/quality)
              → telemetry features + pace intelligence
              → versioned feature snapshots (outside workflow history)
              → Temporal: RaceSessionWorkflow → prediction activities
              → prediction store (idempotent writes) → FastAPI → dashboard
raw events + predictions → S3 → offline evaluation
```

## Why Temporal (and what it does NOT do)
- Coordinates session lifecycle, prediction scheduling, health checks,
  finalization, and replay evaluation — with retries, timeouts, recovery.
- Does NOT ingest the stream, hold telemetry samples in history, or recover
  data the ingestion service missed. One workflow per session, not per sample.
- Prediction cycles start as activities; a `PredictionCycleWorkflow` is only
  introduced if independent recovery/parallelism justifies it.
