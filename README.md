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

## Contributing

This project uses trunk-based development: work on short-lived branches off `main`. All changes require a pull request with at least one approval before merging. Linear history is enforced — your branch must be rebased on top of `main` before merging (no merge commits); CI will fail if the branch is not a fast-forward of `main`. Run `pdm run test` and `pdm run lint` locally before pushing.

See [docs/developer-workflow.md](docs/developer-workflow.md) for the full workflow.
