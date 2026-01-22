#!/usr/bin/env bash
#
# Possible additions to this bootstrap script
#
#- Version checks: verify git, make, docker, docker-compose if you plan to use them.
#- PDM health checks: run pdm lock --check, pdm sync --dry-run, or pdm info after install.
#- Environment validation: confirm required env vars (e.g., ANTHROPIC_API_KEY) and fail with a clear message.
#- Dotenv guidance: detect empty .env keys and print a short checklist.
#- Pre-commit warm‑up: pdm run pre-commit run --all-files (optional, can be slow).
#- Test smoke: run a tiny import check or pytest -q to confirm the env works.
#- Cache cleanup: remove stale .venv or .ruff_cache if mismatched Python versions detected.
#- Runtime sanity: pdm run python -c "import ..." to validate core imports (langchain, pydantic, etc.).
#- Developer UX: print next steps (e.g., pdm run start, pdm run test) and helpful links.
#- Optional services: hook into make up / docker compose if you add infra.
#
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log() {
  printf "==> %s\n" "$*"
}

die() {
  printf "error: %s\n" "$*" >&2
  exit 1
}

have() {
  command -v "$1" >/dev/null 2>&1
}

PIPX_HOME="${PIPX_HOME:-$HOME/.local/pipx}"
PIPX_BIN_DIR="${PIPX_BIN_DIR:-$HOME/.local/bin}"
export PIPX_HOME
export PIPX_BIN_DIR
export PATH="$PIPX_BIN_DIR:$PATH"

PYTHON_BIN="${PYTHON_BIN:-python3.13}"

if ! have "$PYTHON_BIN"; then
  if have python3; then
    PYTHON_BIN="python3"
  fi
fi

if ! have "$PYTHON_BIN"; then
  die "Python 3.13 is required but was not found. Install it (e.g. via pyenv or asdf) and retry."
fi

PYTHON_VERSION="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$PYTHON_VERSION" != "3.13" ]]; then
  die "Python 3.13 is required. Found $PYTHON_VERSION at $PYTHON_BIN."
fi

PIPX_CMD="pipx"
if ! have pipx; then
  if "$PYTHON_BIN" -m pipx --version >/dev/null 2>&1; then
    PIPX_CMD="$PYTHON_BIN -m pipx"
  else
    log "pipx not found; bootstrapping with ensurepip/pip..."
    if "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
      "$PYTHON_BIN" -m pip install --user pipx
    elif "$PYTHON_BIN" -m ensurepip --version >/dev/null 2>&1; then
      "$PYTHON_BIN" -m ensurepip --upgrade
      "$PYTHON_BIN" -m pip install --user pipx
    else
      die "pipx is required to install pdm, but pip/ensurepip is unavailable. Install pipx via your system package manager and retry."
    fi

    if "$PYTHON_BIN" -m pipx --version >/dev/null 2>&1; then
      PIPX_CMD="$PYTHON_BIN -m pipx"
    elif have pipx; then
      PIPX_CMD="pipx"
    else
      die "pipx installation failed or is not on PATH. Ensure $PIPX_BIN_DIR is on PATH and retry."
    fi
  fi
fi

if ! have pdm; then
  log "pdm not found; installing with pipx..."
  $PIPX_CMD install pdm
fi

if ! have pdm; then
  die "pdm is still not available on PATH. Ensure pipx's bin directory is on PATH and retry."
fi

export PDM_VENV_IN_PROJECT=1

if [[ ! -d .venv ]]; then
  log "Creating virtual environment..."
  pdm venv create "$PYTHON_BIN"
fi

log "Installing dependencies ..."
pdm install

if [[ -f .env.example && ! -f .env ]]; then
  log "Creating .env from .env.example..."
  cp .env.example .env
  log "Populate .env with your ANTHROPIC_API_KEY before running the app."
fi

if [[ -f .pre-commit-config.yaml && -d .git && $(have git; echo $?) -eq 0 ]]; then
  log "Installing git hooks with pre-commit..."
  pdm run pre-commit install --install-hooks
fi

log "Bootstrap complete."
