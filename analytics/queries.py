"""Core Query Implementations answering architectural questions Q1-Q6.

Each function maps to a documented project question:
- Q1: Retrieve a complete trace
- Q2: Search and filter traces
- Q3: Find slow traces exceeding threshold
- Q4: Find slow spans / bottlenecks
- Q5: Service summary performance
- Q6: Dependency summary
"""

from typing import Any, Dict, List, Optional, Tuple
from db.connection import get_database
from repositories.traces import get_trace, search_traces


def find_slow_traces(threshold_ms: float = 500.0, limit: int = 20) -> List[Dict[str, Any]]:
    """Question Q3: Find traces whose total duration exceeds threshold_ms.
    
    Uses MongoDB indexed range query on duration_ms with descending sort.
    """
    db = get_database()
    query = {"duration_ms": {"$gte": threshold_ms}}
    cursor = db.traces.find(query, {"_id": 0}).sort("duration_ms", -1).limit(limit)
    return list(cursor)


def find_slow_spans(threshold_ms: float = 300.0, limit: int = 20) -> List[Dict[str, Any]]:
    """Question Q4: Find slowest individual spans across all traces.
    
    Uses MongoDB aggregation: unwinds spans, filters by duration, sorts descending.
    """
    db = get_database()
    pipeline = [
        {"$unwind": "$spans"},
        {"$match": {"spans.duration_ms": {"$gte": threshold_ms}}},
        {"$sort": {"spans.duration_ms": -1}},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "trace_id": "$trace_id",
                "span_id": "$spans.span_id",
                "service": "$spans.service",
                "operation": "$spans.operation",
                "duration_ms": "$spans.duration_ms",
                "status": "$spans.status",
            }
        },
    ]
    return list(db.traces.aggregate(pipeline))


def service_summary() -> List[Dict[str, Any]]:
    """Question Q5: High-level performance summary for each service.
    
    Uses MongoDB aggregation:
    - Counts total spans
    - Calculates average latency
    - Calculates error count and error percentage
    """
    db = get_database()
    pipeline = [
        {"$unwind": "$spans"},
        {
            "$group": {
                "_id": "$spans.service",
                "total_spans": {"$sum": 1},
                "avg_duration_ms": {"$avg": "$spans.duration_ms"},
                "max_duration_ms": {"$max": "$spans.duration_ms"},
                "error_spans": {
                    "$sum": {"$cond": [{"$eq": ["$spans.status", "ERROR"]}, 1, 0]}
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "service": "$_id",
                "total_spans": 1,
                "avg_duration_ms": {"$round": ["$avg_duration_ms", 2]},
                "max_duration_ms": {"$round": ["$max_duration_ms", 2]},
                "error_spans": 1,
                "error_rate_pct": {
                    "$round": [
                        {
                            "$multiply": [
                                {"$divide": ["$error_spans", "$total_spans"]},
                                100,
                            ]
                        },
                        2,
                    ]
                },
            }
        },
        {"$sort": {"total_spans": -1}},
    ]
    return list(db.traces.aggregate(pipeline))


def dependency_summary() -> List[Dict[str, Any]]:
    """Question Q6: Summary of observed service dependencies."""
    db = get_database()
    cursor = db.service_dependencies.find({}, {"_id": 0}).sort("observation_count", -1)
    return list(cursor)
