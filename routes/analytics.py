"""Routes for Performance Analytics and Service Dependencies.

Endpoints:
- /analytics: Renders tables of the 5 required MongoDB aggregation pipelines
- /dependencies: Renders the materialized service dependency graph
- /dependencies/rebuild: Triggers re-aggregation of service dependencies
"""

from flask import Blueprint, flash, redirect, render_template, url_for
from analytics.dependencies import get_service_dependencies, rebuild_service_dependencies
from analytics.performance import (
    average_latency_by_service,
    error_rate_by_service,
    service_dependency_frequency,
    slowest_operations,
    trace_latency_distribution,
)
from routes.auth import login_required

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def analytics():
    # Execute the 5 MongoDB aggregation pipelines
    avg_latency = average_latency_by_service()
    error_rates = error_rate_by_service()
    slow_ops = slowest_operations(limit=10)
    dep_freq = service_dependency_frequency()
    latency_dist = trace_latency_distribution()

    return render_template(
        "analytics.html",
        avg_latency=avg_latency,
        error_rates=error_rates,
        slow_ops=slow_ops,
        dep_freq=dep_freq,
        latency_dist=latency_dist,
    )


@analytics_bp.route("/dependencies")
@login_required
def dependencies():
    deps = get_service_dependencies()
    return render_template("dependencies.html", dependencies=deps)


@analytics_bp.route("/dependencies/rebuild", methods=["POST"])
@login_required
def rebuild_dependencies_action():
    count = rebuild_service_dependencies()
    flash(f"Materialized {count} service dependency edges from trace evidence.", "success")
    return redirect(url_for("analytics.dependencies"))
