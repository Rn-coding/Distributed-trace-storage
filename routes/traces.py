"""Routes for Dashboard and Traces Views.

Endpoints:
- / -> redirect to /dashboard
- /dashboard: summary stats and recent traces
- /traces: filtered trace list with pagination
- /traces/<trace_id>: trace hierarchy tree and span details
- /traces/<trace_id>/delete: trace deletion
"""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from analytics.performance import average_latency_by_service
from analytics.tree import build_trace_tree
from db.connection import get_database
from repositories.services import list_services
from repositories.traces import count_traces, delete_trace, get_trace, search_traces
from routes.auth import login_required

traces_bp = Blueprint("traces", __name__)


@traces_bp.route("/")
def index():
    return redirect(url_for("traces.dashboard"))


@traces_bp.route("/dashboard")
@login_required
def dashboard():
    db = get_database()
    total_traces = count_traces()
    error_traces = count_traces({"status": "ERROR"})
    service_count = db.services.count_documents({})

    # Compute average latency across all traces via aggregation
    avg_pipeline = [
        {"$group": {"_id": None, "avg_dur": {"$avg": "$duration_ms"}}}
    ]
    avg_res = list(db.traces.aggregate(avg_pipeline))
    avg_latency = round(avg_res[0]["avg_dur"], 1) if avg_res else 0.0

    # Get slowest service from A1 aggregation
    service_latencies = average_latency_by_service()
    slowest_service = service_latencies[0] if service_latencies else None

    # Recent traces
    recent_traces, _ = search_traces(limit=8)

    return render_template(
        "dashboard.html",
        total_traces=total_traces,
        error_traces=error_traces,
        service_count=service_count,
        avg_latency=avg_latency,
        slowest_service=slowest_service,
        recent_traces=recent_traces,
    )


@traces_bp.route("/traces")
@login_required
def traces_list():
    service = request.args.get("service", "").strip() or None
    status = request.args.get("status", "").strip() or None
    min_dur = request.args.get("min_duration", "").strip()
    max_dur = request.args.get("max_duration", "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    limit = 20
    skip = (page - 1) * limit

    min_duration = float(min_dur) if min_dur else None
    max_duration = float(max_dur) if max_dur else None

    traces, total_count = search_traces(
        service=service,
        status=status,
        min_duration=min_duration,
        max_duration=max_duration,
        limit=limit,
        skip=skip,
    )

    total_pages = max((total_count + limit - 1) // limit, 1)
    services = list_services()

    return render_template(
        "traces.html",
        traces=traces,
        services=services,
        selected_service=service,
        selected_status=status,
        min_duration=min_dur,
        max_duration=max_dur,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
    )


@traces_bp.route("/traces/<trace_id>")
@login_required
def trace_detail(trace_id):
    trace = get_trace(trace_id)
    if not trace:
        flash(f"Trace '{trace_id}' not found.", "danger")
        return redirect(url_for("traces.traces_list"))

    # Reconstruct dynamic span hierarchy tree
    tree_spans = build_trace_tree(trace)

    return render_template(
        "trace_detail.html",
        trace=trace,
        tree_spans=tree_spans,
    )


@traces_bp.route("/traces/<trace_id>/delete", methods=["POST"])
@login_required
def delete_trace_action(trace_id):
    success = delete_trace(trace_id)
    if success:
        flash(f"Trace {trace_id} was successfully deleted.", "success")
    else:
        flash(f"Could not delete trace {trace_id}.", "danger")
    return redirect(url_for("traces.traces_list"))
