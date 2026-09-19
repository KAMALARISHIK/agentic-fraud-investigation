import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "fraud-agent"
sys.path.insert(0, str(BASE_DIR))
os.chdir(str(BASE_DIR))

from scripts.backtest import run_backtest

if __name__ == "__main__":
    run_backtest()
