#!/usr/bin/env bash
set -euo pipefail
uv run black --check .
uv run mypy --explicit-package-bases src
