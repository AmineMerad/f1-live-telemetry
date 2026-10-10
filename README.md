# F1 Live Intelligence

> Status: planning / pre-implementation. This repo is a scaffold — no validated
> capabilities yet. Independent, non-commercial educational project, not
> affiliated with Formula 1, the FIA, or any team. Full spec:
> `f1-live-intelligence.md`.

Near-real-time system that detects driver pace changes, compares telemetry
patterns, and estimates head-to-head finish probabilities, orchestrated with
Temporal. See the spec for scope, interpretation boundaries, and the 8-week
roadmap.

## Layout (uv workspace mono-repo)

```text
.
├── src/                    # workspace libraries (importable packages)
│   ├── common/             # event envelope, config, prediction keys
│   ├── ingestion/          # OpenF1 client + normalization (live + replay path)
│   ├── race-state/         # race-state engine, freshness / quality
│   ├── features/           # versioned feature snapshots
│   ├── intelligence/       # pace-change detection, trace comparison
│   ├── prediction/         # baseline + model inference, idempotent writes
│   ├── workflows/          # Temporal workflows + activities (deterministic boundary)
│   └── replay/             # historical replay reader (event-time order, no future leak)
├── services/               # runnable entrypoints (each with its own Dockerfile)
│   ├── api/                # FastAPI: predictions, evidence, freshness
│   ├── worker/             # Temporal worker (workflows + activities)
│   └── ingestion/          # live/replay ingestion runtime
├── tests/                  # unit / integration / recovery
├── configs/                # non-secret configuration
├── infrastructure/aws/     # cost checklist + Terraform placeholder (not provisioned)
├── notebooks/              # offline exploration (FastF1/pandas)
└── docs/                   # architecture, data-rights, runbook
```

High-frequency ingestion and signal processing run **outside** Temporal.
Temporal coordinates session lifecycle, prediction cycles, and replay
evaluation. Never one workflow per telemetry sample.

## Quickstart

```bash
make install        # uv sync, Python 3.12 (needs ~/.local/bin on PATH for uv)
make test           # pytest
make dev            # postgres + elasticsearch + temporal + ui + api/worker/ingestion
make ui             # open http://localhost:8000/ui (data explorer)
make temporal-ui    # open http://localhost:8080 (workflows)
make compose-down   # stop everything including volumes
```

Local API: http://localhost:8000/health — `make dev` creates `.env` from
`.env.example` on first run.

## Commands

| Target | Description |
|---|---|
| `make install` | `uv sync --frozen --all-packages --group dev` |
| `make test` | `uv run pytest` |
| `make lint` | `uv run ruff check scripts src services tests` |
| `make api / worker / ingestion` | run one service locally (needs Temporal up for worker) |
| `make dev / compose-down / logs` | full local stack / tear down / follow logs |
| `make ui / temporal-ui` | open the data UI (:8000/ui) / Temporal UI (:8080) |
| `make replay SESSION_KEY=... [TELEMETRY_DRIVER=..]` | historical replay through the pipeline |
| `make plot SESSION_KEY=... PAIR=VER-NOR` | head-to-head PNGs into data/figures/ |
| `make temporal-setup / search-demo` | register search attributes / visibility demo |

## Docs

- `f1-live-intelligence.md` — full project spec (planning status, scope, roadmap)
- `docs/architecture.md` — why Temporal, what it does not do
- `docs/temporal-visibility.md` — Elasticsearch role, measured resources, drilled failure behavior
- `docs/data-rights.md` — provider terms checklist (recheck before publishing)
- `docs/runbook.md` — local run/stop procedures

## Budget / data warnings

- Under-USD-20/month is a **target, not an estimate**. Price compute, storage,
  networking, transfer, logging, Temporal, and live data before provisioning.
- Recheck OpenF1 terms, pricing, sampling vs. delivery cadence, and the
  CC BY-NC-SA non-commercial constraints before paying or publishing.
- Never commit `.env`, credentials, provider tokens, or raw datasets.

## Licence

Code: MIT (see `LICENSE`). Data-provider rights are separate: OpenF1 content
carries its own licence/terms (see `docs/data-rights.md`) — the MIT licence
covers this repo's code, not F1 data or branding.
