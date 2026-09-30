"""Contract for ParkingLot repositories."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.parking_lot import ParkingLot


class ParkingLotsRepositoryInterface(ABC):
    """Repository contract for parking_lot persistence."""

    @abstractmethod
    def create(self, parking_lot: ParkingLot) -> ParkingLot:
        """Persist a parking_lot and return the persisted entity."""
        ...

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[ParkingLot]:
        """Return a parking_lot by id or None if not found."""
        ...

    @abstractmethod
    def list_all(self) -> List[ParkingLot]:
        """Return all parking_lots."""
        ...
