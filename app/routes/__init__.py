import sys
from pathlib import Path

FRAUD_AGENT_DIR = Path(__file__).resolve().parent.parent.parent / "fraud-agent"
if str(FRAUD_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(FRAUD_AGENT_DIR))

import importlib
for submod in ["cases", "timeline", "graph", "actions", "memory", "stats", "extra"]:
    spec = importlib.util.spec_from_file_location(f"fraud_agent_routes_{submod}", str(FRAUD_AGENT_DIR / "app" / "routes" / f"{submod}.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"fraud_agent_routes_{submod}"] = module
    spec.loader.exec_module(module)
    globals()[submod] = module
