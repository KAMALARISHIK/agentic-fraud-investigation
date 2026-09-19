import sys
import os
import importlib.util
from pathlib import Path

FRAUD_AGENT_DIR = Path(__file__).resolve().parent.parent / "fraud-agent"
if str(FRAUD_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(FRAUD_AGENT_DIR))

os.chdir(str(FRAUD_AGENT_DIR))

# Load the actual app from fraud-agent/app/main.py
spec = importlib.util.spec_from_file_location("fraud_agent_app_main", str(FRAUD_AGENT_DIR / "app" / "main.py"))
module = importlib.util.module_from_spec(spec)
sys.modules["fraud_agent_app_main"] = module
spec.loader.exec_module(module)

app = module.app
