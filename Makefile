.PHONY: help setup test build run install

# Get Python version from .python-version file
PYTHON_VERSION := $(shell cat .python-version 2>/dev/null || echo "3.13")

# Default target - show help
help:
	@echo "Available targets:"
	@echo "  setup (s)       - Install dependencies"
	@echo "  test (t)        - Run tests with pytest"
	@echo "  install (i)     - Install the CLI tool locally"
	@echo "  run             - Run the CLI tool (usage: make run ARGS='--url ... --count ...')"
	@echo "  build           - Build Docker image"
	@echo "  docker-run      - Run CLI tool in Docker"
	@echo ""
	@echo "Aliases:"
	@echo "  s = setup"
	@echo "  t = test"
	@echo "  i = install"

# Aliases
s: setup
t: test
i: install

# Setup development environment
setup:
	@echo "Installing dependencies with uv..."
	uv sync
	@echo "Setup complete!"

# Run tests
test:
	@echo "Running tests..."
	uv run pytest

# Install CLI tool locally
install:
	@echo "Installing CLI tool..."
	uv sync
	@echo "✓ CLI tool installed! Run 'uv run chotot-miner --help'"

# Run CLI tool
run:
	@echo "Running chotot-miner..."
	uv run chotot-miner $(ARGS)

# Build docker image
build:
	@echo "Building chotot-miner with Python $(PYTHON_VERSION)..."
	docker build -t chotot-miner \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		.

# Run CLI in Docker
docker-run:
	@echo "Running chotot-miner in Docker..."
	docker run --rm -v $(PWD)/output:/output chotot-miner $(ARGS)

# Example: Scrape to TSV
example-tsv:
	@echo "Example: Scraping to TSV..."
	uv run chotot-miner run \
		--url "https://www.chotot.com/mua-ban-dien-thoai" \
		--count 10 \
		--output tsv \
		--output-file output.tsv

# Example: Scrape to SQLite
example-sqlite:
	@echo "Example: Scraping to SQLite..."
	uv run chotot-miner run \
		--url "https://www.chotot.com/mua-ban-dien-thoai" \
		--count 10 \
		--output sqlite \
		--output-file output.db
