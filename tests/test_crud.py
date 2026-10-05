"""Test suite verifying Milestone M3 CRUD operations."""

from datetime import datetime, timezone
import pytest
from db.connection import get_database
from models.schemas import create_span_dict, create_trace_dict
from repositories.traces import (
    create_trace,
    get_trace,
    search_traces,
    update_trace_status,
    delete_trace,
)
from repositories.services import (
    create_service,
    get_service,
    update_service,
    delete_service,
    list_services,
)
from repositories.operations import (
    create_operation,
    get_operation,
    update_operation,
    delete_operation,
    list_operations,
)
from repositories.users import (
    create_user,
    get_user_by_username,
    verify_user_credentials,
)


def test_trace_crud():
    trace_id = "T-TEST-CRUD-001"
    delete_trace(trace_id)

    spans = [
        create_span_dict("S01", "test-gateway", "GET /test", 50, 0, None, "OK"),
        create_span_dict("S02", "test-service", "process", 40, 10, "S01", "OK"),
    ]
    doc = create_trace_dict(
        trace_id=trace_id,
        root_service="test-gateway",
        root_operation="GET /test",
        duration_ms=50,
        spans=spans,
        start_time=datetime.now(timezone.utc),
        status="OK",
    )

    # 1. Create
    inserted_id = create_trace(doc)
    assert inserted_id == trace_id

    # 2. Read (get_trace)
    retrieved = get_trace(trace_id)
    assert retrieved is not None
    assert retrieved["trace_id"] == trace_id
    assert retrieved["duration_ms"] == 50
    assert len(retrieved["spans"]) == 2

    # 3. Read (search_traces)
    results, total = search_traces(service="test-service")
    assert total >= 1
    found_ids = [t["trace_id"] for t in results]
    assert trace_id in found_ids

    # 4. Update
    updated = update_trace_status(trace_id, "ERROR")
    assert updated is True
    retrieved_updated = get_trace(trace_id)
    assert retrieved_updated["status"] == "ERROR"

    # 5. Delete
    deleted = delete_trace(trace_id)
    assert deleted is True
    assert get_trace(trace_id) is None


def test_service_crud():
    svc_name = "test-crud-service"
    delete_service(svc_name)

    # 1. Create
    created = create_service(svc_name, team="QA", environment="staging", active=True)
    assert created == svc_name

    # 2. Read
    svc = get_service(svc_name)
    assert svc is not None
    assert svc["team"] == "QA"

    # 3. Update
    updated = update_service(svc_name, {"team": "Core Dev"})
    assert updated is True
    svc_after = get_service(svc_name)
    assert svc_after["team"] == "Core Dev"

    # 4. Delete
    deleted = delete_service(svc_name)
    assert deleted is True
    assert get_service(svc_name) is None


def test_operation_crud():
    svc = "test-crud-service-2"
    op = "compute_hash"
    delete_operation(svc, op)

    # 1. Create
    created = create_operation(svc, op, operation_type="internal", active=True)
    assert created["operation_name"] == op

    # 2. Read
    res = get_operation(svc, op)
    assert res is not None
    assert res["operation_type"] == "internal"

    # 3. Update
    updated = update_operation(svc, op, {"active": False})
    assert updated is True
    res_after = get_operation(svc, op)
    assert res_after["active"] is False

    # 4. Delete
    deleted = delete_operation(svc, op)
    assert deleted is True
    assert get_operation(svc, op) is None


def test_user_authentication_crud():
    username = "test-auth-user"
    db = get_database()
    db.users.delete_one({"username": username})

    # 1. Create with password hashing
    created = create_user(username, "secretPassword123!", role="viewer")
    assert created == username

    # 2. Verify with correct password
    verified = verify_user_credentials(username, "secretPassword123!")
    assert verified is not None
    assert verified["username"] == username
    assert verified["role"] == "viewer"

    # 3. Verify with incorrect password
    failed = verify_user_credentials(username, "wrongPassword")
    assert failed is None

    # Cleanup
    db.users.delete_one({"username": username})
