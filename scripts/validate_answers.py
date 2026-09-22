import sys
import os
import importlib.util
from pathlib import Path

FRAUD_AGENT_DIR = Path(__file__).resolve().parent.parent / "fraud-agent"
if str(FRAUD_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(FRAUD_AGENT_DIR))

spec = importlib.util.spec_from_file_location("fraud_agent_validate_answers", str(FRAUD_AGENT_DIR / "scripts" / "validate_answers.py"))
module = importlib.util.module_from_spec(spec)
sys.modules["fraud_agent_validate_answers"] = module
spec.loader.exec_module(module)

validate_all_answers = module.validate_all_answers

if __name__ == "__main__":
    is_valid = validate_all_answers()
    sys.exit(0 if is_valid else 1)
