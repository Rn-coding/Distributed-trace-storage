"""End-to-end integration test demonstrating the full Phase 2 lifecycle."""

from app import create_app
from config import Config
from db.connection import get_database
from init_db import init_database
from generator.generate_traces import generate_dataset
from analytics.dependencies import rebuild_service_dependencies, get_service_dependencies
from analytics.performance import (
    average_latency_by_service,
    error_rate_by_service,
    slowest_operations,
    service_dependency_frequency,
    trace_latency_distribution,
)
from repositories.traces import create_trace, get_trace, update_trace_status, delete_trace, search_traces
from models.schemas import create_span_dict, create_trace_dict


def test_full_phase_2_integration_lifecycle():
    # 1. Initialize Clean Database
    init_database(drop_existing=True)
    db = get_database()

    # Verify all 5 collections exist
    colls = set(db.list_collection_names())
    for req_col in ["traces", "services", "operations", "service_dependencies", "users"]:
        assert req_col in colls

    # 2. Deterministic Synthetic Generation (120 traces)
    total_generated = generate_dataset(total_traces=120, seed=42, drop_existing=False)
    assert total_generated == 120
    assert db.traces.count_documents({}) >= 100
    assert db.services.count_documents({}) >= 5
    assert db.operations.count_documents({}) >= 10

    # 3. Materialize Service Dependencies
    dep_count = rebuild_service_dependencies()
    assert dep_count > 0
    assert db.service_dependencies.count_documents({}) == dep_count

    # 4. CRUD Demonstration on Trace
    crud_trace_id = "T-INTEG-9999"
    spans = [
        create_span_dict("S99-01", "api-gateway", "GET /integ", 60, 0, None, "OK"),
        create_span_dict("S99-02", "order-service", "exec_integ", 40, 10, "S99-01", "OK"),
    ]
    t_doc = create_trace_dict(
        trace_id=crud_trace_id,
        root_service="api-gateway",
        root_operation="GET /integ",
        duration_ms=60,
        spans=spans,
        status="OK",
    )

    # Create
    created_id = create_trace(t_doc)
    assert created_id == crud_trace_id

    # Read
    read_trace = get_trace(crud_trace_id)
    assert read_trace is not None
    assert read_trace["trace_id"] == crud_trace_id

    # Update
    assert update_trace_status(crud_trace_id, "ERROR") is True
    assert get_trace(crud_trace_id)["status"] == "ERROR"

    # Delete
    assert delete_trace(crud_trace_id) is True
    assert get_trace(crud_trace_id) is None

    # 5. Indexed Trace Retrieval
    t1 = get_trace("T000001")
    assert t1 is not None
    assert t1["trace_id"] == "T000001"

    # 6. Execute All 5 MongoDB Aggregation Pipelines
    a1 = average_latency_by_service()
    assert len(a1) >= 5
    a2 = error_rate_by_service()
    assert len(a2) >= 5
    a3 = slowest_operations(10)
    assert len(a3) >= 5
    a4 = service_dependency_frequency()
    assert len(a4) >= 4
    a5 = trace_latency_distribution()
    assert len(a5) >= 3

    # 7. Web Application Client Simulation
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # Unauthenticated redirect
    r = client.get("/dashboard")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]

    # Login
    login_res = client.post(
        "/login",
        data={"username": Config.ADMIN_USERNAME, "password": Config.ADMIN_PASSWORD},
        follow_redirects=True,
    )
    assert login_res.status_code == 200
    assert b"Operational Overview" in login_res.data

    # Dashboard view
    dash_res = client.get("/dashboard")
    assert dash_res.status_code == 200
    assert b"Total Ingested Traces" in dash_res.data

    # Traces view
    traces_res = client.get("/traces")
    assert traces_res.status_code == 200
    assert b"T000001" in traces_res.data

    # Trace detail view
    detail_res = client.get("/traces/T000001")
    assert detail_res.status_code == 200
    assert b"Span Hierarchy" in detail_res.data

    # Analytics view
    analytics_res = client.get("/analytics")
    assert analytics_res.status_code == 200
    assert b"1. Average Latency by Service" in analytics_res.data

    # Dependencies view & Rebuild action
    dep_res = client.get("/dependencies")
    assert dep_res.status_code == 200
    rebuild_res = client.post("/dependencies/rebuild", follow_redirects=True)
    assert rebuild_res.status_code == 200
    assert b"Materialized" in rebuild_res.data
