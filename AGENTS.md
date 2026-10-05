# AGENTS.md

# Agent Instructions --- Jaeger-Inspired NoSQL Trace Analysis System

## 1. Role

You are an implementation agent working on a BTech Database Systems
project.

Your job is to implement Phase 2 incrementally according to
`ARCHITECTURE.md`.

The primary goal is a defensible MongoDB database project, not a
production-grade observability platform.

------------------------------------------------------------------------

# 2. Read Before Changing Code

Before making implementation changes:

1.  Read `ARCHITECTURE.md`.
2.  Inspect the existing repository.
3.  Identify what phase has already been completed.
4.  Run the existing tests or smoke checks.
5.  Do not recreate working functionality.
6.  Do not introduce dependencies without a concrete reason.

If the architecture and existing code conflict, stop and identify the
conflict rather than silently redesigning the project.

------------------------------------------------------------------------

# 3. Core Technology Constraints

Use:

-   Python 3.x
-   MongoDB
-   PyMongo
-   Flask for the minimal web application
-   server-rendered HTML/Jinja
-   plain CSS for responsive layout

Do not introduce:

-   Redis
-   Neo4j
-   Kafka
-   OpenTelemetry
-   Kubernetes
-   Docker
-   React/Vue/Angular
-   Celery
-   message queues
-   cloud infrastructure

unless the user explicitly changes the project scope.

The Phase-2 project should run locally.

------------------------------------------------------------------------

# 4. Database Is the Main Project

Do not turn this into a web-development project.

The important implementation is:

``` text
MongoDB
  |
  +-- document model
  +-- CRUD
  +-- indexes
  +-- aggregation
  +-- derived dependency data
  +-- validation
```

Flask exists primarily to demonstrate these capabilities.

Do not spend disproportionate effort on:

-   CSS,
-   animations,
-   dashboards,
-   frontend components,
-   visual polish.

------------------------------------------------------------------------

# 5. Data Model Rules

Primary collections:

``` text
traces
services
operations
service_dependencies
users
```

## `traces`

A trace document contains:

``` text
trace_id
start_time
duration_ms
status
root_service
root_operation
spans[]
```

Each span should contain at least:

``` text
span_id
parent_span_id
service
operation
start_offset_ms
duration_ms
status
tags
```

Do not split spans into a separate collection unless the architecture is
explicitly revised.

Do not add arbitrary collections to satisfy a count.

------------------------------------------------------------------------

# 6. Source of Truth

The source of truth is:

``` text
traces
```

The following are derived or metadata collections:

``` text
services
operations
service_dependencies
users
```

`service_dependencies` must be derivable from trace data.

If the dependency collection becomes inconsistent, it must be possible
to rebuild it.

Do not make the dependency collection the only source of dependency
information.

------------------------------------------------------------------------

# 7. Query-Driven Development

Every database feature should start with a question.

Good:

> Find the average latency of each service.

Then implement the MongoDB aggregation.

Bad:

> Add a complicated aggregation because MongoDB supports it.

For each query, record:

``` text
Question
Input
MongoDB operation
Expected result
Test
```

------------------------------------------------------------------------

# 8. MongoDB Usage Rules

Use MongoDB for:

-   filtering,
-   sorting,
-   grouping,
-   counting,
-   averaging,
-   aggregation,
-   indexing,
-   document validation.

Do not:

``` python
all_traces = list(collection.find({}))
```

and then perform the entire analysis in Python.

Python may handle:

-   request validation,
-   trace-tree reconstruction,
-   presentation,
-   orchestration,
-   controlled post-processing.

The database should perform database work.

------------------------------------------------------------------------

# 9. Required Aggregations

Maintain at least these five named pipelines:

``` text
average_latency_by_service
error_rate_by_service
slowest_operations
service_dependency_frequency
trace_latency_distribution
```

Keep the pipeline definitions readable.

Do not hide them inside giant functions.

Prefer:

``` python
pipeline = [
    ...
]
result = collection.aggregate(pipeline)
```

over dynamically generated, unreadable pipelines.

------------------------------------------------------------------------

# 10. Index Rules

At minimum, create indexes that support real access patterns.

Required candidates:

``` text
traces.trace_id
traces.start_time
```

Additional indexes should be added only when justified.

Every index should have a comment/documentation explaining:

``` text
Which query uses it?
Why is the index useful?
```

Use `explain()` when verifying important queries.

Do not claim an index improves performance without evidence.

------------------------------------------------------------------------

# 11. CRUD Rules

CRUD must operate on real entities.

Required examples:

### Create

``` text
create_trace
create_service
create_operation
```

### Read

``` text
get_trace
search_traces
get_service
```

### Update

``` text
update_service
update_operation
```

### Delete

``` text
delete_trace
```

For destructive operations, use a clear confirmation in the UI if
appropriate.

Do not create fake CRUD endpoints whose only purpose is satisfying the
rubric.

------------------------------------------------------------------------

# 12. Trace Generation Rules

Synthetic data must be useful for testing.

Use a fixed seed during development.

Generate:

-   normal traces,
-   slow traces,
-   error traces,
-   fan-out traces,
-   deep traces.

Do not generate random data where every trace is structurally identical.

The generator must make the analytics visibly meaningful.

For example:

``` text
payment is slow in some traces
inventory fails in some traces
gateway fans out to multiple services
```

The generator should produce at least 100 trace documents for the
Phase-2 milestone.

------------------------------------------------------------------------

# 13. Trace Hierarchy Rules

Use:

``` text
span_id
parent_span_id
```

to represent relationships.

A root span has:

``` text
parent_span_id = null
```

Example:

``` text
gateway
  |
  +-- order
       |
       +-- inventory
       |
       +-- payment
```

The UI should display this hierarchy in a readable way.

Do not hard-code the tree structure.

------------------------------------------------------------------------

# 14. Dependency Derivation

A dependency is inferred from parent-child span relationships.

For example:

``` text
parent span:
service = order

child span:
service = payment
```

creates:

``` text
order -> payment
```

Aggregate repeated observations.

Store useful derived fields such as:

``` text
source_service
target_service
observation_count
error_count
avg_latency_ms
last_seen
```

Do not manually insert dependency edges that do not exist in trace data.

------------------------------------------------------------------------

# 15. Authentication Rules

Basic authentication is enough.

Use:

-   password hashing,
-   session-based authentication,
-   login,
-   logout,
-   protected routes.

Never:

-   store plaintext passwords,
-   print passwords,
-   commit credentials,
-   hard-code real secrets.

Provide `.env.example`, not real credentials.

A development admin account may be created by an initialization script
with a clearly documented development password or environment-provided
password.

------------------------------------------------------------------------

# 16. Configuration Rules

Do not hard-code:

``` text
MongoDB URI
secret key
credentials
```

Use environment variables where appropriate.

Example:

``` text
MONGO_URI
MONGO_DB
FLASK_SECRET_KEY
ADMIN_USERNAME
ADMIN_PASSWORD
```

Provide safe development defaults only where appropriate.

Never commit `.env`.

------------------------------------------------------------------------

# 17. Repository Structure

Keep the implementation close to:

``` text
app.py
config.py

db/
    connection.py
    indexes.py
    validation.py

models/
    schemas.py

repositories/
    traces.py
    services.py
    operations.py
    users.py

analytics/
    performance.py
    dependencies.py

generator/
    generate_traces.py

routes/
    auth.py
    traces.py
    analytics.py

templates/
    login.html
    dashboard.html
    traces.html
    trace_detail.html

static/
    style.css
```

Small deviations are acceptable if they improve clarity.

Do not create a package/module for every tiny function.

------------------------------------------------------------------------

# 18. Incremental Work Protocol

Never implement Phase 2 in one giant change.

Work in these milestones:

``` text
M0 Environment
M1 Database initialization
M2 One trace
M3 CRUD
M4 Synthetic data
M5 Core queries
M6 Aggregations
M7 Dependencies
M8 Authentication
M9 UI
M10 Index verification
M11 Integration
```

After each milestone:

1.  run the application/tests,
2.  inspect MongoDB state,
3.  verify the milestone's acceptance criteria,
4.  fix failures,
5.  only then move on.

------------------------------------------------------------------------

# 19. M0 --- Environment

Implement:

-   virtual environment documentation,
-   requirements file,
-   MongoDB connection,
-   configuration.

Test:

``` python
db.command("ping")
```

Acceptance:

``` text
MongoDB connection succeeds.
```

Do not build UI.

------------------------------------------------------------------------

# 20. M1 --- Database Initialization

Implement:

-   database creation,
-   collections,
-   validation,
-   indexes,
-   development admin initialization.

Make initialization repeatable.

Acceptance:

``` text
A clean MongoDB instance can be initialized without manual collection creation.
```

------------------------------------------------------------------------

# 21. M2 --- One Trace

Create exactly one clear manually designed trace first.

Example:

``` text
gateway
  -> order
      -> inventory
      -> payment
```

Verify:

-   insert,
-   retrieval,
-   span contents,
-   parent IDs,
-   status,
-   duration.

Acceptance:

``` text
One complete trace is understandable in MongoDB Compass.
```

Do not generate 100 traces before this works.

------------------------------------------------------------------------

# 22. M3 --- CRUD

Implement and test CRUD repositories.

Each repository should have small functions with clear inputs/outputs.

Avoid business logic inside MongoDB connection code.

Acceptance:

``` text
Create/read/update/delete operations work against real project data.
```

------------------------------------------------------------------------

# 23. M4 --- Synthetic Data

Implement deterministic generation.

Target:

``` text
100+ traces
6–10 services
10–20 operations
5–15 spans per trace
```

Ensure multiple scenarios exist.

Acceptance:

``` text
The database contains enough variation for every major analytic query.
```

------------------------------------------------------------------------

# 24. M5 --- Core Queries

Implement:

``` text
get_trace()
search_traces()
find_slow_traces()
find_slow_spans()
service_summary()
dependency_summary()
```

Each must have a test or executable demonstration.

Acceptance:

``` text
Core project questions are answerable from MongoDB.
```

------------------------------------------------------------------------

# 25. M6 --- Aggregations

Implement the five required aggregation pipelines.

Do not replace aggregation with Python loops.

For each pipeline:

-   give it a descriptive name,
-   document the input,
-   document the output,
-   test it against known data.

Acceptance:

``` text
Five meaningful MongoDB aggregation pipelines execute successfully.
```

------------------------------------------------------------------------

# 26. M7 --- Dependency Materialization

Implement:

``` text
rebuild_service_dependencies()
```

The process should:

1.  read trace/span relationships,
2.  derive service pairs,
3.  aggregate observations,
4.  calculate useful statistics,
5.  write the derived collection.

Acceptance:

``` text
Changing trace data and rebuilding dependencies produces the expected graph.
```

------------------------------------------------------------------------

# 27. M8 --- Authentication

Implement:

``` text
/login
/logout
```

Protect:

``` text
/dashboard
/traces
/analytics
/dependencies
```

Acceptance:

``` text
Unauthenticated users cannot access protected pages.
```

------------------------------------------------------------------------

# 28. M9 --- UI

Implement only these pages:

``` text
/login
/dashboard
/traces
/traces/<trace_id>
/analytics
/dependencies
```

The UI must expose the database functionality.

Do not create a complex JavaScript application.

Acceptance:

``` text
A reviewer can demonstrate the system entirely from a browser.
```

------------------------------------------------------------------------

# 29. M10 --- Index Verification

Use MongoDB `explain()`.

Verify at least:

``` text
trace_id lookup
time-based trace search
```

Document whether the expected index is used.

Acceptance:

``` text
Two indexes have concrete query-driven justification.
```

------------------------------------------------------------------------

# 30. M11 --- Integration

Perform a clean run:

``` text
initialize DB
    ->
generate data
    ->
start application
    ->
login
    ->
CRUD
    ->
trace retrieval
    ->
analytics
    ->
dependency analysis
```

Acceptance:

``` text
No manual database editing is required for the standard demonstration.
```

------------------------------------------------------------------------

# 31. Testing Requirements

At minimum test:

### Database

-   connection,
-   initialization,
-   insert,
-   read,
-   update,
-   delete,
-   aggregation.

### Trace logic

-   root span,
-   parent-child relationship,
-   nested trace,
-   missing trace,
-   slow trace,
-   error trace.

### Authentication

-   valid login,
-   invalid login,
-   protected route,
-   logout.

### UI

-   trace search,
-   trace detail,
-   analytics page,
-   dependency page.

Tests should fail loudly.

Do not write:

``` python
try:
    ...
except:
    pass
```

------------------------------------------------------------------------

# 32. Error Handling

Expected errors must be handled clearly.

Examples:

``` text
Trace not found
Invalid duration
Invalid login
Duplicate service
MongoDB unavailable
Invalid trace ID
```

Do not expose internal stack traces to normal users.

During development, logs may contain diagnostic information.

------------------------------------------------------------------------

# 33. Code Quality Rules

Prefer:

``` python
def get_trace(trace_id):
    ...
```

over large functions that:

-   query MongoDB,
-   calculate analytics,
-   render HTML,
-   handle authentication,
-   and format output simultaneously.

Keep responsibilities separate.

Avoid unnecessary:

-   classes,
-   design patterns,
-   factories,
-   dependency injection frameworks,
-   generic repositories,
-   abstraction layers.

This is a small academic project.

------------------------------------------------------------------------

# 34. UI Rules

The UI is a demonstration layer.

Good:

``` text
table
filter
button
result
```

Avoid:

``` text
complex SPA
state-management library
animation system
custom charting framework
```

Responsive means:

-   readable on desktop,
-   usable on a narrow viewport,
-   tables do not destroy the layout,
-   navigation remains usable.

------------------------------------------------------------------------

# 35. Documentation Rules

Update `README.md` as implementation progresses.

It must eventually contain:

``` text
Project overview
Architecture
Requirements
Installation
MongoDB setup
Environment variables
Database initialization
Sample-data generation
Application startup
Demo credentials for development
Query/analytics overview
Testing
```

Do not document features that are not implemented.

------------------------------------------------------------------------

# 36. Git Rules

Make small commits aligned with milestones.

Recommended:

``` text
setup MongoDB connection
add database initialization
add trace model and first trace
implement trace CRUD
add synthetic trace generator
add aggregation analytics
add dependency materialization
add authentication
add web UI
verify indexes
```

Do not commit:

``` text
.env
credentials
MongoDB dumps
virtual environments
large generated datasets
```

------------------------------------------------------------------------

# 37. Agent Decision Rules

When uncertain:

1.  Prefer the existing architecture.
2.  Prefer the smallest implementation.
3.  Prefer MongoDB functionality over Python reimplementation.
4.  Prefer measurable evidence over assumptions.
5.  Prefer a simple working feature over a sophisticated incomplete
    feature.
6.  Ask before changing the data model.
7.  Ask before adding a new database or infrastructure component.
8.  Do not silently expand project scope.

------------------------------------------------------------------------

# 38. Forbidden Shortcuts

Do not:

-   fake aggregation results,
-   hard-code analytics,
-   hard-code dependency graphs,
-   store passwords in plaintext,
-   generate meaningless random data,
-   claim performance improvements without measurement,
-   create indexes solely to satisfy a count,
-   create collections solely to satisfy a count,
-   bypass MongoDB with in-memory dictionaries,
-   replace database queries with full-database Python scans,
-   add Neo4j/Redis because they sound more advanced,
-   build a frontend before the database functionality works.

------------------------------------------------------------------------

# 39. Final Phase-2 Checklist

Before declaring Phase 2 complete:

``` text
[ ] 5+ meaningful collections
[ ] 100+ documents
[ ] CRUD demonstrated
[ ] Trace retrieval demonstrated
[ ] Trace search demonstrated
[ ] 5+ MongoDB aggregations
[ ] 2+ justified indexes
[ ] explain() checked
[ ] Dependency analysis demonstrated
[ ] Authentication demonstrated
[ ] Responsive UI demonstrated
[ ] Synthetic data is reproducible
[ ] Error handling works
[ ] README is accurate
[ ] Clean setup works
[ ] No unnecessary infrastructure
```

The agent must not declare Phase 2 complete until every unchecked item
has either been implemented or explicitly waived by the user.
