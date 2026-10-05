"""Synthetic Trace Generator for Phase 2.

Generates realistic, varied, deterministic distributed trace data:
- 7 services
- 16 operations
- Scenarios: Normal, Slow Payment, Slow Inventory, Payment Failure,
  Inventory Out of Stock, Auth Failure, Product Fan-out, Deep Fulfillment
- Uses deterministic seed (default 42) for reproducible analytics.
"""

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import get_database
from models.schemas import (
    create_span_dict,
    create_trace_dict,
    create_service_dict,
    create_operation_dict,
)

SERVICES = [
    {"service_name": "api-gateway", "team": "Platform", "environment": "production"},
    {"service_name": "auth-service", "team": "Identity", "environment": "production"},
    {"service_name": "order-service", "team": "Core Commerce", "environment": "production"},
    {"service_name": "payment-service", "team": "Payments", "environment": "production"},
    {"service_name": "inventory-service", "team": "Logistics", "environment": "production"},
    {"service_name": "notification-service", "team": "Comms", "environment": "production"},
    {"service_name": "shipping-service", "team": "Logistics", "environment": "production"},
]

OPERATIONS = [
    ("api-gateway", "POST /orders", "http"),
    ("api-gateway", "GET /products", "http"),
    ("api-gateway", "POST /auth/login", "http"),
    ("auth-service", "verify_token", "rpc"),
    ("auth-service", "authenticate", "rpc"),
    ("order-service", "create_order", "rpc"),
    ("order-service", "get_order_status", "rpc"),
    ("order-service", "cancel_order", "rpc"),
    ("payment-service", "process_payment", "rpc"),
    ("payment-service", "refund_payment", "rpc"),
    ("inventory-service", "check_inventory", "rpc"),
    ("inventory-service", "reserve_stock", "rpc"),
    ("inventory-service", "release_stock", "rpc"),
    ("shipping-service", "calculate_rate", "rpc"),
    ("shipping-service", "schedule_pickup", "rpc"),
    ("notification-service", "send_email", "queue"),
    ("notification-service", "send_sms", "queue"),
]


def seed_services_and_operations(db):
    """Seed services and operations collections."""
    for svc in SERVICES:
        db.services.update_one(
            {"service_name": svc["service_name"]},
            {"$set": create_service_dict(svc["service_name"], svc["team"], svc["environment"], True)},
            upsert=True,
        )

    for svc_name, op_name, op_type in OPERATIONS:
        db.operations.update_one(
            {"service_name": svc_name, "operation_name": op_name},
            {"$set": create_operation_dict(svc_name, op_name, op_type, True)},
            upsert=True,
        )


def generate_trace_scenario(
    trace_idx: int,
    base_time: datetime,
    scenario_type: str,
    rng: random.Random,
) -> Dict[str, Any]:
    trace_id = f"T{trace_idx:06d}"
    spans: List[Dict[str, Any]] = []

    def make_span_id(idx: int) -> str:
        return f"S{trace_idx:04d}-{idx:02d}"

    offset = 0.0

    if scenario_type == "NORMAL_ORDER":
        # Root gateway
        s1_dur = rng.uniform(15, 30)
        s1 = create_span_dict(make_span_id(1), "api-gateway", "POST /orders", s1_dur, offset, None, "OK", {"http.status": 201})
        spans.append(s1)

        # Auth verify
        s2_dur = rng.uniform(8, 20)
        spans.append(create_span_dict(make_span_id(2), "auth-service", "verify_token", s2_dur, offset + 5, s1["span_id"], "OK"))

        # Order creation
        s3_dur = rng.uniform(90, 150)
        s3 = create_span_dict(make_span_id(3), "order-service", "create_order", s3_dur, offset + 25, s1["span_id"], "OK")
        spans.append(s3)

        # Inventory check & reserve
        s4_dur = rng.uniform(20, 45)
        spans.append(create_span_dict(make_span_id(4), "inventory-service", "check_inventory", s4_dur, offset + 35, s3["span_id"], "OK"))
        s5_dur = rng.uniform(25, 50)
        spans.append(create_span_dict(make_span_id(5), "inventory-service", "reserve_stock", s5_dur, offset + 65, s3["span_id"], "OK"))

        # Payment
        s6_dur = rng.uniform(40, 85)
        spans.append(create_span_dict(make_span_id(6), "payment-service", "process_payment", s6_dur, offset + 105, s3["span_id"], "OK"))

        # Notification
        s7_dur = rng.uniform(15, 35)
        spans.append(create_span_dict(make_span_id(7), "notification-service", "send_email", s7_dur, offset + 145, s3["span_id"], "OK"))

        total_dur = round(offset + 185 + rng.uniform(5, 30), 2)
        return create_trace_dict(trace_id, "api-gateway", "POST /orders", total_dur, spans, base_time, "OK")

    elif scenario_type == "SLOW_PAYMENT":
        s1 = create_span_dict(make_span_id(1), "api-gateway", "POST /orders", 25, offset, None, "OK")
        spans.append(s1)
        spans.append(create_span_dict(make_span_id(2), "auth-service", "verify_token", 15, offset + 5, s1["span_id"], "OK"))
        s3 = create_span_dict(make_span_id(3), "order-service", "create_order", 750, offset + 25, s1["span_id"], "OK")
        spans.append(s3)
        spans.append(create_span_dict(make_span_id(4), "inventory-service", "check_inventory", 30, offset + 35, s3["span_id"], "OK"))
        spans.append(create_span_dict(make_span_id(5), "inventory-service", "reserve_stock", 35, offset + 65, s3["span_id"], "OK"))

        # Slow payment bottleneck: 450 - 950 ms
        slow_pay_dur = round(rng.uniform(450, 950), 2)
        spans.append(create_span_dict(make_span_id(6), "payment-service", "process_payment", slow_pay_dur, offset + 110, s3["span_id"], "OK", {"warning": "slow_gateway_response"}))
        spans.append(create_span_dict(make_span_id(7), "notification-service", "send_email", 20, offset + 115 + slow_pay_dur, s3["span_id"], "OK"))

        total_dur = round(offset + 140 + slow_pay_dur, 2)
        return create_trace_dict(trace_id, "api-gateway", "POST /orders", total_dur, spans, base_time, "OK")

    elif scenario_type == "SLOW_INVENTORY":
        s1 = create_span_dict(make_span_id(1), "api-gateway", "POST /orders", 25, offset, None, "OK")
        spans.append(s1)
        spans.append(create_span_dict(make_span_id(2), "auth-service", "verify_token", 12, offset + 5, s1["span_id"], "OK"))
        s3 = create_span_dict(make_span_id(3), "order-service", "create_order", 620, offset + 20, s1["span_id"], "OK")
        spans.append(s3)

        # Slow inventory database lock: 350 - 750 ms
        slow_inv_dur = round(rng.uniform(350, 750), 2)
        spans.append(create_span_dict(make_span_id(4), "inventory-service", "check_inventory", slow_inv_dur, offset + 30, s3["span_id"], "OK", {"db.lock_wait_ms": 320}))
        spans.append(create_span_dict(make_span_id(5), "inventory-service", "reserve_stock", 40, offset + 40 + slow_inv_dur, s3["span_id"], "OK"))
        spans.append(create_span_dict(make_span_id(6), "payment-service", "process_payment", 50, offset + 85 + slow_inv_dur, s3["span_id"], "OK"))
        spans.append(create_span_dict(make_span_id(7), "notification-service", "send_email", 20, offset + 140 + slow_inv_dur, s3["span_id"], "OK"))

        total_dur = round(offset + 170 + slow_inv_dur, 2)
        return create_trace_dict(trace_id, "api-gateway", "POST /orders", total_dur, spans, base_time, "OK")

    elif scenario_type == "PAYMENT_FAILURE":
        s1 = create_span_dict(make_span_id(1), "api-gateway", "POST /orders", 180, offset, None, "ERROR", {"http.status": 500})
        spans.append(s1)
        spans.append(create_span_dict(make_span_id(2), "auth-service", "verify_token", 15, offset + 5, s1["span_id"], "OK"))
        s3 = create_span_dict(make_span_id(3), "order-service", "create_order", 150, offset + 25, s1["span_id"], "ERROR")
        spans.append(s3)
        spans.append(create_span_dict(make_span_id(4), "inventory-service", "reserve_stock", 45, offset + 35, s3["span_id"], "OK"))

        # Payment error
        pay_err_dur = rng.uniform(40, 80)
        spans.append(create_span_dict(make_span_id(5), "payment-service", "process_payment", pay_err_dur, offset + 85, s3["span_id"], "ERROR", {"error.code": "CARD_DECLINED", "error.message": "Insufficient funds"}))

        # Rollback stock
        spans.append(create_span_dict(make_span_id(6), "inventory-service", "release_stock", 30, offset + 90 + pay_err_dur, s3["span_id"], "OK"))

        total_dur = round(offset + 130 + pay_err_dur, 2)
        return create_trace_dict(trace_id, "api-gateway", "POST /orders", total_dur, spans, base_time, "ERROR")

    elif scenario_type == "AUTH_FAILURE":
        s1 = create_span_dict(make_span_id(1), "api-gateway", "POST /orders", 30, offset, None, "ERROR", {"http.status": 401})
        spans.append(s1)
        spans.append(create_span_dict(make_span_id(2), "auth-service", "verify_token", 25, offset + 5, s1["span_id"], "ERROR", {"error": "Invalid or expired token"}))

        total_dur = round(offset + 32, 2)
        return create_trace_dict(trace_id, "api-gateway", "POST /orders", total_dur, spans, base_time, "ERROR")

    elif scenario_type == "BROWSE_PRODUCTS":
        # Fan-out
        s1 = create_span_dict(make_span_id(1), "api-gateway", "GET /products", 70, offset, None, "OK", {"http.status": 200})
        spans.append(s1)
        # Parallel calls to inventory and shipping
        spans.append(create_span_dict(make_span_id(2), "inventory-service", "check_inventory", rng.uniform(30, 55), offset + 10, s1["span_id"], "OK"))
        spans.append(create_span_dict(make_span_id(3), "shipping-service", "calculate_rate", rng.uniform(25, 45), offset + 12, s1["span_id"], "OK"))

        total_dur = round(offset + rng.uniform(65, 95), 2)
        return create_trace_dict(trace_id, "api-gateway", "GET /products", total_dur, spans, base_time, "OK")

    else:  # DEEP_FULFILLMENT
        s1 = create_span_dict(make_span_id(1), "api-gateway", "POST /orders", 260, offset, None, "OK")
        spans.append(s1)
        spans.append(create_span_dict(make_span_id(2), "auth-service", "verify_token", 15, offset + 5, s1["span_id"], "OK"))
        s3 = create_span_dict(make_span_id(3), "order-service", "create_order", 220, offset + 25, s1["span_id"], "OK")
        spans.append(s3)
        s4 = create_span_dict(make_span_id(4), "inventory-service", "reserve_stock", 60, offset + 35, s3["span_id"], "OK")
        spans.append(s4)
        spans.append(create_span_dict(make_span_id(5), "payment-service", "process_payment", 65, offset + 100, s3["span_id"], "OK"))

        # Deep chained call: order -> shipping -> notification
        s6 = create_span_dict(make_span_id(6), "shipping-service", "schedule_pickup", 50, offset + 170, s3["span_id"], "OK")
        spans.append(s6)
        spans.append(create_span_dict(make_span_id(7), "notification-service", "send_sms", 25, offset + 190, s6["span_id"], "OK"))

        total_dur = round(offset + 250 + rng.uniform(10, 40), 2)
        return create_trace_dict(trace_id, "api-gateway", "POST /orders", total_dur, spans, base_time, "OK")


def generate_dataset(total_traces: int = 120, seed: int = 42, drop_existing: bool = False):
    """Generate deterministically varied trace documents and seed MongoDB."""
    rng = random.Random(seed)
    db = get_database()

    if drop_existing:
        print("[!] Dropping existing traces for fresh generation...")
        db.traces.delete_many({})

    # Seed metadata
    seed_services_and_operations(db)
    print(f"[+] Seeded {len(SERVICES)} services and {len(OPERATIONS)} operations metadata.")

    # Scenarios distribution weights
    scenarios = [
        ("NORMAL_ORDER", 0.45),
        ("SLOW_PAYMENT", 0.15),
        ("SLOW_INVENTORY", 0.10),
        ("PAYMENT_FAILURE", 0.10),
        ("AUTH_FAILURE", 0.05),
        ("BROWSE_PRODUCTS", 0.10),
        ("DEEP_FULFILLMENT", 0.05),
    ]

    population = [s[0] for s in scenarios]
    weights = [s[1] for s in scenarios]

    now = datetime.now(timezone.utc)
    traces: List[Dict[str, Any]] = []

    print(f"[*] Generating {total_traces} realistic traces with seed={seed}...")
    for i in range(1, total_traces + 1):
        chosen_scenario = rng.choices(population, weights=weights, k=1)[0]
        # Spread start times over past 24 hours
        time_offset_sec = rng.randint(0, 86400)
        trace_time = now - timedelta(seconds=time_offset_sec)

        trace_doc = generate_trace_scenario(i, trace_time, chosen_scenario, rng)
        traces.append(trace_doc)

    # Insert in batch
    db.traces.insert_many(traces)
    print(f"[SUCCESS] Inserted {len(traces)} trace documents into MongoDB.")

    # Print summary statistics directly from MongoDB queries
    total_in_db = db.traces.count_documents({})
    errors_in_db = db.traces.count_documents({"status": "ERROR"})
    print(f"    Total traces in DB: {total_in_db}")
    print(f"    Error traces in DB: {errors_in_db} ({round(errors_in_db / total_in_db * 100, 1)}%)")
    print(f"    Services count: {db.services.count_documents({})}")
    print(f"    Operations count: {db.operations.count_documents({})}")

    return total_in_db


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Synthetic Trace Generator")
    parser.add_argument("--count", type=int, default=120, help="Number of traces to generate (min 100)")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--drop-existing", action="store_true", help="Clear traces before generation")
    args = parser.parse_args()

    generate_dataset(total_traces=args.count, seed=args.seed, drop_existing=args.drop_existing)
