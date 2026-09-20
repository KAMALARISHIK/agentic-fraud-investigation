import sys
import logging
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
from tg_client import TigerGraphManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_agent.install_queries")

def install_all_queries():
    manager = TigerGraphManager()
    if not manager.is_connected():
        logger.error("TigerGraph is not connected. Cannot install queries.")
        return False

    queries_dir = BASE_DIR / "gsql" / "queries"
    query_files = list(queries_dir.glob("*.gsql"))
    if not query_files:
        logger.warning("No GSQL query files found to install.")
        return False

    graph_name = config.TG_GRAPHNAME or "FraudGraph"
    logger.info(f"Found {len(query_files)} query files to install onto {graph_name}...")
    
    # 1. Add all queries to TigerGraph schema
    for q_file in query_files:
        q_name = q_file.stem
        logger.info(f"Adding query '{q_name}'...")
        with open(q_file, "r", encoding="utf-8") as f:
            gsql_text = f.read()
        adapted_text = gsql_text.replace("FraudGraph", graph_name)
        try:
            res = manager.run_gsql(adapted_text)
            logger.info(f"Added {q_name}: {res}")
        except Exception as e:
            logger.error(f"Failed to add query {q_name}: {e}")

    # 2. Install all queries
    logger.info(f"Compiling and installing all queries on TigerGraph (INSTALL QUERY ALL for {graph_name})...")
    try:
        install_cmd = f"USE GRAPH {graph_name}\nINSTALL QUERY ALL"
        res = manager.run_gsql(install_cmd)
        logger.info(f"Installation output: {res}")
        return True
    except Exception as e:
        logger.error(f"Failed to install queries: {e}")
        return False

if __name__ == "__main__":
    success = install_all_queries()
    sys.exit(0 if success else 1)
