"""Service Dependency Materialization Engine.

Materializes derived directed dependencies between services from raw trace evidence:
    parent span (source_service) -> child span (target_service)

Trace data is the source of truth; service_dependencies is purely derived and rebuildable.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from db.connection import get_database


def rebuild_service_dependencies() -> int:
    """Derive parent-child service links from traces and write into service_dependencies collection.
    
    Returns total materialized dependency edges count.
    """
    db = get_database()

    pipeline = [
        {
            "$project": {
                "trace_time": "$start_time",
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
                            "trace_time": "$start_time",
                        },
                    }
                },
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
                "observation_count": {"$sum": 1},
                "error_count": {
                    "$sum": {
                        "$cond": [{"$eq": ["$edges.child_status", "ERROR"]}, 1, 0]
                    }
                },
                "avg_latency_ms": {"$avg": "$edges.child_duration_ms"},
                "last_seen": {"$max": "$edges.trace_time"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "source_service": "$_id.source_service",
                "target_service": "$_id.target_service",
                "observation_count": 1,
                "error_count": 1,
                "avg_latency_ms": {"$round": ["$avg_latency_ms", 2]},
                "last_seen": 1,
            }
        },
    ]

    materialized_edges = list(db.traces.aggregate(pipeline))

    # Clean existing materialized collection
    db.service_dependencies.delete_many({})

    if materialized_edges:
        db.service_dependencies.insert_many(materialized_edges)

    return len(materialized_edges)


def get_service_dependencies() -> List[Dict[str, Any]]:
    """Retrieve all materialized service dependencies sorted by observation count."""
    db = get_database()
    return list(
        db.service_dependencies.find({}, {"_id": 0}).sort("observation_count", -1)
    )
