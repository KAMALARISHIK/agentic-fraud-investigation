import sys
import logging
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
from tg_client import TigerGraphManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_agent.create_schema")

def create_schema():
    schema_path = BASE_DIR / "gsql" / "schema.gsql"
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        return False

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_gsql = f.read()

    manager = TigerGraphManager()
    if not manager.is_connected():
        logger.warning("TigerGraph is not connected. Please ensure TG_HOST, TG_SECRET or TG_USERNAME/TG_PASSWORD in .env are set and the workspace is active.")
        return False

    logger.info("Applying FraudGraph schema to TigerGraph...")
    try:
        res = manager.run_gsql(schema_gsql)
        logger.info(f"Schema applied successfully: {res}")
        return True
    except Exception as e:
        logger.error(f"Error applying schema: {e}")
        return False

if __name__ == "__main__":
    success = create_schema()
    sys.exit(0 if success else 1)
