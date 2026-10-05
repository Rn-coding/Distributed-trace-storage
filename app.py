"""Flask Application Factory and Entrypoint.

Binds MongoDB-driven routes for authentication, traces, analytics, and dependencies.
"""

from flask import Flask, render_template
from config import Config
from routes.auth import auth_bp
from routes.traces import traces_bp
from routes.analytics import analytics_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(traces_bp)
    app.register_blueprint(analytics_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("base.html", error_message="404: The requested resource was not found."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("base.html", error_message="500: An internal database or application error occurred."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=Config.PORT, debug=True)
