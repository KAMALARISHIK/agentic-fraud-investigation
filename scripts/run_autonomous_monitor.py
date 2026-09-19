import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "fraud-agent"
sys.path.insert(0, str(BASE_DIR))
os.chdir(str(BASE_DIR))

from scripts.run_autonomous_monitor import main

if __name__ == "__main__":
    main()
