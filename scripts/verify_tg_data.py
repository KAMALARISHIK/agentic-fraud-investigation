import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fraud-agent"))

import config
from tg_client import get_tg_connection

def verify():
    # Mute background loggers so output is clean and contains ONLY requested data
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)
    logging.getLogger("fraud_agent.tg_client").setLevel(logging.CRITICAL)
    logging.getLogger("pyTigerGraph").setLevel(logging.CRITICAL)

    conn = get_tg_connection()
    if not conn:
        print("ERROR: Could not connect to TigerGraph.")
        sys.exit(1)

    vertex_types = [
        "InvestigationCase",
        "ActionRecord",
        "Transaction",
        "Card",
        "DeviceProfile",
        "ClosedCase",
        "PolicyChunk"
    ]

    # 1. Count of each vertex type in FraudGraph
    print("=== 1. Vertex Counts in FraudGraph ===")
    for v_type in vertex_types:
        try:
            cnt = conn.getVertexCount(v_type)
            print(f"{v_type}: {cnt}")
        except Exception:
            try:
                verts = conn.getVertices(v_type, limit=100000)
                print(f"{v_type}: {len(verts)}")
            except Exception as e:
                print(f"{v_type}: Error ({e})")

    # 2. List of InvestigationCase IDs
    print("\n=== 2. InvestigationCase IDs ===")
    try:
        cases = conn.getVertices("InvestigationCase", limit=1000)
        case_ids = sorted([c.get("v_id") for c in cases if "v_id" in c])
        print(f"Total InvestigationCases: {len(case_ids)}")
        print(f"IDs: {case_ids}")
    except Exception as e:
        case_ids = []
        print(f"Error fetching InvestigationCases: {e}")

    # 3. Benchmark cases check (HHG-001 to HHG-020) and duplicate check
    print("\n=== 3. Benchmark Cases Check (HHG-001 to HHG-020) ===")
    benchmark_nums = [f"HHG-{i:03d}" for i in range(1, 21)]
    
    # Check if each benchmark case exists either as HHG-XXX or CASE-HHG-XXX
    found_benchmark = []
    missing_benchmark = []
    for b in benchmark_nums:
        if b in case_ids or f"CASE-{b}" in case_ids:
            found_benchmark.append(b)
        else:
            missing_benchmark.append(b)

    all_20_exist = (len(missing_benchmark) == 0)
    print(f"All 20 benchmark cases exist: {all_20_exist}")
    if missing_benchmark:
        print(f"Missing benchmark cases: {missing_benchmark}")
    else:
        print(f"Found all 20 benchmark cases: {found_benchmark}")

    # Check for duplicate IDs
    duplicates = [cid for cid in set(case_ids) if case_ids.count(cid) > 1]
    has_duplicates = (len(duplicates) > 0)
    print(f"Any duplicate case IDs in graph: {has_duplicates}")
    if has_duplicates:
        print(f"Duplicate IDs found: {duplicates}")

if __name__ == "__main__":
    verify()
