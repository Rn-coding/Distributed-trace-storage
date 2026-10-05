"""Test suite verifying Milestone M8 Authentication and M9 Web UI routes."""

import pytest
from app import create_app
from config import Config
from repositories.traces import search_traces


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.test_client() as test_client:
        yield test_client


def test_unauthenticated_redirects(client):
    """Verify unauthenticated requests to protected endpoints redirect to login."""
    protected_urls = ["/dashboard", "/traces", "/analytics", "/dependencies"]
    for url in protected_urls:
        res = client.get(url, follow_redirects=False)
        assert res.status_code == 302
        assert "/login" in res.headers["Location"]


def test_login_invalid_credentials(client):
    res = client.post("/login", data={"username": "admin", "password": "wrongpassword"}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Invalid username or password" in res.data


def test_login_and_access_protected_pages(client):
    # 1. Login with valid admin credentials
    res = client.post(
        "/login",
        data={"username": Config.ADMIN_USERNAME, "password": Config.ADMIN_PASSWORD},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Operational Overview" in res.data

    # 2. Access /dashboard
    dash_res = client.get("/dashboard")
    assert dash_res.status_code == 200
    assert b"Total Ingested Traces" in dash_res.data

    # 3. Access /traces
    traces_res = client.get("/traces")
    assert traces_res.status_code == 200
    assert b"Distributed Traces Explorer" in traces_res.data

    # 4. Access /traces/<trace_id>
    traces_list, _ = search_traces(limit=1)
    assert len(traces_list) > 0
    sample_id = traces_list[0]["trace_id"]

    detail_res = client.get(f"/traces/{sample_id}")
    assert detail_res.status_code == 200
    assert sample_id.encode() in detail_res.data
    assert b"Span Hierarchy" in detail_res.data

    # 5. Access /analytics
    analytics_res = client.get("/analytics")
    assert analytics_res.status_code == 200
    assert b"Average Latency by Service" in analytics_res.data
    assert b"Error Rate by Service" in analytics_res.data
    assert b"Top Slowest Operations" in analytics_res.data

    # 6. Access /dependencies
    dep_res = client.get("/dependencies")
    assert dep_res.status_code == 200
    assert b"Materialized Service Dependencies" in dep_res.data

    # 7. Logout
    logout_res = client.get("/logout", follow_redirects=True)
    assert logout_res.status_code == 200
    assert b"You have been logged out" in logout_res.data

    # 8. Re-attempt accessing /dashboard after logout
    after_logout = client.get("/dashboard", follow_redirects=False)
    assert after_logout.status_code == 302
    assert "/login" in after_logout.headers["Location"]
