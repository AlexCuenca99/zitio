"""Contract for Booking repositories."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.booking import Booking


class BookingsRepositoryInterface(ABC):
    """Repository contract for booking persistence."""

    @abstractmethod
    def create(self, booking: Booking) -> Booking:
        """Persist a booking and return the persisted entity."""
        ...

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Booking]:
        """Return a booking by id or None if not found."""
        ...

    @abstractmethod
    def list_all(self) -> List[Booking]:
        """Return all bookings."""
        ...
