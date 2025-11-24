#!/usr/bin/env bash
set -euo pipefail
uv run pytest -q --cov --cov-report=term-missing
