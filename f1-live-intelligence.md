# F1 Live Intelligence

A portfolio project combining Formula 1 telemetry intelligence, live head-to-head predictions, and durable workflow orchestration with Temporal on AWS.

> Status: planning / pre-implementation. This README describes the intended MVP, not implemented or validated capabilities. This is an independent, non-commercial educational project, not affiliated with Formula 1, the FIA, or any team.

## Project goal

Build a near-real-time system that detects changes in driver pace, compares telemetry patterns, and estimates the probability that one selected driver finishes ahead of another.

The project emphasizes reproducible analysis, streaming-state correctness, calibrated predictions, and recovery from failures—not guaranteed race predictions or vehicle diagnostics.

**Target:** a focused solo MVP in 6–8 weeks, using Python, ML, Temporal, and AWS.

**Budget target:** under USD 20/month including live data. Deployment feasibility and current service pricing must be verified before provisioning.

## MVP scope

- Historical race replay through the same processing pipeline used for live sessions.
- Live ingestion and normalization of available timing, telemetry, and race events.
- Race-state reconstruction with freshness and data-quality indicators.
- Pace-change detection and comparisons between selected drivers.
- Speed, throttle, brake, and gear trace comparisons for selected laps.
- Continuously updated head-to-head finish probabilities for a small set of driver pairs.
- A dashboard showing predictions, supporting features, uncertainty, and data freshness.
- Durable orchestration, retry-safe prediction writes, and a worker-restart demonstration.
- Historical evaluation against simple baselines.

### Out of scope

- Predicting the complete finishing order in the initial release.
- Mechanical fault diagnosis or direct measurement of tyre wear.
- High-frequency vehicle control or engineering-grade telemetry.
- Automated betting, financial actions, or commercial data redistribution.
- Kubernetes, managed Kafka, and a large distributed service fleet.

## Architecture

```text
OpenF1 live feed / historical replay
                  |
                  v
       Python ingestion service
                  |
                  v
    Normalized events + race-state engine
                  |
                  v
   Telemetry features + pace intelligence
                  |
                  v
      Versioned feature snapshots
                  |
                  v
 Temporal orchestration -> prediction activities
                  |
                  v
       Prediction store -> live dashboard

Raw events + predictions -> S3 -> offline evaluation
```

High-frequency ingestion and signal processing run outside Temporal. Temporal coordinates meaningful operations such as session lifecycle, prediction cycles, recovery, and replay evaluation.

Do not create one workflow per telemetry sample. Feature snapshots are stored outside workflow history; activities receive stable references and versions.

### Proposed stack

| Component | Proposed technology | Notes |
|---|---|---|
| Ingestion and analytics | Python | Shared event-processing path for live and replay |
| Durable orchestration | Temporal Python SDK | Workflow and activity boundaries kept explicit |
| Offline exploration | pandas / NumPy / FastF1 | Validate coverage before committing to features |
| Initial ML | Simple baseline, then gradient boosting | Select library after dataset validation |
| API | FastAPI | Proposed, not yet implemented |
| Dashboard | To be selected | Prioritize evidence and freshness over decorative charts |
| Event archive | Amazon S3 | Partition by session and data type |
| AWS compute | Small, time-bounded deployment | Size and price after measuring resource use |
| Temporal persistence | To be selected | Required for self-hosting; no production HA claim |

## Temporal design

### RaceSessionWorkflow

Coordinates session startup, prediction scheduling, health-check activities, and finalization. The external ingestion service owns its stream connection and checkpointing.

### Prediction cycles

Initially implemented as activities within the session workflow. Introduce a `PredictionCycleWorkflow` only if independent recovery or parallel execution justifies it.

Each cycle:

1. Captures a reference to a specific feature snapshot.
2. Validates input freshness and completeness.
3. Loads the specified model version and performs inference in an activity.
4. Persists a prediction using an idempotency key.
5. Makes the saved result available to the dashboard.

Proposed initial cadence: every 15–30 seconds, with selected event-triggered updates. This is a design choice, not a provider latency guarantee.

### ReplayEvaluationWorkflow

Coordinates replay of a historical session, collection of predictions, and generation of evaluation metrics. Replay must preserve event-time ordering and must not expose future race information to features or predictions.

### Reliability rules

- Keep workflow code deterministic: network calls, model inference, storage, and other side effects belong in activities.
- Use stable workflow IDs and prediction keys.
- Prediction key: `session_id + driver_pair + snapshot_version + model_version`.
- Retried inference uses the same captured snapshot, not newer race state.
- Configure bounded retries, timeouts, heartbeats where appropriate, and cancellation handling.
- Treat invalid data differently from transient service failures.
- Use Continue-As-New when necessary to bound workflow history.
- Use compatible workflow changes and explicit model versions.
- Never assume Temporal recovery restores telemetry that the ingestion service missed.

## Data sources and limitations

### OpenF1

Candidate primary source for historical and live data.

A preliminary check of its website on October 10, 2026 indicated:

- Historical sessions from 2023 onward.
- Paid live access via REST, MQTT, and WebSocket.
- Advertised sponsor pricing of EUR 9.90/month.
- Car telemetry sampled at approximately 3.7 Hz.
- Approximately three seconds of live delay.
- A listed CC BY-NC-SA licence and non-commercial usage constraints.

These details must be rechecked before implementation or payment. Sampling rate is not the same as delivery cadence or guaranteed latency. Verify field-level coverage, session availability, rate limits, authentication, subscription terms, and permitted publication separately.

Source: https://openf1.org/

### FastF1

Candidate tool for historical exploration and offline analysis. Its documentation describes lap timing, car telemetry, position, tyre, weather, and session data with caching.

Do not assume FastF1 is the live production feed. Verify its data rights and limitations separately from its software licence.

Source: https://docs.fastf1.dev/

### Interpretation boundaries

Public telemetry is limited and may be delayed, incomplete, or revised. Pace changes may reflect traffic, tyre management, fuel load, weather, strategy, or interruptions. Detected patterns are not proof of tyre degradation or mechanical faults.

Do not publish raw datasets, protected branding, or a commercial service until the relevant terms have been reviewed.

## Event and state design

Proposed normalized event envelope:

```json
{
  "event_id": "stable-source-or-derived-id",
  "session_id": "session-identifier",
  "driver_id": "driver-identifier-or-null",
  "event_type": "telemetry",
  "source_timestamp": "ISO-8601 timestamp",
  "received_at": "ISO-8601 timestamp",
  "schema_version": "1",
  "payload": {}
}
```

The engine must distinguish source time from arrival time and handle duplicate, late, missing, and out-of-order events. Record ingestion checkpoints and gaps. Define an explicit late-event policy before live deployment.

Feature snapshots include:

- Snapshot ID, version, and event-time cutoff.
- Driver-pair identity.
- Feature values and missingness indicators.
- Data freshness and quality status.
- Feature-pipeline version.

Predictions include the snapshot reference, model version, probability, creation time, quality status, and the final evaluation label once known.

## Telemetry intelligence

Start with interpretable methods:

- Distance-aligned lap trace comparisons.
- Recent clean-lap pace and relative pace trends.
- Exclusion or labeling of pit laps and interrupted laps.
- Traffic and race-control context where supported by the data.
- Persistent-change detection, followed by change-point methods if justified.

Anomaly thresholds and false-positive behavior must be evaluated rather than presented as validated by default.

## Prediction design

### Initial target

> Given the information available at this point in the race, what is the probability that driver A finishes ahead of driver B?

Define the outcome rules before training, including retirements, disqualifications, unclassified drivers, and post-race classification changes. Keep training and evaluation consistent with those rules.

### Candidate features

Subject to data availability:

- Current position and time gap.
- Recent relative clean-lap pace.
- Tyre compound and stint age.
- Remaining laps.
- Pit-stop history.
- Race-control state.
- Missingness and freshness indicators.

### Modeling sequence

1. Establish current-running-order and simple statistical baselines.
2. Build a small supervised model.
3. Compare gradient boosting with the baseline.
4. Calibrate probabilities using a separate validation set.
5. Evaluate on unseen, later races.

Feature contributions describe model behavior; they are not causal explanations.

## Evaluation

- Split chronologically by whole races, never random lap rows.
- Construct features only from information available at prediction time.
- Fit preprocessing and calibration without test-set leakage.
- Report Brier score, log loss, calibration, and baseline comparisons.
- Report metrics by race phase and data-quality state.
- Account for correlation between predictions from the same race; do not treat every timestamp as an independent trial.
- Track event-to-dashboard latency, stale-data duration, missing-event rates, and recovery time.
- Store replay configuration, model version, and dataset references for reproducibility.

## Deployment and budget

Develop locally first with Temporal and a Python worker. Select a tested local setup from the current Temporal documentation; setup commands will be added when the repository exists.

For AWS, prefer a small deployment operated during development sessions and race weekends. Keep application modules separate in code without requiring a separate managed service for each module.

The under-USD-20 budget is a target, not a verified estimate. Paid live data consumes a substantial portion. A self-hosted Temporal deployment adds database, memory, disk, backup, and maintenance requirements; Temporal Cloud requires a separate pricing review.

Before provisioning, price compute, storage, public networking, data transfer, logging, Temporal, and live data in the selected region. Add AWS budget alerts and explicit shutdown procedures. A single-node portfolio deployment must not be described as highly available or production-grade.

## Eight-week roadmap

| Week | Deliverable |
|---|---|
| 1 | Validate data coverage, terms, latency, deployment costs, and schemas |
| 2 | Historical ingestion and deterministic replay |
| 3 | Race-state reconstruction, freshness, and data-quality checks |
| 4 | Telemetry comparisons and pace-change detection |
| 5 | Head-to-head baseline and feature snapshots |
| 6 | Evaluation, calibration, Temporal prediction orchestration |
| 7 | AWS deployment, dashboard, reconnects, recovery testing |
| 8 | Live-session test, recorded demo, architecture write-up, results |

## First milestone acceptance criteria

- Replay one historical race through the event-processing pipeline.
- Start and complete a RaceSessionWorkflow.
- Produce versioned feature snapshots and saved head-to-head predictions.
- Restart a worker mid-run and resume without duplicate prediction records.
- Demonstrate stale-data handling and an activity failure/retry.
- Generate a reproducible evaluation report against a baseline.
- Run the replay without using future information.

## Proposed repository structure

```text
f1-live-intelligence/
├── README.md
├── src/
│   ├── ingestion/
│   ├── race_state/
│   ├── features/
│   ├── intelligence/
│   ├── prediction/
│   ├── workflows/
│   ├── activities/
│   ├── api/
│   └── replay/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── recovery/
├── notebooks/
├── configs/
├── infrastructure/
└── docs/
```

This structure is proposed; the directories and application do not yet exist. Installation, environment variables, and run commands will be documented once implemented and tested. Never commit credentials or provider tokens.

## Portfolio deliverables

- Architecture diagram explaining why Temporal is used.
- Historical replay demo available between race weekends.
- Live dashboard with evidence and freshness indicators.
- Worker-failure and recovery demonstration.
- Model evaluation report with baselines and limitations.
- Documented AWS costs and deployment trade-offs.

## Open decisions

- Exact AWS region and compute configuration.
- Self-hosted Temporal versus Temporal Cloud feasibility.
- Provider terms and permitted public presentation.
- Dashboard framework and prediction-store technology.
- Initial driver-pair selection and outcome-label policy.
- Model library, update cadence, and late-event policy.

## Licence and attribution

Project code licence: not selected yet. Data-provider licences and rights are separate from the code licence. Add required attribution and confirm redistribution permissions before publication.
