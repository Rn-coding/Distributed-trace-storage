"""Document schemas and helper constructors for MongoDB entities.

Entities:
- TraceDocument: Embedded span representation of a distributed trace
- Span: Individual unit of execution in a trace
- ServiceDocument: Microservice metadata
- OperationDocument: Endpoint / operation metadata
- DependencyDocument: Derived service-to-service relationship
- UserDocument: User credentials and role
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def create_span_dict(
    span_id: str,
    service: str,
    operation: str,
    duration_ms: float,
    start_offset_ms: float = 0.0,
    parent_span_id: Optional[str] = None,
    status: str = "OK",
    tags: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a validated dictionary for an embedded span."""
    return {
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "service": service,
        "operation": operation,
        "start_offset_ms": float(start_offset_ms),
        "duration_ms": float(duration_ms),
        "status": status,
        "tags": tags or {},
    }


def create_trace_dict(
    trace_id: str,
    root_service: str,
    root_operation: str,
    duration_ms: float,
    spans: List[Dict[str, Any]],
    start_time: Optional[datetime] = None,
    status: str = "OK",
) -> Dict[str, Any]:
    """Build a validated dictionary for a distributed trace document."""
    return {
        "trace_id": trace_id,
        "start_time": start_time or datetime.now(timezone.utc),
        "duration_ms": float(duration_ms),
        "status": status,
        "root_service": root_service,
        "root_operation": root_operation,
        "spans": spans,
    }


def create_service_dict(
    service_name: str,
    team: str = "Engineering",
    environment: str = "production",
    active: bool = True,
) -> Dict[str, Any]:
    """Build a service catalog metadata dictionary."""
    return {
        "service_name": service_name,
        "team": team,
        "environment": environment,
        "active": active,
    }


def create_operation_dict(
    service_name: str,
    operation_name: str,
    operation_type: str = "http",
    active: bool = True,
) -> Dict[str, Any]:
    """Build an operation catalog metadata dictionary."""
    return {
        "service_name": service_name,
        "operation_name": operation_name,
        "operation_type": operation_type,
        "active": active,
    }
