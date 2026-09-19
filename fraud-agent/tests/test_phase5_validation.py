import pytest
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.validate_answers import validate_all_answers

def test_phase5_answers_validation():
    """Verify all 20 HHG answer files exist, are strictly formatted, and compliant with policy."""
    assert validate_all_answers() is True
