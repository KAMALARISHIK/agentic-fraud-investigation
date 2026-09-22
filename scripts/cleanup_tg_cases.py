import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fraud-agent"))

import config
from tg_client import get_tg_connection

def cleanup():
    # Connect
    conn = get_tg_connection()
    if not conn:
        print("ERROR: Could not connect to TigerGraph.")
        sys.exit(1)

    # 1. Fetch all current InvestigationCase vertices
    all_cases = conn.getVertices("InvestigationCase", limit=10000)
    all_case_ids = [c["v_id"] for c in all_cases if "v_id" in c]

    benchmark_ids = {f"CASE-HHG-{i:03d}" for i in range(1, 21)}
    
    extra_case_ids = [cid for cid in all_case_ids if cid not in benchmark_ids]
    valid_benchmark_ids = [cid for cid in all_case_ids if cid in benchmark_ids]

    print(f"Total InvestigationCase vertices found: {len(all_case_ids)}")
    print(f"Benchmark InvestigationCases to keep ({len(valid_benchmark_ids)}): {sorted(valid_benchmark_ids)}")
    print(f"Extra/Test InvestigationCases to remove ({len(extra_case_ids)}): {sorted(extra_case_ids)}")

    # Safety check: do not delete if any benchmark case is in the delete list
    for cid in extra_case_ids:
        if "HHG" in cid:
            raise ValueError(f"CRITICAL SAFETY CHECK FAILED: Benchmark case {cid} found in delete list!")

    # 2. Delete extra InvestigationCase vertices
    if extra_case_ids:
        print(f"\nDeleting {len(extra_case_ids)} extra InvestigationCase vertices...")
        del_count = conn.delVerticesById("InvestigationCase", extra_case_ids)
        print(f"Deleted {del_count} InvestigationCase vertices.")

    # 3. Clean up associated test Finding and ActionRecord vertices (CC prefix)
    all_findings = conn.getVertices("Finding", limit=10000)
    cc_findings = [f["v_id"] for f in all_findings if "v_id" in f and "CC-" in f["v_id"]]
    if cc_findings:
        print(f"Deleting {len(cc_findings)} test Finding vertices for CC cases...")
        conn.delVerticesById("Finding", cc_findings)

    all_actions = conn.getVertices("ActionRecord", limit=10000)
    cc_actions = [a["v_id"] for a in all_actions if "v_id" in a and "CC-" in a["v_id"]]
    if cc_actions:
        print(f"Deleting {len(cc_actions)} test ActionRecord vertices for CC cases...")
        conn.delVerticesById("ActionRecord", cc_actions)

    # 4. Verify post-cleanup state
    remaining_cases = conn.getVertices("InvestigationCase", limit=10000)
    remaining_ids = sorted([c["v_id"] for c in remaining_cases if "v_id" in c])
    closed_cases_count = conn.getVertexCount("ClosedCase")

    print("\n=== Post-Cleanup Verification ===")
    print(f"Remaining InvestigationCase Count: {len(remaining_ids)}")
    print(f"Remaining InvestigationCase IDs: {remaining_ids}")
    print(f"ClosedCase Count (untouched): {closed_cases_count}")
    print(f"All 20 benchmark cases preserved: {set(remaining_ids) == benchmark_ids}")

if __name__ == "__main__":
    cleanup()
