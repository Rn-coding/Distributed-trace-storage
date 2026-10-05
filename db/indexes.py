"""Index creation and justification definitions.

Every index defined here directly maps to access patterns in ARCHITECTURE.md:
- Q1: trace retrieval by ID
- Q2: trace filtering by time, status, and root service
- Aggregations A1-A4: span-level grouping and unwinding
- Entity lookups and uniqueness constraints across services, operations, and users.
"""

from pymongo import ASCENDING, DESCENDING, IndexModel


def create_all_indexes(db):
    """Create all required and justified indexes on the target database."""
    results = {}

    # 1. TRACES COLLECTION INDEXES
    trace_indexes = [
        # Query: Q1 (get_trace by trace_id)
        # Why: Enables point lookups in O(1) time (IXSCAN) without full collection scan (COLLSCAN).
        # Enforces uniqueness of trace_id across distributed trace documents.
        IndexModel(
            [("trace_id", ASCENDING)],
            unique=True,
            name="idx_traces_trace_id_unique",
        ),
        # Query: Q2 (search_traces sorted by recency)
        # Why: Traces are queried in descending chronological order.
        # This index eliminates in-memory blocking sort and supports time-range queries.
        IndexModel(
            [("start_time", DESCENDING)],
            name="idx_traces_start_time_desc",
        ),
        # Query: Q2 & Q3 (filtering by trace execution status: OK vs ERROR)
        # Why: Allows quick identification and retrieval of failed traces without scanning healthy traces.
        IndexModel(
            [("status", ASCENDING)],
            name="idx_traces_status",
        ),
        # Query: Q2 & Dashboard (filtering traces originating from a specific entrypoint service)
        # Why: Enables fast lookup of traces by top-level caller.
        IndexModel(
            [("root_service", ASCENDING)],
            name="idx_traces_root_service",
        ),
        # Query: A1, A2, A3 (aggregations unwinding and matching spans by microservice name)
        # Why: Multikey index on embedded spans.service supports pipeline match stages on service names.
        IndexModel(
            [("spans.service", ASCENDING)],
            name="idx_traces_spans_service",
        ),
    ]
    results["traces"] = db.traces.create_indexes(trace_indexes)

    # 2. SERVICES COLLECTION INDEXES
    service_indexes = [
        # Query: Service metadata lookup, create_service, get_service
        # Why: Enforces uniqueness of service names and speeds up point lookups by name.
        IndexModel(
            [("service_name", ASCENDING)],
            unique=True,
            name="idx_services_service_name_unique",
        ),
    ]
    results["services"] = db.services.create_indexes(service_indexes)

    # 3. OPERATIONS COLLECTION INDEXES
    operation_indexes = [
        # Query: Operation metadata lookup and CRUD
        # Why: Compound unique constraint prevents duplicate operation names for the same service.
        IndexModel(
            [("service_name", ASCENDING), ("operation_name", ASCENDING)],
            unique=True,
            name="idx_operations_service_operation_unique",
        ),
    ]
    results["operations"] = db.operations.create_indexes(operation_indexes)

    # 4. SERVICE_DEPENDENCIES COLLECTION INDEXES
    dependency_indexes = [
        # Query: Dependency graph queries and rebuild upserts
        # Why: Ensures uniqueness of directed service-to-service pairs (source -> target).
        IndexModel(
            [("source_service", ASCENDING), ("target_service", ASCENDING)],
            unique=True,
            name="idx_dependencies_source_target_unique",
        ),
    ]
    results["service_dependencies"] = db.service_dependencies.create_indexes(
        dependency_indexes
    )

    # 5. USERS COLLECTION INDEXES
    user_indexes = [
        # Query: Authentication username lookup (/login)
        # Why: Guarantees unique usernames and provides instantaneous lookup during login authentication.
        IndexModel(
            [("username", ASCENDING)],
            unique=True,
            name="idx_users_username_unique",
        ),
    ]
    results["users"] = db.users.create_indexes(user_indexes)

    return results
