#!/usr/bin/env bash
set -euo pipefail
source .venv/Scripts/activate
pytest -q --cov --cov-report=term-missing
