import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
from tg_client import TigerGraphManager

def test_tigergraph_loaded_counts():
    """Verify TigerGraph contains all required vertices and embeddings."""
    manager = TigerGraphManager()
    assert manager.is_connected(), "TigerGraph is not connected"
    
    counts = manager.conn.getVertexCount("*")
    assert counts.get("Transaction", 0) > 10000, f"Expected >10k transactions, got {counts}"
    assert counts.get("ClosedCase", 0) >= 5000, f"Expected >=5k closed cases, got {counts}"
    assert counts.get("Customer", 0) >= 1000, f"Expected >=1k customers, got {counts}"
    assert counts.get("Card", 0) >= 1000, f"Expected >=1k cards, got {counts}"
    assert counts.get("PolicyChunk", 0) >= 10, f"Expected >=10 policy chunks, got {counts}"
    assert counts.get("DeviceProfile", 0) >= 500, f"Expected >=500 device profiles, got {counts}"

def test_embeddings_cache_exists():
    """Verify embeddings cache exists and has embeddings."""
    cache_path = config.EMBEDDINGS_CACHE_PATH
    assert cache_path.exists(), "embeddings_cache.json missing"
    import json
    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) >= 5000, f"Expected >=5000 cached vectors, got {len(data)}"
