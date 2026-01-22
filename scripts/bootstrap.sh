#!/usr/bin/env bash
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

if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
  die "pip is not available for $PYTHON_BIN. Install pip and retry."
fi

if ! have pdm; then
  log "pdm not found; installing..."
  if have pipx; then
    pipx install pdm
  else
    "$PYTHON_BIN" -m pip install --user pdm
  fi
fi

if ! have pdm; then
  die "pdm is still not available on PATH. Ensure your user base bin directory is on PATH and retry."
fi

export PDM_VENV_IN_PROJECT=1

if [[ ! -d .venv ]]; then
  log "Creating virtual environment..."
  pdm venv create -p "$PYTHON_BIN"
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
