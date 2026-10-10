# Runbook (local)

```bash
make install && make test
make dev   # .env from example if missing; compose up --build in foreground —
           # logs stream here (temporal :7233, ui :8080, api :8000). Ctrl-C stops.
```

Second terminal while dev runs (or after `docker compose up -d`):

```bash
make logs                              # follow all services
docker compose logs -f worker          # one service
curl localhost:8000/health
```

- Worker-restart demo: `docker compose restart worker`, confirm no duplicate
  prediction keys (see tests/recovery/).
- Shutdown: `make compose-down` (also stops -v volumes). For AWS: follow
  infrastructure/aws/README.md shutdown procedure once provisioned.
