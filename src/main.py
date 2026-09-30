"""Main entry point for the Flask application."""

# Third-parties
from flask import Flask

# Locals
from configs.config import settings
from src.bootstrap.app import build_app


def start_app() -> Flask:
    """Initialize and start the Flask application."""
    return build_app(environment=settings.environment)


# Create app instance for Gunicorn
app = start_app()

if __name__ == "__main__":
    app.run(debug=settings.flask_debug, host=settings.flask_host, port=5000)
