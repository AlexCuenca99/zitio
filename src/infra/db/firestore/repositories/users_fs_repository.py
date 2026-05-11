"""Firestore repository for User entities implementing the repository interface."""

from typing import List, Optional

from google.cloud.firestore import Client

from src.domain.entities.user import User
from src.interactor.interfaces.users.users_repository import UsersRepositoryInterface


class UsersFirestoreRepository(UsersRepositoryInterface):
    """Simple Firestore-backed repository for users."""

    def __init__(self, firestore_client: Client):
        self.firestore = firestore_client
        self.collection_name = "users"

    def create(self, user: User) -> User:
        data = user.model_dump(mode="json")
        self.firestore.collection(self.collection_name).document(user.uid).set(data)
        return user

    def get_by_uid(self, uid: str) -> Optional[User]:
        doc = self.firestore.collection(self.collection_name).document(uid).get()
        if not doc.exists:
            return None
        return User.model_validate(doc.to_dict())

    def list_all(self) -> List[User]:
        docs = self.firestore.collection(self.collection_name).stream()
        return [User.model_validate(d.to_dict()) for d in docs]
