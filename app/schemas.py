import sys
from pathlib import Path

FRAUD_AGENT_DIR = Path(__file__).resolve().parent.parent / "fraud-agent"
if str(FRAUD_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(FRAUD_AGENT_DIR))

import importlib.util
spec = importlib.util.spec_from_file_location("fraud_agent_schemas", str(FRAUD_AGENT_DIR / "app" / "schemas.py"))
module = importlib.util.module_from_spec(spec)
sys.modules["fraud_agent_schemas"] = module
spec.loader.exec_module(module)

# Re-export everything
for k, v in module.__dict__.items():
    if not k.startswith("_"):
        globals()[k] = v
