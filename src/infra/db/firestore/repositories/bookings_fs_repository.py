"""Firestore repository for Booking entities implementing the repository interface."""

from typing import List, Optional

from google.cloud.firestore import Client

from src.domain.entities.booking import Booking
from src.interactor.interfaces.bookings.bookings_repository import BookingsRepositoryInterface


class BookingsFirestoreRepository(BookingsRepositoryInterface):
    """Simple Firestore-backed repository for bookings."""

    def __init__(self, firestore_client: Client):
        self.firestore = firestore_client
        self.collection_name = "bookings"

    def create(self, booking: Booking) -> Booking:
        data = booking.model_dump(mode="json")
        self.firestore.collection(self.collection_name).document(booking.id).set(data)
        return booking

    def get_by_id(self, id: str) -> Optional[Booking]:
        doc = self.firestore.collection(self.collection_name).document(id).get()
        if not doc.exists:
            return None
        return Booking.model_validate(doc.to_dict())

    def list_all(self) -> List[Booking]:
        docs = self.firestore.collection(self.collection_name).stream()
        return [Booking.model_validate(d.to_dict()) for d in docs]
