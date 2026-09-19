import sys
from pathlib import Path

FRAUD_AGENT_DIR = Path(__file__).resolve().parent.parent / "fraud-agent"
if str(FRAUD_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(FRAUD_AGENT_DIR))
