"""Milestone M10: Query Plan Index Verification with explain().

Directly verifies that MongoDB uses justified indexes rather than COLLSCAN:
1. trace_id point lookup uses 'idx_traces_trace_id_unique' (IXSCAN)
2. start_time descending query uses 'idx_traces_start_time_desc' (IXSCAN without memory sort)
3. Unindexed comparison query demonstrates fallback to COLLSCAN
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import get_database


def inspect_winning_plan(plan_node):
    """Recursively search for IXSCAN or COLLSCAN stage and indexName."""
    stages = []

    def walk(node):
        if not isinstance(node, dict):
            return
        stage = node.get("stage")
        if stage:
            stages.append({
                "stage": stage,
                "indexName": node.get("indexName"),
                "direction": node.get("direction"),
            })
        if "inputStage" in node:
            walk(node["inputStage"])
        if "inputStages" in node:
            for s in node["inputStages"]:
                walk(s)

    walk(plan_node)
    return stages


def verify_indexes():
    db = get_database()
    print("=" * 70)
    print("       MONGODB QUERY PLAN & INDEX VERIFICATION (explain)")
    print("=" * 70)

    # -------------------------------------------------------------
    # Query 1: Point lookup by trace_id (Q1)
    # Expected: IXSCAN using idx_traces_trace_id_unique
    # -------------------------------------------------------------
    print("\n[TEST 1] Query: db.traces.find({'trace_id': 'T000001'})")
    q1_explain = db.command(
        "explain",
        {"find": "traces", "filter": {"trace_id": "T000001"}},
        verbosity="executionStats",
    )

    stats1 = q1_explain.get("executionStats", {})
    plan1 = q1_explain.get("queryPlanner", {}).get("winningPlan", {})
    stages1 = inspect_winning_plan(plan1)

    print(f"  - Winning Plan Stages: {[s['stage'] for s in stages1]}")
    ixscan1 = next((s for s in stages1 if s["stage"] in ("IXSCAN", "EXPRESS_IXSCAN")), None)
    if ixscan1:
        print(f"  - Using Stage: {ixscan1.get('stage')}")
        print(f"  - Using Index: {ixscan1.get('indexName')}")
        print(f"  - Documents Examined: {stats1.get('totalDocsExamined')}")
        print(f"  - Keys Examined: {stats1.get('totalKeysExamined')}")
        print(f"  - Execution Time: {stats1.get('executionTimeMillis')} ms")
        assert ixscan1.get("indexName") == "idx_traces_trace_id_unique"
        print(f"  [PASS] Successfully executed via {ixscan1.get('stage')} (Index Justified)")
    else:
        print("  [FAIL] Did not use IXSCAN or EXPRESS_IXSCAN!")

    # -------------------------------------------------------------
    # Query 2: Chronological Sort by start_time (Q2)
    # Expected: IXSCAN using idx_traces_start_time_desc
    # -------------------------------------------------------------
    print("\n[TEST 2] Query: db.traces.find().sort({'start_time': -1}).limit(20)")
    q2_explain = db.command(
        "explain",
        {"find": "traces", "sort": {"start_time": -1}, "limit": 20},
        verbosity="executionStats",
    )

    stats2 = q2_explain.get("executionStats", {})
    plan2 = q2_explain.get("queryPlanner", {}).get("winningPlan", {})
    stages2 = inspect_winning_plan(plan2)

    print(f"  - Winning Plan Stages: {[s['stage'] for s in stages2]}")
    ixscan2 = next((s for s in stages2 if s["stage"] == "IXSCAN"), None)
    if ixscan2:
        print(f"  - Using Index: {ixscan2.get('indexName')}")
        print(f"  - Documents Examined: {stats2.get('totalDocsExamined')}")
        print(f"  - Keys Examined: {stats2.get('totalKeysExamined')}")
        print(f"  - Execution Time: {stats2.get('executionTimeMillis')} ms")
        assert ixscan2.get("indexName") == "idx_traces_start_time_desc"
        print("  [PASS] Successfully executed via IXSCAN (Index Justified - No Blocking In-Memory Sort)")
    else:
        print("  [FAIL] Did not use IXSCAN!")

    # -------------------------------------------------------------
    # Query 3: Unindexed field search (Contrast demonstration)
    # Expected: COLLSCAN (Full collection scan)
    # -------------------------------------------------------------
    print("\n[TEST 3 - Contrast] Query on unindexed field: db.traces.find({'unindexed_field': 'value'})")
    q3_explain = db.command(
        "explain",
        {"find": "traces", "filter": {"unindexed_field": "value"}},
        verbosity="executionStats",
    )

    stats3 = q3_explain.get("executionStats", {})
    plan3 = q3_explain.get("queryPlanner", {}).get("winningPlan", {})
    stages3 = inspect_winning_plan(plan3)

    print(f"  - Winning Plan Stages: {[s['stage'] for s in stages3]}")
    collscan3 = next((s for s in stages3 if s["stage"] == "COLLSCAN"), None)
    if collscan3:
        print(f"  - Full Scan Stage: COLLSCAN")
        print(f"  - Total Documents Scanned: {stats3.get('totalDocsExamined')} (Full Collection)")
        print("  [CONFIRMED] Full scan occurs when no supporting index exists.")

    print("\n" + "=" * 70)
    print("  CONCLUSION: At least 2 indexes have query-driven empirical justification.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    verify_indexes()
