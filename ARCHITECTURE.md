# ARCHITECTURE.md

# Jaeger-Inspired NoSQL Trace Analysis System

## 1. Purpose

This document defines the target architecture and incremental
implementation plan for Phase 2 of the Database Systems project.

Phase 2 is not a full Jaeger clone. The implementation is a focused
database application that demonstrates:

-   a meaningful MongoDB document model,
-   trace ingestion and retrieval,
-   CRUD operations,
-   aggregation-based performance analysis,
-   service-dependency analysis,
-   indexing,
-   basic authentication,
-   a small responsive UI,
-   and enough sample data to demonstrate the database design.

The architecture must remain small enough for a BTech database project
and must prioritize database functionality over infrastructure.

------------------------------------------------------------------------

## 2. Phase-2 Acceptance Criteria

The implementation is considered Phase-2 complete only when all of the
following are demonstrable:

### Database

-   MongoDB database created and initialized by the project.
-   At least 5 meaningful collections.
-   At least 100 sample documents in total.
-   Sample trace data representing multiple services and operations.
-   At least 2 useful indexes.
-   Basic authentication implemented.
-   Database validation/schema rules where useful.

### Functionality

-   Create operation.
-   Read operation.
-   Update operation.
-   Delete operation.
-   Trace retrieval by trace ID.
-   Trace search/filtering.
-   Performance analysis.
-   Service dependency analysis.
-   At least 5 meaningful MongoDB aggregation pipelines.

### Application

-   Python application connected to MongoDB.
-   Simple responsive web UI.
-   UI can demonstrate the important database operations and analytics.
-   No unnecessary frontend framework or distributed infrastructure.

### Demonstration

The system must be runnable from a clean checkout using documented
commands.

The demonstration should be able to show:

1.  database initialization,
2.  sample-data generation,
3.  CRUD,
4.  indexed trace retrieval,
5.  aggregation analytics,
6.  dependency analysis,
7.  authentication,
8.  UI access.

These requirements directly reflect the course rubric and should be
treated as acceptance tests rather than suggestions.

------------------------------------------------------------------------

# 3. Scope

## 3.1 In scope

-   Synthetic distributed-trace generation.
-   MongoDB storage.
-   Trace and span modeling.
-   Service and operation metadata.
-   Derived service dependencies.
-   Trace retrieval.
-   Trace search.
-   Latency analysis.
-   Error analysis.
-   Service-level statistics.
-   Dependency analysis.
-   CRUD.
-   Indexing.
-   Basic authentication.
-   Responsive browser UI.
-   Query execution and result presentation.
-   Explainable database design.

## 3.2 Out of scope

Do not implement these during Phase 2:

-   OpenTelemetry collector.
-   Kubernetes integration.
-   Kafka.
-   Docker-based deployment.
-   Production-scale distributed ingestion.
-   Actual microservice deployment.
-   Real Jaeger source-code integration.
-   Redis caching.
-   Neo4j.
-   Machine learning.
-   Real-time streaming infrastructure.
-   Complex SPA frontend.
-   Cloud deployment.

These may be discussed as future work but should not consume
implementation time.

------------------------------------------------------------------------

# 4. High-Level Architecture

``` text
                    +----------------------+
                    |    Browser / User    |
                    +----------+-----------+
                               |
                               | HTTP
                               v
                    +----------------------+
                    |   Flask Application   |
                    |----------------------|
                    | Authentication       |
                    | Trace Operations     |
                    | Analytics             |
                    | Dependency Analysis  |
                    | UI / API Routes       |
                    +----------+-----------+
                               |
                               | PyMongo
                               v
                    +----------------------+
                    |       MongoDB        |
                    |----------------------|
                    | traces               |
                    | services             |
                    | operations           |
                    | dependencies         |
                    | users                |
                    +----------------------+

       +-----------------------+
       | Synthetic Trace       |
       | Generator              |
       +-----------+-----------+
                   |
                   | generated documents
                   v
                MongoDB
```

The application layer is deliberately thin. MongoDB should perform
meaningful database work through queries, indexes, and aggregation
pipelines rather than having Python calculate everything.

------------------------------------------------------------------------

# 5. Logical Data Model

The minimum architecture uses five primary collections.

## 5.1 `traces`

One document represents one distributed trace.

Example:

``` json
{
  "_id": "...",
  "trace_id": "T000001",
  "start_time": "2026-10-01T10:00:00Z",
  "duration_ms": 184,
  "status": "OK",
  "root_service": "gateway",
  "root_operation": "POST /orders",
  "spans": [
    {
      "span_id": "S000001",
      "parent_span_id": null,
      "service": "gateway",
      "operation": "POST /orders",
      "start_offset_ms": 0,
      "duration_ms": 20,
      "status": "OK",
      "tags": {
        "http.method": "POST"
      }
    },
    {
      "span_id": "S000002",
      "parent_span_id": "S000001",
      "service": "order",
      "operation": "create_order",
      "start_offset_ms": 20,
      "duration_ms": 90,
      "status": "OK",
      "tags": {}
    }
  ]
}
```

### Design rationale

Spans are embedded because the dominant trace-level access pattern is:

> Given a trace ID, retrieve the complete trace.

This makes complete trace retrieval a single document lookup.

The embedded structure also makes the parent-child relationships
immediately available for trace reconstruction.

The system must avoid unbounded documents. Synthetic traces should
remain comfortably below MongoDB's document-size limit.

------------------------------------------------------------------------

## 5.2 `services`

One document represents a known service.

Example:

``` json
{
  "_id": "...",
  "service_name": "payment",
  "team": "payments",
  "environment": "production",
  "active": true
}
```

Purpose:

-   service metadata,
-   service lookup,
-   service CRUD,
-   validation of generated traces.

------------------------------------------------------------------------

## 5.3 `operations`

One document represents a known operation.

Example:

``` json
{
  "_id": "...",
  "service_name": "payment",
  "operation_name": "charge",
  "operation_type": "internal",
  "active": true
}
```

Purpose:

-   operation metadata,
-   operation CRUD,
-   filtering and reporting.

------------------------------------------------------------------------

## 5.4 `service_dependencies`

This is derived data.

One document represents an observed service-to-service dependency.

Example:

``` json
{
  "_id": "...",
  "source_service": "order",
  "target_service": "payment",
  "observation_count": 384,
  "error_count": 7,
  "avg_latency_ms": 31.4,
  "last_seen": "2026-10-01T12:30:00Z"
}
```

This collection should not be treated as the original source of truth.
It is derived from trace/span data.

The implementation should provide a command/function that rebuilds or
updates this collection from traces.

This distinction is important:

``` text
Raw evidence
    traces
       |
       v
Derived relationship
    service_dependencies
```

------------------------------------------------------------------------

## 5.5 `users`

Used only for basic application authentication.

Example:

``` json
{
  "_id": "...",
  "username": "admin",
  "password_hash": "...",
  "role": "admin",
  "active": true
}
```

Passwords must never be stored in plaintext.

Use a standard password-hashing mechanism available in Python.

------------------------------------------------------------------------

# 6. Why Embedded Spans

The initial Review-1 design favors a trace document containing its
spans.

The implementation should preserve that choice unless measurements show
a clear problem.

Advantages:

-   complete trace retrieval is simple,
-   trace reconstruction is local to one document,
-   the schema naturally represents the trace hierarchy,
-   fewer application-level joins,
-   easy demonstration in MongoDB Compass.

Trade-off:

-   cross-trace span analytics require `$unwind`,
-   very large traces could create large documents,
-   individual span updates are less convenient.

For this project, trace retrieval and analysis are more important than
extremely large-scale ingestion, so embedding is a reasonable Phase-2
design.

Do not split spans into a separate collection merely to make the
architecture look more complex.

------------------------------------------------------------------------

# 7. Important Access Patterns

The implementation must be driven by these queries.

## Q1 --- Retrieve a complete trace

Input:

``` text
trace_id
```

Output:

``` text
trace metadata + all spans
```

Expected database operation:

``` text
find({"trace_id": ...})
```

------------------------------------------------------------------------

## Q2 --- Search traces

Possible filters:

-   service,
-   operation,
-   status,
-   minimum duration,
-   maximum duration,
-   time range.

The implementation should construct filters rather than hard-code
separate functions for every combination.

------------------------------------------------------------------------

## Q3 --- Find slow traces

Example:

> Return traces whose duration exceeds 500 ms.

This should use a MongoDB query.

------------------------------------------------------------------------

## Q4 --- Find slow services/spans

Use:

``` text
$unwind
$group
$avg / $max
$sort
```

Example result:

``` text
payment      48.2 ms
inventory    31.7 ms
order        24.1 ms
gateway      12.3 ms
```

------------------------------------------------------------------------

## Q5 --- Service performance

Calculate at least:

-   request/span count,
-   average latency,
-   maximum latency,
-   error count,
-   error rate.

This must be implemented with MongoDB aggregation rather than loading
every trace into Python and calculating statistics there.

------------------------------------------------------------------------

## Q6 --- Dependency analysis

For each parent-child span relationship:

``` text
parent service -> child service
```

derive:

``` text
gateway -> order
order   -> inventory
order   -> payment
```

Aggregate:

-   observation count,
-   average child latency,
-   error count.

------------------------------------------------------------------------

## Q7 --- Trace reconstruction

Use:

``` text
span_id
parent_span_id
```

to reconstruct the hierarchy.

The reconstruction algorithm may run in Python because this is primarily
application-level interpretation of one retrieved trace.

The database should retrieve the raw data; Python may build the display
tree.

------------------------------------------------------------------------

# 8. Required Aggregation Pipelines

At least five meaningful aggregation pipelines must exist.

Recommended set:

## A1 --- Average latency by service

``` text
traces
 -> unwind spans
 -> group by spans.service
 -> average spans.duration_ms
 -> sort descending
```

## A2 --- Error rate by service

``` text
traces
 -> unwind spans
 -> group by service
 -> count total
 -> count errors
 -> calculate error rate
```

## A3 --- Slowest operations

``` text
traces
 -> unwind spans
 -> group by service + operation
 -> average/max duration
 -> sort
 -> limit
```

## A4 --- Service dependency frequency

``` text
traces
 -> unwind spans
 -> derive parent/child relationships
 -> group by parent service + child service
 -> count
 -> sort
```

## A5 --- Trace latency distribution

Group traces into useful latency ranges or calculate:

-   count,
-   average,
-   minimum,
-   maximum.

Optional additional pipelines:

-   error traces by service,
-   top failing operations,
-   requests per time window,
-   dependency error rate,
-   slowest traces.

------------------------------------------------------------------------

# 9. Indexing Strategy

Indexes must support actual access patterns.

Minimum:

``` text
traces.trace_id
traces.start_time
```

Recommended additional indexes:

``` text
traces.status
traces.root_service
```

Do not create indexes just to increase the count.

The project should demonstrate:

``` text
query
   |
   +--> without index
   |
   +--> with index
```

and inspect the query plan with MongoDB `explain()`.

The report/demo should explain why each important index exists.

------------------------------------------------------------------------

# 10. CRUD Architecture

CRUD must be visible in the codebase.

Recommended CRUD targets:

### Create

Insert:

-   trace,
-   service,
-   operation,
-   user.

### Read

Retrieve:

-   trace by ID,
-   service,
-   operation,
-   filtered traces.

### Update

Update:

-   service metadata,
-   operation metadata,
-   trace status if the application needs correction/update behavior.

### Delete

Delete:

-   a trace,
-   a service/operation where safe.

Do not add artificial CRUD merely to satisfy the rubric. CRUD should
operate on actual project entities.

------------------------------------------------------------------------

# 11. Application Structure

Keep the code small.

Recommended structure:

``` text
jaeger-nosql/
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── app.py
├── config.py
│
├── db/
│   ├── connection.py
│   ├── indexes.py
│   └── validation.py
│
├── models/
│   └── schemas.py
│
├── repositories/
│   ├── traces.py
│   ├── services.py
│   ├── operations.py
│   └── users.py
│
├── analytics/
│   ├── performance.py
│   └── dependencies.py
│
├── generator/
│   └── generate_traces.py
│
├── routes/
│   ├── auth.py
│   ├── traces.py
│   └── analytics.py
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── traces.html
│   └── trace_detail.html
│
└── static/
    └── style.css
```

This is a logical separation, not a requirement to create large
abstractions.

------------------------------------------------------------------------

# 12. UI Architecture

The UI should be intentionally small.

Required screens:

## Login

-   username
-   password
-   authentication error

## Dashboard

Show:

-   total traces,
-   error traces,
-   average trace latency,
-   number of services,
-   slowest service.

## Trace Search

Filters:

-   trace ID,
-   service,
-   status,
-   minimum duration.

Results:

-   trace ID,
-   root service,
-   duration,
-   status,
-   timestamp.

## Trace Detail

Show:

``` text
gateway
 └── order
      ├── inventory
      └── payment
```

and a table containing span information.

## Analytics

Show results of the main aggregation queries in tables.

Charts are optional. Do not spend Phase-2 time building a visualization
framework.

The UI only needs to be responsive enough to work on desktop and narrow
screens.

------------------------------------------------------------------------

# 13. Synthetic Data Architecture

The generator should produce deterministic, realistic data.

Suggested initial dataset:

-   100+ trace documents.
-   6--10 services.
-   10--20 operations.
-   5--15 spans per trace.
-   both successful and failed traces.
-   several latency profiles.

Recommended scenarios:

### Normal

Most traces.

### Slow payment

Payment spans have unusually high duration.

### Slow inventory

Inventory becomes the bottleneck.

### Failure

One downstream service returns an error.

### Fan-out

One service calls multiple downstream services.

### Deep chain

Gateway -\> order -\> inventory -\> database.

The generator should deliberately create these patterns so the
aggregation queries produce meaningful results.

Use a fixed random seed during development so test results are
reproducible.

------------------------------------------------------------------------

# 14. Error Handling

The application must not crash on ordinary invalid input.

Examples:

-   nonexistent trace ID,
-   invalid login,
-   malformed duration filter,
-   duplicate service name,
-   invalid ObjectId,
-   MongoDB connection failure.

Database errors should be caught at the application boundary and
converted into useful messages.

Do not silently swallow exceptions.

------------------------------------------------------------------------

# 15. Validation and Integrity

Use MongoDB validation where practical.

Examples:

### Trace

Required:

``` text
trace_id
start_time
duration_ms
status
spans
```

### Span

Required:

``` text
span_id
service
operation
duration_ms
status
```

### Service

Required:

``` text
service_name
```

### User

Required:

``` text
username
password_hash
```

Validation does not need to be exhaustive. It exists to demonstrate
controlled document structure.

------------------------------------------------------------------------

# 16. Authentication

Basic authentication is sufficient.

Flow:

``` text
Browser
   |
   v
/login
   |
   v
users collection
   |
   v
password verification
   |
   v
session
   |
   v
protected pages
```

Rules:

-   hash passwords,
-   never store plaintext passwords,
-   protect dashboard/trace/analytics routes,
-   provide logout,
-   keep authorization simple.

A single `admin` role is enough for Phase 2 unless the project needs
more.

------------------------------------------------------------------------

# 17. Testing Strategy

Testing is incremental.

## Unit-level

Test:

-   trace generation,
-   filter construction,
-   hierarchy reconstruction,
-   latency calculations where Python logic exists.

## Database-level

Test:

-   insert,
-   find,
-   update,
-   delete,
-   aggregation results,
-   indexes.

## Application-level

Test:

-   login,
-   protected route access,
-   trace search,
-   trace detail,
-   analytics pages.

The most important tests should be executable scripts or automated tests
rather than screenshots.

------------------------------------------------------------------------

# 18. Incremental Implementation Plan

Do not implement the entire system at once.

## Phase 2.0 --- Environment

Goal:

``` text
Python -> MongoDB
```

Tasks:

1.  Install MongoDB.
2.  Install Python dependencies.
3.  Create virtual environment.
4.  Create repository.
5.  Connect to MongoDB.
6.  Run `ping`.
7.  Create database.

Exit condition:

``` text
MongoDB connection works from Python.
```

------------------------------------------------------------------------

## Phase 2.1 --- Database Initialization

Goal:

``` text
Database structure exists.
```

Tasks:

1.  Create the five collections.
2.  Add validation rules.
3.  Create required indexes.
4.  Create one admin user.
5.  Write an initialization script that is safe to run repeatedly.

Exit condition:

``` text
Fresh MongoDB instance can be initialized by one command/script.
```

------------------------------------------------------------------------

## Phase 2.2 --- First Real Trace

Goal:

``` text
One complete trace can be stored and retrieved.
```

Tasks:

1.  Create one manually defined trace.
2.  Insert it.
3.  Retrieve by `trace_id`.
4.  Print all spans.
5.  Verify parent-child relationships.
6.  Inspect the document in MongoDB Compass.

Exit condition:

``` text
A human can inspect the document and understand the trace.
```

Do not generate hundreds of traces yet.

------------------------------------------------------------------------

## Phase 2.3 --- Repository/Database Operations

Goal:

``` text
Database access is isolated from UI code.
```

Implement:

``` text
create_trace()
get_trace()
search_traces()
update_trace()
delete_trace()
```

Then implement equivalent operations for services and operations.

Exit condition:

``` text
CRUD works from Python without the web UI.
```

------------------------------------------------------------------------

## Phase 2.4 --- Synthetic Data Generator

Goal:

``` text
100+ useful trace documents.
```

Tasks:

1.  Define services.
2.  Define operations.
3.  Define trace templates.
4.  Generate spans.
5.  Generate normal/slow/error/fan-out scenarios.
6.  Use deterministic randomness.
7.  Load at least 100 trace documents.
8.  Verify counts.

Exit condition:

``` text
Database contains enough varied data to make analytics meaningful.
```

------------------------------------------------------------------------

## Phase 2.5 --- Core Queries

Implement in this order:

1.  trace by ID,
2.  trace search,
3.  slow traces,
4.  slow spans,
5.  service performance,
6.  dependency analysis.

Each query must have:

-   input,
-   MongoDB operation,
-   expected output,
-   test case.

Exit condition:

``` text
All major project questions can be answered from the database.
```

------------------------------------------------------------------------

## Phase 2.6 --- Aggregation Pipelines

Implement the five required aggregations.

For each:

1.  write the pipeline,
2.  run it against the sample data,
3.  inspect the result,
4.  wrap it in Python,
5.  add a test,
6.  document what question it answers.

Do not move aggregation logic into Python just because Python is easier.

Exit condition:

``` text
Five meaningful MongoDB aggregation pipelines are demonstrated.
```

------------------------------------------------------------------------

## Phase 2.7 --- Dependency Materialization

Goal:

``` text
Raw traces -> service dependency collection
```

Tasks:

1.  Extract parent-child service pairs.
2.  Aggregate observations.
3.  Calculate latency/error statistics.
4.  Write/update `service_dependencies`.
5.  Add a query for the dependency table.

Exit condition:

``` text
The system can show service A -> service B relationships from stored traces.
```

------------------------------------------------------------------------

## Phase 2.8 --- Authentication

Goal:

``` text
Unauthenticated users cannot access the application.
```

Tasks:

1.  Create users collection.
2.  Add password hashing.
3.  Implement login.
4.  Implement logout.
5.  Protect application routes.
6.  Test invalid credentials.

Exit condition:

``` text
Login and route protection work.
```

------------------------------------------------------------------------

## Phase 2.9 --- Minimal Responsive UI

Goal:

``` text
All important database functionality is demonstrable from a browser.
```

Implement in this order:

1.  login,
2.  dashboard,
3.  trace search,
4.  trace detail,
5.  analytics,
6.  dependency view.

Use server-rendered HTML and simple CSS.

Exit condition:

``` text
A reviewer can use the application without running database commands manually.
```

------------------------------------------------------------------------

## Phase 2.10 --- Index and Query Verification

Goal:

``` text
Indexes are justified, not decorative.
```

Tasks:

1.  Run important queries without/with indexes where practical.
2.  Inspect `explain()` output.
3.  Confirm index usage.
4.  Record observations.
5.  Remove useless indexes.

Exit condition:

``` text
At least two indexes have a clear access-pattern justification.
```

------------------------------------------------------------------------

## Phase 2.11 --- Integration and Cleanup

Tasks:

1.  Run from a clean checkout.
2.  Initialize database.
3.  Generate sample data.
4.  Start application.
5.  Login.
6.  Demonstrate CRUD.
7.  Demonstrate trace retrieval.
8.  Demonstrate five aggregations.
9.  Demonstrate dependency analysis.
10. Check 100+ documents.
11. Remove dead code.
12. Update README.
13. Freeze Phase-2 scope.

Exit condition:

``` text
The complete Phase-2 workflow works from start to finish.
```

------------------------------------------------------------------------

# 19. Definition of Done

Phase 2 is done when:

``` text
[ ] MongoDB database initializes successfully
[ ] 5+ meaningful collections exist
[ ] 100+ documents exist
[ ] Trace data is realistic and varied
[ ] CRUD works
[ ] Trace retrieval works
[ ] Trace search works
[ ] 5+ aggregation pipelines work
[ ] 2+ useful indexes exist
[ ] Index usage is verified
[ ] Dependency analysis works
[ ] Basic authentication works
[ ] Responsive UI works
[ ] Error handling exists
[ ] Source code is organized
[ ] README contains setup/run instructions
[ ] Clean-checkout demonstration succeeds
```

------------------------------------------------------------------------

# 20. Phase-2 Demonstration Sequence

The final demo should follow a fixed sequence.

### 1. Show architecture

``` text
Browser -> Flask -> PyMongo -> MongoDB
                         ^
                         |
                  Trace Generator
```

### 2. Show collections

``` text
traces
services
operations
service_dependencies
users
```

### 3. Show sample trace

Open one trace and explain:

``` text
trace_id
root service
spans
parent_span_id
duration
status
```

### 4. Demonstrate CRUD

Create/read/update/delete one real entity.

### 5. Demonstrate indexed query

Retrieve a trace using `trace_id`.

### 6. Demonstrate aggregation

Show:

-   service latency,
-   error rate,
-   slow operations,
-   dependency frequency,
-   trace latency distribution.

### 7. Demonstrate dependency analysis

Show:

``` text
gateway -> order
order -> inventory
order -> payment
```

### 8. Demonstrate authentication

Logout and show that protected pages require login.

------------------------------------------------------------------------

# 21. Architectural Rules

These rules should not be violated without a documented reason.

1.  MongoDB is the primary data store.
2.  MongoDB must perform meaningful query and aggregation work.
3.  Python must not simply load the entire database and perform all
    analytics itself.
4.  Trace data is the source of truth.
5.  Service dependencies are derived data.
6.  Every index must support a real query.
7.  Synthetic data must contain controlled scenarios.
8.  The UI must remain thin.
9.  No additional infrastructure is introduced without a concrete
    requirement.
10. Do not optimize before measuring.
11. Do not add a second database merely to make the project look more
    advanced.
12. Prefer a working small feature over an unfinished large feature.
