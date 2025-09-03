import sys
from pathlib import Path

# Ensure the ``src`` directory is on the Python path so ``import ainfo`` works
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
