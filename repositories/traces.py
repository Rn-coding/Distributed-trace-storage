"""Repository for traces collection.

Implements query-driven CRUD operations on distributed traces:
- create_trace
- get_trace (Q1: Point lookup by trace_id)
- search_traces (Q2: Compound filtering by service, status, duration range, time)
- update_trace_status
- delete_trace
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from db.connection import get_database


def get_traces_collection():
    return get_database().traces


def create_trace(trace_doc: Dict[str, Any]) -> str:
    """Insert a new trace document. Returns trace_id."""
    col = get_traces_collection()
    col.insert_one(trace_doc)
    return trace_doc["trace_id"]


def get_trace(trace_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single trace document by trace_id (Q1)."""
    col = get_traces_collection()
    return col.find_one({"trace_id": trace_id}, {"_id": 0})


def search_traces(
    service: Optional[str] = None,
    operation: Optional[str] = None,
    status: Optional[str] = None,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None,
    start_time_after: Optional[datetime] = None,
    start_time_before: Optional[datetime] = None,
    limit: int = 25,
    skip: int = 0,
) -> Tuple[List[Dict[str, Any]], int]:
    """Search and filter traces using MongoDB query builder (Q2).
    
    Returns a tuple of (traces_list, total_count).
    Does NOT load entire collection into Python; uses DB-level filtering and pagination.
    """
    col = get_traces_collection()
    query: Dict[str, Any] = {}

    if service:
        # Match if service is root service or any embedded span service
        query["$or"] = [
            {"root_service": service},
            {"spans.service": service},
        ]

    if operation:
        query["spans.operation"] = operation

    if status:
        query["status"] = status

    if min_duration is not None or max_duration is not None:
        duration_query: Dict[str, Any] = {}
        if min_duration is not None:
            duration_query["$gte"] = float(min_duration)
        if max_duration is not None:
            duration_query["$lte"] = float(max_duration)
        query["duration_ms"] = duration_query

    if start_time_after is not None or start_time_before is not None:
        time_query: Dict[str, Any] = {}
        if start_time_after is not None:
            time_query["$gte"] = start_time_after
        if start_time_before is not None:
            time_query["$lte"] = start_time_before
        query["start_time"] = time_query

    total_count = col.count_documents(query)
    cursor = (
        col.find(query, {"_id": 0})
        .sort("start_time", -1)
        .skip(skip)
        .limit(limit)
    )

    return list(cursor), total_count


def update_trace_status(trace_id: str, new_status: str) -> bool:
    """Update trace status (OK/ERROR) and cascade to root span if needed."""
    if new_status not in ("OK", "ERROR"):
        raise ValueError("Status must be either 'OK' or 'ERROR'")

    col = get_traces_collection()
    result = col.update_one(
        {"trace_id": trace_id},
        {"$set": {"status": new_status}},
    )
    return result.modified_count > 0


def delete_trace(trace_id: str) -> bool:
    """Delete a trace document by trace_id."""
    col = get_traces_collection()
    result = col.delete_one({"trace_id": trace_id})
    return result.deleted_count > 0


def count_traces(query: Optional[Dict[str, Any]] = None) -> int:
    """Return total number of traces matching query."""
    col = get_traces_collection()
    return col.count_documents(query or {})
