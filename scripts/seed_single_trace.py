"""Milestone M2: Verification of one canonical trace.

Hierarchy:
gateway (POST /order)
  └── order (create_order)
       ├── inventory (check_stock)
       └── payment (authorize_card)
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import get_database
from models.schemas import (
    create_span_dict,
    create_trace_dict,
    create_service_dict,
    create_operation_dict,
)


def seed_single_trace():
    db = get_database()
    trace_id = "T-CANONICAL-001"

    # Clean existing entry if re-running
    db.traces.delete_one({"trace_id": trace_id})

    # Register participating services
    services_to_seed = [
        ("gateway", "Platform", "production"),
        ("order", "Order Management", "production"),
        ("inventory", "Warehouse & Stock", "production"),
        ("payment", "Billing & Payments", "production"),
    ]
    for s_name, team, env in services_to_seed:
        db.services.update_one(
            {"service_name": s_name},
            {"$set": create_service_dict(s_name, team, env, True)},
            upsert=True,
        )

    # Register participating operations
    ops_to_seed = [
        ("gateway", "POST /order", "http"),
        ("order", "create_order", "rpc"),
        ("inventory", "check_stock", "rpc"),
        ("payment", "authorize_card", "rpc"),
    ]
    for s_name, op_name, op_type in ops_to_seed:
        db.operations.update_one(
            {"service_name": s_name, "operation_name": op_name},
            {"$set": create_operation_dict(s_name, op_name, op_type, True)},
            upsert=True,
        )

    # Build canonical spans
    span1 = create_span_dict(
        span_id="S001",
        service="gateway",
        operation="POST /order",
        start_offset_ms=0,
        duration_ms=185,
        parent_span_id=None,
        status="OK",
        tags={"http.method": "POST", "http.status_code": 200, "client.ip": "192.168.1.10"},
    )
    span2 = create_span_dict(
        span_id="S002",
        service="order",
        operation="create_order",
        start_offset_ms=10,
        duration_ms=165,
        parent_span_id="S001",
        status="OK",
        tags={"order.id": "ord-9921", "customer.tier": "gold"},
    )
    span3 = create_span_dict(
        span_id="S003",
        service="inventory",
        operation="check_stock",
        start_offset_ms=25,
        duration_ms=45,
        parent_span_id="S002",
        status="OK",
        tags={"item.sku": "SKU-4401", "stock.available": 12},
    )
    span4 = create_span_dict(
        span_id="S004",
        service="payment",
        operation="authorize_card",
        start_offset_ms=75,
        duration_ms=95,
        parent_span_id="S002",
        status="OK",
        tags={"payment.provider": "stripe", "amount.usd": 149.99},
    )

    trace = create_trace_dict(
        trace_id=trace_id,
        root_service="gateway",
        root_operation="POST /order",
        duration_ms=185,
        start_time=datetime.now(timezone.utc),
        status="OK",
        spans=[span1, span2, span3, span4],
    )

    # Insert trace
    insert_res = db.traces.insert_one(trace)
    print(f"[+] Inserted trace {trace_id} with _id: {insert_res.inserted_id}")

    # Query back
    retrieved = db.traces.find_one({"trace_id": trace_id})
    assert retrieved is not None, "Trace retrieval failed!"
    assert retrieved["trace_id"] == trace_id
    assert len(retrieved["spans"]) == 4

    print("[+] Retrieved trace successfully from MongoDB:")
    print(f"    Trace ID: {retrieved['trace_id']}")
    print(f"    Root Service: {retrieved['root_service']}")
    print(f"    Root Operation: {retrieved['root_operation']}")
    print(f"    Duration: {retrieved['duration_ms']} ms")
    print(f"    Status: {retrieved['status']}")
    print(f"    Spans count: {len(retrieved['spans'])}")

    print("\n[+] Span hierarchy breakdown:")
    for s in retrieved["spans"]:
        parent = s["parent_span_id"] or "ROOT"
        print(f"    [{s['span_id']}] {s['service']}:{s['operation']} (offset: {s['start_offset_ms']}ms, duration: {s['duration_ms']}ms, parent: {parent})")

    return retrieved


if __name__ == "__main__":
    seed_single_trace()
