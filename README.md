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

The ELK stack and the API run as separate compose projects. Filebeat runs as a sidecar alongside the API and ships logs to Elasticsearch over the host network.

### Start

```bash
# 1. Start ELK (Elasticsearch + Kibana)
docker compose -f infra/docker-compose.elk.yml up -d

# 2. Start the API + Filebeat sidecar
docker compose -f infra/docker-compose.api.yml up --build
```

Omit `--build` on subsequent API starts unless `infra/Dockerfile` or `pyproject.toml` has changed.

Services:
| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Kibana | http://localhost:5601 |
| Elasticsearch | http://localhost:9200 |

### Pointing Filebeat at a remote Elasticsearch

By default Filebeat ships to `host.docker.internal:9200` (i.e. the local ELK compose stack). To use a managed ES cluster instead, set the environment variables before starting the API compose:

```bash
ELASTICSEARCH_HOST=my-cluster.es.io ELASTICSEARCH_PORT=443 \
  docker compose -f infra/docker-compose.api.yml up --build
```

### First-time Kibana setup

1. Open Kibana → **Stack Management → Data Views → Create data view**
2. Name: `storylord-*`, Timestamp field: `@timestamp`
3. Go to **Discover** to query logs

### How it works

- The API runs with `LOG_FORMAT=json`, emitting structured JSON to stdout
- Docker captures stdout via its default log driver
- Filebeat (sidecar in the API compose) reads `/var/lib/docker/containers/*/*.log` via the host Docker socket, filters to containers whose name contains `storylord`, and ships to Elasticsearch
- Uvicorn logger config (`infra/uvicorn_log_config.json`) propagates uvicorn logs through the root structlog handler so they share the same JSON format

### Stop

```bash
docker compose -f infra/docker-compose.api.yml down
docker compose -f infra/docker-compose.elk.yml down
```

Add `-v` to the ELK down command to also wipe the Elasticsearch data volume (indices, Kibana data views, etc.).

## Contributing

This project uses trunk-based development: work on short-lived branches off `main`. All changes require a pull request with at least one approval before merging. Linear history is enforced — your branch must be rebased on top of `main` before merging (no merge commits); CI will fail if the branch is not a fast-forward of `main`. Run `pdm run test` and `pdm run lint` locally before pushing.

See [docs/developer-workflow.md](docs/developer-workflow.md) for the full workflow.
