"""Test suite verifying Milestone M7 Dependency Materialization."""

from datetime import datetime, timezone
from analytics.dependencies import rebuild_service_dependencies, get_service_dependencies
from repositories.traces import create_trace, delete_trace
from models.schemas import create_span_dict, create_trace_dict


def test_rebuild_service_dependencies():
    count = rebuild_service_dependencies()
    assert count > 0

    deps = get_service_dependencies()
    assert len(deps) == count

    edges = {(d["source_service"], d["target_service"]) for d in deps}
    # Expected edges from generated traces
    assert ("api-gateway", "order-service") in edges
    assert ("order-service", "payment-service") in edges
    assert ("order-service", "inventory-service") in edges

    for d in deps:
        assert d["observation_count"] > 0
        assert d["avg_latency_ms"] >= 0
        assert "last_seen" in d


def test_trace_mutation_dependency_rebuild():
    """Verify that adding and deleting trace data reflects accurately upon rebuild."""
    test_trace_id = "T-DEP-MUTATION-001"
    delete_trace(test_trace_id)

    # Insert a unique synthetic dependency edge: alpha-service -> beta-service
    spans = [
        create_span_dict("S-DEP-1", "alpha-service", "call", 100, 0, None, "OK"),
        create_span_dict("S-DEP-2", "beta-service", "exec", 80, 10, "S-DEP-1", "ERROR"),
    ]
    trace = create_trace_dict(
        trace_id=test_trace_id,
        root_service="alpha-service",
        root_operation="call",
        duration_ms=100,
        spans=spans,
        start_time=datetime.now(timezone.utc),
        status="ERROR",
    )
    create_trace(trace)

    # Rebuild and assert new edge exists
    rebuild_service_dependencies()
    deps = get_service_dependencies()
    alpha_beta = [d for d in deps if d["source_service"] == "alpha-service" and d["target_service"] == "beta-service"]
    assert len(alpha_beta) == 1
    assert alpha_beta[0]["error_count"] >= 1

    # Delete trace and rebuild; assert edge is removed
    delete_trace(test_trace_id)
    rebuild_service_dependencies()
    deps_after = get_service_dependencies()
    alpha_beta_after = [d for d in deps_after if d["source_service"] == "alpha-service" and d["target_service"] == "beta-service"]
    assert len(alpha_beta_after) == 0
