import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "fraud-agent"
sys.path.insert(0, str(BASE_DIR))
os.chdir(str(BASE_DIR))

from scripts.validate_answers import validate_all_answers

if __name__ == "__main__":
    is_valid = validate_all_answers()
    sys.exit(0 if is_valid else 1)
