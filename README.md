# storylord-api-server

## Running the API Server

### Development

```bash
pdm run api
```

Starts the server with hot reload on `http://127.0.0.1:8000`.

### Production

**Single process:**
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

**Multiple workers (recommended):**
```bash
gunicorn -k uvicorn.workers.UvicornWorker api.app:app --workers 4 --bind 0.0.0.0:8000
```

Requires `gunicorn` to be installed (`pdm add gunicorn`).

## ELK Stack (Elasticsearch, Logstash, Kibana)

The full ELK stack runs the API in a container alongside Elasticsearch, Kibana, and Filebeat, with structured JSON logs routed via Docker's log driver.

### Start

```bash
docker compose -f infra/docker-compose.elk.yml up --build
```

Omit `--build` on subsequent runs unless `infra/Dockerfile` or `pyproject.toml` has changed.

Services:
| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Kibana | http://localhost:5601 |
| Elasticsearch | http://localhost:9200 |

### First-time Kibana setup

1. Open Kibana → **Stack Management → Data Views → Create data view**
2. Name: `storylord-*`, Timestamp field: `@timestamp`
3. Go to **Discover** to query logs

### How it works

- The API runs with `LOG_FORMAT=json`, emitting structured JSON to stdout
- Docker captures stdout via its default log driver
- Filebeat reads `/var/lib/docker/containers/*/*.log`, filters to containers whose name contains `storylord`, and ships to Elasticsearch
- Uvicorn logger config (`infra/uvicorn_log_config.json`) propagates uvicorn logs through the root structlog handler so they share the same JSON format

### Stop

```bash
docker compose -f infra/docker-compose.elk.yml down
```

Add `-v` to also wipe the Elasticsearch data volume (indices, Kibana data views, etc.).

## Contributing

This project uses trunk-based development: work on short-lived branches off `main`. All changes require a pull request with at least one approval before merging. Linear history is enforced — your branch must be rebased on top of `main` before merging (no merge commits); CI will fail if the branch is not a fast-forward of `main`. Run `pdm run test` and `pdm run lint` locally before pushing.

See [docs/developer-workflow.md](docs/developer-workflow.md) for the full workflow.
