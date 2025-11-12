#!/usr/bin/env bash
set -euo pipefail
source .venv/Scripts/activate
black --check .
mypy --explicit-package-bases src
