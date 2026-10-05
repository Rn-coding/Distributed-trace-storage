"""Required MongoDB Aggregation Pipelines.

Implements the five architectural pipelines required by AGENTS.md and ARCHITECTURE.md:
1. average_latency_by_service
2. error_rate_by_service
3. slowest_operations
4. service_dependency_frequency
5. trace_latency_distribution

All calculations are executed directly inside MongoDB engine.
"""

from typing import Any, Dict, List
from db.connection import get_database


# ----------------------------------------------------------------------
# 1. AVERAGE LATENCY BY SERVICE
# ----------------------------------------------------------------------
def average_latency_by_service() -> List[Dict[str, Any]]:
    """Pipeline A1: Compute average, min, and max span execution latency by service.
    
    Input: traces collection
    Output: List of {service, avg_latency_ms, min_latency_ms, max_latency_ms, span_count}
    """
    db = get_database()
    pipeline = [
        {"$unwind": "$spans"},
        {
            "$group": {
                "_id": "$spans.service",
                "avg_latency_ms": {"$avg": "$spans.duration_ms"},
                "min_latency_ms": {"$min": "$spans.duration_ms"},
                "max_latency_ms": {"$max": "$spans.duration_ms"},
                "span_count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "service": "$_id",
                "avg_latency_ms": {"$round": ["$avg_latency_ms", 2]},
                "min_latency_ms": {"$round": ["$min_latency_ms", 2]},
                "max_latency_ms": {"$round": ["$max_latency_ms", 2]},
                "span_count": 1,
            }
        },
        {"$sort": {"avg_latency_ms": -1}},
    ]
    return list(db.traces.aggregate(pipeline))


# ----------------------------------------------------------------------
# 2. ERROR RATE BY SERVICE
# ----------------------------------------------------------------------
def error_rate_by_service() -> List[Dict[str, Any]]:
    """Pipeline A2: Compute error rate and error counts for each microservice.
    
    Input: traces collection
    Output: List of {service, total_spans, error_spans, error_rate_pct}
    """
    db = get_database()
    pipeline = [
        {"$unwind": "$spans"},
        {
            "$group": {
                "_id": "$spans.service",
                "total_spans": {"$sum": 1},
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
        {"$sort": {"error_rate_pct": -1, "total_spans": -1}},
    ]
    return list(db.traces.aggregate(pipeline))


# ----------------------------------------------------------------------
# 3. SLOWEST OPERATIONS
# ----------------------------------------------------------------------
def slowest_operations(limit: int = 10) -> List[Dict[str, Any]]:
    """Pipeline A3: Identify slowest operations grouped by service and operation name.
    
    Input: traces collection
    Output: List of {service, operation, avg_duration_ms, max_duration_ms, invocations}
    """
    db = get_database()
    pipeline = [
        {"$unwind": "$spans"},
        {
            "$group": {
                "_id": {
                    "service": "$spans.service",
                    "operation": "$spans.operation",
                },
                "avg_duration_ms": {"$avg": "$spans.duration_ms"},
                "max_duration_ms": {"$max": "$spans.duration_ms"},
                "invocations": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "service": "$_id.service",
                "operation": "$_id.operation",
                "avg_duration_ms": {"$round": ["$avg_duration_ms", 2]},
                "max_duration_ms": {"$round": ["$max_duration_ms", 2]},
                "invocations": 1,
            }
        },
        {"$sort": {"avg_duration_ms": -1}},
        {"$limit": limit},
    ]
    return list(db.traces.aggregate(pipeline))


# ----------------------------------------------------------------------
# 4. SERVICE DEPENDENCY FREQUENCY
# ----------------------------------------------------------------------
def service_dependency_frequency() -> List[Dict[str, Any]]:
    """Pipeline A4: Derive service invocation frequencies and error counts directly from trace parent-child span edges.
    
    Input: traces collection
    Output: List of {source_service, target_service, frequency, error_count, avg_latency_ms}
    """
    db = get_database()
    pipeline = [
        {
            "$project": {
                "edges": {
                    "$map": {
                        "input": {
                            "$filter": {
                                "input": "$spans",
                                "as": "s",
                                "cond": {"$ne": ["$$s.parent_span_id", None]},
                            }
                        },
                        "as": "child",
                        "in": {
                            "source_service": {
                                "$let": {
                                    "vars": {
                                        "parent": {
                                            "$first": {
                                                "$filter": {
                                                    "input": "$spans",
                                                    "as": "p",
                                                    "cond": {
                                                        "$eq": [
                                                            "$$p.span_id",
                                                            "$$child.parent_span_id",
                                                        ]
                                                    },
                                                }
                                            }
                                        }
                                    },
                                    "in": "$$parent.service",
                                }
                            },
                            "target_service": "$$child.service",
                            "child_duration_ms": "$$child.duration_ms",
                            "child_status": "$$child.status",
                        },
                    }
                }
            }
        },
        {"$unwind": "$edges"},
        {
            "$match": {
                "edges.source_service": {"$ne": None},
                "$expr": {
                    "$ne": ["$edges.source_service", "$edges.target_service"]
                },
            }
        },
        {
            "$group": {
                "_id": {
                    "source_service": "$edges.source_service",
                    "target_service": "$edges.target_service",
                },
                "frequency": {"$sum": 1},
                "error_count": {
                    "$sum": {
                        "$cond": [{"$eq": ["$edges.child_status", "ERROR"]}, 1, 0]
                    }
                },
                "avg_latency_ms": {"$avg": "$edges.child_duration_ms"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "source_service": "$_id.source_service",
                "target_service": "$_id.target_service",
                "frequency": 1,
                "error_count": 1,
                "avg_latency_ms": {"$round": ["$avg_latency_ms", 2]},
            }
        },
        {"$sort": {"frequency": -1}},
    ]
    return list(db.traces.aggregate(pipeline))


# ----------------------------------------------------------------------
# 5. TRACE LATENCY DISTRIBUTION
# ----------------------------------------------------------------------
def trace_latency_distribution() -> List[Dict[str, Any]]:
    """Pipeline A5: Bucket traces by duration ranges (0-100ms, 100-250ms, 250-500ms, 500-1000ms, 1000ms+).
    
    Input: traces collection
    Output: List of {range, count, avg_duration_ms, min_duration_ms, max_duration_ms}
    """
    db = get_database()
    pipeline = [
        {
            "$bucket": {
                "groupBy": "$duration_ms",
                "boundaries": [0, 100, 250, 500, 1000, 5000],
                "default": 5000,
                "output": {
                    "count": {"$sum": 1},
                    "avg_duration_ms": {"$avg": "$duration_ms"},
                    "min_duration_ms": {"$min": "$duration_ms"},
                    "max_duration_ms": {"$max": "$duration_ms"},
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "bucket_id": "$_id",
                "range": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$_id", 0]}, "then": "0 - 100 ms"},
                            {"case": {"$eq": ["$_id", 100]}, "then": "100 - 250 ms"},
                            {"case": {"$eq": ["$_id", 250]}, "then": "250 - 500 ms"},
                            {"case": {"$eq": ["$_id", 500]}, "then": "500 - 1000 ms"},
                            {"case": {"$eq": ["$_id", 1000]}, "then": "1000 - 5000 ms"},
                        ],
                        "default": "5000+ ms",
                    }
                },
                "count": 1,
                "avg_duration_ms": {"$round": ["$avg_duration_ms", 2]},
                "min_duration_ms": {"$round": ["$min_duration_ms", 2]},
                "max_duration_ms": {"$round": ["$max_duration_ms", 2]},
            }
        },
        {"$sort": {"bucket_id": 1}},
    ]
    return list(db.traces.aggregate(pipeline))
