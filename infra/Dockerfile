FROM python:3.13-slim
WORKDIR /app

RUN pip install --no-cache-dir pdm

COPY pyproject.toml pdm.lock ./
RUN pdm install --no-self

ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"
