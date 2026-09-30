"""Firestore repository for ParkingLot entities implementing the repository interface."""

from typing import List, Optional

from google.cloud.firestore import Client

from src.domain.entities.parking_lot import ParkingLot
from src.interactor.interfaces.parking_lots.parking_lots_repository import (
    ParkingLotsRepositoryInterface,
)


class ParkingLotsFirestoreRepository(ParkingLotsRepositoryInterface):
    """Simple Firestore-backed repository for parking_lots."""

    def __init__(self, firestore_client: Client):
        self.firestore = firestore_client
        self.collection_name = "parking_lots"

    def create(self, parking_lot: ParkingLot) -> ParkingLot:
        data = parking_lot.model_dump(mode="json")
        self.firestore.collection(self.collection_name).document(parking_lot.id).set(data)
        return parking_lot

    def get_by_id(self, id: str) -> Optional[ParkingLot]:
        doc = self.firestore.collection(self.collection_name).document(id).get()
        if not doc.exists:
            return None
        return ParkingLot.model_validate(doc.to_dict())

    def list_all(self) -> List[ParkingLot]:
        docs = self.firestore.collection(self.collection_name).stream()
        return [ParkingLot.model_validate(d.to_dict()) for d in docs]
