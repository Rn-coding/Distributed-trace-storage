# Jaeger-Inspired NoSQL Trace Analysis System (Phase 2)

A defensible MongoDB database project for distributed trace ingestion, indexing, aggregation analytics, and dynamic service dependency materialization.

Built with **Python 3.14**, **MongoDB 9.0**, **PyMongo**, and a lightweight server-rendered **Flask** web interface.

---

## 1. Project Overview

Modern microservice architectures generate distributed traces representing requests traversing multiple microservices. This project implements a focused database system inspired by Jaeger:
- **Embedded Document Model**: Distributed traces embed hierarchical execution spans (`span_id`, `parent_span_id`, `start_offset_ms`, `duration_ms`, `status`).
- **Database-First Work**: Query filtering, sorting, grouping, counting, averaging, and multi-stage aggregation are executed directly in MongoDB, not in Python memory scans.
- **Derived Topology**: Service dependencies (`service_dependencies`) are materialized dynamically from parent-child span pairs in trace documents.
- **Minimal Infrastructure**: Pure MongoDB + Flask; no unnecessary message queues, microservices, or complex SPA frameworks.

---

## 2. Architecture & Data Model

```text
Browser / Reviewer
       │
       │ HTTP GET/POST (HTML / Jinja2 / CSS)
       ▼
Flask Web App (app.py)
  ├── routes/auth.py        (Session-based authentication & route protection)
  ├── routes/traces.py      (Dashboard, trace explorer, timeline tree detail, CRUD)
  └── routes/analytics.py   (Aggregation reports & dependency materializer trigger)
       │
       │ PyMongo
       ▼
MongoDB 9.0 (jaeger_trace_db)
  ├── traces                (Source of truth: embedded span hierarchy)
  ├── services              (Catalog metadata: team, environment, active)
  ├── operations            (Catalog metadata: endpoint name, type)
  ├── service_dependencies  (Derived materialized directed graph: caller -> callee)
  └── users                 (Hashed credentials for system access)
```

### Primary Collections:

1. **`traces`** (Source of Truth):
   ```json
   {
     "trace_id": "T000001",
     "start_time": "ISODate(...)",
     "duration_ms": 185.0,
     "status": "OK",
     "root_service": "api-gateway",
     "root_operation": "POST /orders",
     "spans": [
       {
         "span_id": "S0001-01",
         "parent_span_id": null,
         "service": "api-gateway",
         "operation": "POST /orders",
         "start_offset_ms": 0.0,
         "duration_ms": 25.0,
         "status": "OK",
         "tags": { "http.status": 201 }
       },
       {
         "span_id": "S0001-03",
         "parent_span_id": "S0001-01",
         "service": "order-service",
         "operation": "create_order",
         "start_offset_ms": 25.0,
         "duration_ms": 110.0,
         "status": "OK",
         "tags": {}
       }
     ]
   }
   ```
2. **`services`**: Registered services metadata (`service_name`, `team`, `environment`, `active`).
3. **`operations`**: Registered operation metadata (`service_name`, `operation_name`, `operation_type`, `active`).
4. **`service_dependencies`**: Materialized service graph (`source_service`, `target_service`, `observation_count`, `error_count`, `avg_latency_ms`, `last_seen`).
5. **`users`**: User accounts (`username`, `password_hash`, `role`, `active`).

---

## 3. Requirements

- Python 3.10+ (tested on Python 3.14.2)
- MongoDB 6.0+ (tested on MongoDB 9.0.0 Community Edition)
- `mongosh` (MongoDB Shell)

---

## 4. Installation & Setup

### 1. Clone & Enter Directory
```bash
git clone <repo_url>
cd DBMS
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env` (safe development defaults are provided):
```powershell
Copy-Item .env.example .env
```

Environment variables supported in `config.py`:
- `MONGO_URI`: MongoDB connection string (default: `mongodb://127.0.0.1:27017/`)
- `MONGO_DB`: Target database name (default: `jaeger_trace_db`)
- `FLASK_SECRET_KEY`: Session encryption key
- `ADMIN_USERNAME`: Development admin username (default: `admin`)
- `ADMIN_PASSWORD`: Development admin password (default: `admin123`)
- `PORT`: Web server port (default: `5000`)

---

## 5. MongoDB Server Startup

If MongoDB is not already running as a Windows service, launch `mongod` pointing to your local data folder:
```powershell
& "C:\Program Files\MongoDB\Server\9.0\bin\mongod.exe" --dbpath "C:\data\db"
```
Verify connectivity:
```powershell
mongosh --eval "db.adminCommand('ping')"
```

---

## 6. Database Initialization & Data Generation

### Step 1: Initialize Database & Indexes
Applies JSON Schema validation rules across all 5 collections, builds required indexes, and seeds the initial development admin account:
```powershell
python init_db.py --drop
```

### Step 2: Generate Deterministic Synthetic Traces
Generates 120 realistic, varied trace documents with deterministic random seed (`seed=42`) covering multiple scenarios (normal, slow payment, slow inventory bottleneck, payment failure, auth failure, product fan-out, deep fulfillment):
```powershell
python -m generator.generate_traces --count 120
```

### Step 3: Materialize Service Dependencies
Computes caller-to-callee relationships from parent-child span links and populates `service_dependencies`:
```powershell
python -c "from analytics.dependencies import rebuild_service_dependencies; print('Materialized:', rebuild_service_dependencies(), 'edges')"
```

---

## 7. Starting the Web Application

Start the Flask development server:
```powershell
python app.py
```
Open your browser at:
**[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**

### Default Development Credentials:
- **Username**: `admin`
- **Password**: `admin123`

---

## 8. Five Required MongoDB Aggregation Pipelines

All pipelines reside in [`analytics/performance.py`](file:///C:/Users/rehan/mine/Programming/Course-work/DBMS/analytics/performance.py):

| Pipeline Name | MongoDB Stages | Question Answered |
|---|---|---|
| **`average_latency_by_service`** | `$unwind` ➔ `$group` ➔ `$project` ➔ `$sort` | Which services have the highest average execution latency? |
| **`error_rate_by_service`** | `$unwind` ➔ `$group` (conditional error sum) ➔ `$project` ➔ `$sort` | Which services suffer the highest failure rates? |
| **`slowest_operations`** | `$unwind` ➔ `$group` by `{service, operation}` ➔ `$sort` ➔ `$limit` | What are the worst bottleneck endpoints across the cluster? |
| **`service_dependency_frequency`** | `$project` (span parent map) ➔ `$unwind` ➔ `$group` by pair ➔ `$sort` | Which microservice interaction paths have the heaviest traffic and errors? |
| **`trace_latency_distribution`** | `$bucket` (0, 100, 250, 500, 1000, 5000) ➔ `$project` | What is the overall latency histogram of transactions? |

---

## 9. Index Strategy & Query Plan Justification (`explain`)

Indexes are defined in [`db/indexes.py`](file:///C:/Users/rehan/mine/Programming/Course-work/DBMS/db/indexes.py) with explicit query mappings:

1. **`traces.trace_id`** (`idx_traces_trace_id_unique`):
   - Supports Q1 (`get_trace` point lookup).
   - Execution plan: **`EXPRESS_IXSCAN`** / **`IXSCAN`** (1 document examined, 0 ms).
2. **`traces.start_time`** (`idx_traces_start_time_desc`):
   - Supports Q2 chronological trace explorer pagination.
   - Execution plan: **`IXSCAN`** avoiding expensive blocking in-memory sorts.

Run the automated index query plan verification:
```powershell
python scripts/verify_indexes.py
```

---

## 10. Running Automated Tests

Run the complete test suite:
```powershell
pytest -v
```

Test coverage includes:
- `tests/test_crud.py`: Full CRUD for traces, services, operations, and users.
- `tests/test_aggregations.py`: Execution and validation of all 5 aggregation pipelines.
- `tests/test_dependencies.py`: Reactive rebuild and graph consistency from trace mutations.
- `tests/test_routes.py`: Unauthenticated redirects, session login/logout, and page rendering.
- `tests/test_integration.py`: End-to-end clean lifecycle run from DB reset to UI verification.

---

## 11. Final Phase 2 Checklist

- [x] 5 meaningful collections (`traces`, `services`, `operations`, `service_dependencies`, `users`)
- [x] 100+ documents in total (120 traces + metadata)
- [x] JSON Schema validation rules implemented
- [x] CRUD demonstrated (Create, Read, Update, Delete)
- [x] Indexed trace retrieval by ID
- [x] Trace search and multi-criteria filtering
- [x] 5 MongoDB aggregation pipelines
- [x] 2+ justified indexes verified with `explain()`
- [x] Service dependency analysis dynamically materialized from traces
- [x] Session authentication & protected routes
- [x] Responsive server-rendered UI (plain CSS, Jinja2)
- [x] Deterministic synthetic data generator
- [x] Comprehensive test suite (15 passed tests)
- [x] Zero unnecessary infrastructure (no Redis, Kafka, Neo4j, Celery, or Docker)
