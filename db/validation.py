"""MongoDB collection JSON Schema validators.

Defines schemas for:
- traces (source of truth, with embedded spans)
- services (metadata)
- operations (metadata)
- service_dependencies (materialized derived relationships)
- users (authentication credentials)
"""

TRACES_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "trace_id",
            "start_time",
            "duration_ms",
            "status",
            "root_service",
            "root_operation",
            "spans",
        ],
        "properties": {
            "trace_id": {
                "bsonType": "string",
                "description": "Unique identifier for the distributed trace",
            },
            "start_time": {
                "bsonType": "date",
                "description": "Timestamp when the trace started",
            },
            "duration_ms": {
                "bsonType": ["int", "long", "double"],
                "minimum": 0,
                "description": "Total trace duration in milliseconds",
            },
            "status": {
                "enum": ["OK", "ERROR"],
                "description": "Overall status of the trace",
            },
            "root_service": {
                "bsonType": "string",
                "description": "Name of the service originating the root span",
            },
            "root_operation": {
                "bsonType": "string",
                "description": "Name of the operation executing the root span",
            },
            "spans": {
                "bsonType": "array",
                "description": "Embedded list of spans constituting the trace tree",
                "items": {
                    "bsonType": "object",
                    "required": [
                        "span_id",
                        "service",
                        "operation",
                        "start_offset_ms",
                        "duration_ms",
                        "status",
                    ],
                    "properties": {
                        "span_id": {
                            "bsonType": "string",
                            "description": "Unique span identifier within the trace",
                        },
                        "parent_span_id": {
                            "bsonType": ["string", "null"],
                            "description": "Parent span id, or null for root span",
                        },
                        "service": {
                            "bsonType": "string",
                            "description": "Executing microservice name",
                        },
                        "operation": {
                            "bsonType": "string",
                            "description": "Executing operation / endpoint name",
                        },
                        "start_offset_ms": {
                            "bsonType": ["int", "long", "double"],
                            "minimum": 0,
                            "description": "Offset from trace start in milliseconds",
                        },
                        "duration_ms": {
                            "bsonType": ["int", "long", "double"],
                            "minimum": 0,
                            "description": "Duration of this span in milliseconds",
                        },
                        "status": {
                            "enum": ["OK", "ERROR"],
                            "description": "Execution status of this span",
                        },
                        "tags": {
                            "bsonType": "object",
                            "description": "Optional contextual key-value tags",
                        },
                    },
                },
            },
        },
    }
}

SERVICES_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["service_name", "team", "environment", "active"],
        "properties": {
            "service_name": {
                "bsonType": "string",
                "description": "Unique name of the registered microservice",
            },
            "team": {
                "bsonType": "string",
                "description": "Owner engineering team",
            },
            "environment": {
                "bsonType": "string",
                "description": "Deployment environment e.g. production, staging",
            },
            "active": {
                "bsonType": "bool",
                "description": "Whether service is actively accepting traces",
            },
        },
    }
}

OPERATIONS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["service_name", "operation_name", "operation_type", "active"],
        "properties": {
            "service_name": {
                "bsonType": "string",
                "description": "Service name to which this operation belongs",
            },
            "operation_name": {
                "bsonType": "string",
                "description": "Endpoint or method name",
            },
            "operation_type": {
                "bsonType": "string",
                "description": "Type: http, rpc, db, queue, internal",
            },
            "active": {
                "bsonType": "bool",
                "description": "Whether operation is active",
            },
        },
    }
}

SERVICE_DEPENDENCIES_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "source_service",
            "target_service",
            "observation_count",
            "error_count",
            "avg_latency_ms",
            "last_seen",
        ],
        "properties": {
            "source_service": {
                "bsonType": "string",
                "description": "Calling (parent) service name",
            },
            "target_service": {
                "bsonType": "string",
                "description": "Callee (child) service name",
            },
            "observation_count": {
                "bsonType": ["int", "long"],
                "minimum": 0,
                "description": "Total parent-child invocations observed in traces",
            },
            "error_count": {
                "bsonType": ["int", "long"],
                "minimum": 0,
                "description": "Number of invocations resulting in child ERROR status",
            },
            "avg_latency_ms": {
                "bsonType": ["int", "long", "double"],
                "minimum": 0,
                "description": "Average duration of target service child spans",
            },
            "last_seen": {
                "bsonType": "date",
                "description": "Timestamp of most recently observed trace containing this edge",
            },
        },
    }
}

USERS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["username", "password_hash", "role", "active"],
        "properties": {
            "username": {
                "bsonType": "string",
                "description": "Unique login username",
            },
            "password_hash": {
                "bsonType": "string",
                "description": "Secure hashed password",
            },
            "role": {
                "bsonType": "string",
                "description": "User role: admin or viewer",
            },
            "active": {
                "bsonType": "bool",
                "description": "Whether user account is active",
            },
        },
    }
}

SCHEMA_MAP = {
    "traces": TRACES_VALIDATOR,
    "services": SERVICES_VALIDATOR,
    "operations": OPERATIONS_VALIDATOR,
    "service_dependencies": SERVICE_DEPENDENCIES_VALIDATOR,
    "users": USERS_VALIDATOR,
}
