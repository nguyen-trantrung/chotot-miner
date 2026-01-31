FROM --platform=arm64 mcr.microsoft.com/devcontainers/python:3.13

ENV RUFF_CACHE_DIR=$HOME/workspace/.cache/ruff
ENV MYPY_CACHE_DIR=$HOME/workspace/.cache/mypy
ENV PRE_COMMIT_HOME=$HOME/workspace/.cache/pre-commit

RUN pipx install --force uv==0.6.9
