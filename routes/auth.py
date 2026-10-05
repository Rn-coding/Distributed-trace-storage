"""Authentication Blueprint and Route Protection.

Implements session-based authentication:
- /login (GET / POST)
- /logout (GET)
- login_required decorator for protected views
"""

from functools import wraps
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from repositories.users import verify_user_credentials

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    """Decorator protecting routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("traces.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = verify_user_credentials(username, password)
        if user:
            session["user"] = user
            flash(f"Welcome back, {user['username']}!", "success")
            next_url = request.args.get("next") or url_for("traces.dashboard")
            return redirect(next_url)
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
