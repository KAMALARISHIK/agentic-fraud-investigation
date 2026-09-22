import sys
import os
import importlib.util
from pathlib import Path

FRAUD_AGENT_DIR = Path(__file__).resolve().parent.parent / "fraud-agent"
if str(FRAUD_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(FRAUD_AGENT_DIR))

spec = importlib.util.spec_from_file_location("fraud_agent_run_all_cases", str(FRAUD_AGENT_DIR / "scripts" / "run_all_cases.py"))
module = importlib.util.module_from_spec(spec)
sys.modules["fraud_agent_run_all_cases"] = module
spec.loader.exec_module(module)

run_all_cases = module.run_all_cases

if __name__ == "__main__":
    run_all_cases()

