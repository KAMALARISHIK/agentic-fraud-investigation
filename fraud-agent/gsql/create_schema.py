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

    graph_name = config.TG_GRAPHNAME or "FraudGraph"
    logger.info(f"Checking if graph '{graph_name}' exists...")
    try:
        ls_res = manager.run_gsql("ls")
        if f"Graph {graph_name}" not in ls_res:
            logger.info(f"Graph '{graph_name}' not found. Creating graph '{graph_name}'...")
            create_graph_res = manager.run_gsql(f"CREATE GRAPH {graph_name}()")
            logger.info(f"Graph created: {create_graph_res}")
        else:
            logger.info(f"Graph '{graph_name}' already exists.")
    except Exception as e:
        logger.warning(f"Note during graph check/creation: {e}")

    logger.info(f"Applying schema to TigerGraph graph '{graph_name}' from {schema_path}...")
    try:
        adapted_gsql = schema_gsql.replace("FraudGraph", graph_name)
        res = manager.run_gsql(adapted_gsql)
        logger.info(f"Schema applied successfully: {res}")
        if "Error:" in res or "error" in res.lower():
            logger.error(f"GSQL error occurred: {res}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error applying schema: {e}")
        return False

if __name__ == "__main__":
    success = create_schema()
    sys.exit(0 if success else 1)
