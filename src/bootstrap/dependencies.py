"""This module defines the application dependency factory."""

from src.infra.db.firestore.firestore_base import firestore_client
from src.infra.loggers.logger_default import LoggerDefault
from src.interactor.use_cases.health.health_use_case import HealthUseCase

# Example repositories/use cases for future entities
# from src.infra.db.firestore.repositories.shipper_firestore_repository import (
#     ShipperFirestoreRepository,
# )
# from src.infra.db.redis.repositories.shipper_redis_repository import (
#     ShipperRedisRepository,
# )
# from src.interactor.use_cases.shippers.get_shipper_use_case import (
#     GetShipperUseCase,
# )


def build_dependencies(logger: LoggerDefault):
    """Build all application dependencies."""
    # shipper_firestore_repository = ShipperFirestoreRepository(
    #     firestore_client=firestore_client,
    # )
    # shipper_redis_repository = ShipperRedisRepository(
    #     redis_client=redis_client,
    # )

    health_use_case = HealthUseCase(
        logger=logger,
        firestore_client=firestore_client,
    )

    # get_shipper_use_case = GetShipperUseCase(
    #     shipper_firestore_repository=shipper_firestore_repository,
    #     shipper_redis_repository=shipper_redis_repository,
    # )

    return {
        "health_use_case": health_use_case,
        # "get_shipper_use_case": get_shipper_use_case,
    }
