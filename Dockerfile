ARG PYTHON_VERSION=3.13

# Base stage - Install Python and uv
FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-slim AS base

ARG PYTHON_VERSION

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_VERSION=0.6.9

# Install uv
RUN pip install --no-cache-dir uv==${UV_VERSION}

WORKDIR /app

# Builder stage - Install dependencies and build application
FROM base AS builder

ARG PYTHON_VERSION

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy all pyproject.toml files first for better caching
COPY pyproject.toml uv.lock .python-version ./
COPY shared/pyproject.toml shared/pyproject.toml
COPY cli/pyproject.toml cli/pyproject.toml

# Copy shared source code
COPY shared/src shared/src

# Copy CLI source code
COPY cli/src cli/src

# Install dependencies for the CLI package
RUN uv sync --frozen --no-dev --package chotot-miner-cli

# Runner stage - Minimal runtime image
FROM python:${PYTHON_VERSION}-slim AS runner

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/cli /app/cli
COPY --from=builder /app/shared /app/shared

# Set entrypoint to the CLI tool
ENTRYPOINT ["chotot-miner"]
