import sys
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.extra_monitor import autonomous_monitor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_agent.run_monitor")

def main():
    logger.info("================================================================")
    logger.info("   LAUNCHING INNOVATION EXTRA: AUTONOMOUS FRAUD RING MONITOR    ")
    logger.info("================================================================")
    cases = autonomous_monitor.scan_unflagged_rings(risk_threshold=0.80, max_cases=5)
    logger.info(f"Scan complete: {len(cases)} undocumented fraud rings identified and saved to cases_extra/")

if __name__ == "__main__":
    main()
