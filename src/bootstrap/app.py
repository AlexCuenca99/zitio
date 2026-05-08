"""Application bootstrap."""

from src.app.blueprints.v1.health.health_bp import create_health_bp

# from src.app.blueprints.v1.shippers.shippers_bp import create_shippers_bp
from src.app.create_app import create_app
from src.app.initialization import ConnectionInitializer
from src.bootstrap.dependencies import build_dependencies
from src.infra.loggers.logger_default import LoggerDefault


def build_app(environment):
    """Build the Flask application with all dependencies."""
    logger = LoggerDefault(environment=environment)

    initializer = ConnectionInitializer(logger)
    if not initializer.initialize_all():
        raise RuntimeError("Failed to initialize connections")

    dependencies = build_dependencies(logger)

    health_bp = create_health_bp(
        health_use_case=dependencies["health_use_case"],
    )

    # shippers_bp = create_shippers_bp(
    #     get_shipper_use_case=dependencies["get_shipper_use_case"],
    # )

    return create_app(
        blueprints=[
            health_bp,
            # shippers_bp
        ],
        logger=logger,
    )
