from pathlib import Path
import sys

# Ensure the repo root is on sys.path so "backend" package can be imported
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
