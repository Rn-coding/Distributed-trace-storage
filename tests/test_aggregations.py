"""Test suite verifying Milestone M6 MongoDB aggregation pipelines."""

from analytics.performance import (
    average_latency_by_service,
    error_rate_by_service,
    slowest_operations,
    service_dependency_frequency,
    trace_latency_distribution,
)


def test_average_latency_by_service():
    results = average_latency_by_service()
    assert isinstance(results, list)
    assert len(results) > 0

    first = results[0]
    assert "service" in first
    assert "avg_latency_ms" in first
    assert "span_count" in first
    assert first["avg_latency_ms"] >= 0
    assert first["span_count"] > 0

    # Ensure results are sorted descending by latency
    latencies = [r["avg_latency_ms"] for r in results]
    assert latencies == sorted(latencies, reverse=True)


def test_error_rate_by_service():
    results = error_rate_by_service()
    assert isinstance(results, list)
    assert len(results) > 0

    first = results[0]
    assert "service" in first
    assert "total_spans" in first
    assert "error_spans" in first
    assert "error_rate_pct" in first
    assert 0 <= first["error_rate_pct"] <= 100


def test_slowest_operations():
    results = slowest_operations(limit=5)
    assert isinstance(results, list)
    assert 0 < len(results) <= 5

    first = results[0]
    assert "service" in first
    assert "operation" in first
    assert "avg_duration_ms" in first
    assert "invocations" in first


def test_service_dependency_frequency():
    results = service_dependency_frequency()
    assert isinstance(results, list)
    assert len(results) > 0

    first = results[0]
    assert "source_service" in first
    assert "target_service" in first
    assert "frequency" in first
    assert "error_count" in first
    assert "avg_latency_ms" in first
    assert first["frequency"] >= 1
    assert first["source_service"] != first["target_service"]


def test_trace_latency_distribution():
    results = trace_latency_distribution()
    assert isinstance(results, list)
    assert len(results) > 0

    first = results[0]
    assert "range" in first
    assert "count" in first
    assert "avg_duration_ms" in first
    assert first["count"] > 0
