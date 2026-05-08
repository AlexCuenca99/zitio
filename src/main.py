"""Main entry point for the Flask application."""

# Third-parties
from flask import Flask

# Locals
from configs.config import FLASK_DEBUG, FLASK_HOST, environment
from src.bootstrap.app import build_app


def start_app() -> Flask:
    """Initialize and start the Flask application."""
    return build_app(environment=environment)


# Create app instance for Gunicorn
app = start_app()

if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=5000)
