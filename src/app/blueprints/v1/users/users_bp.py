"""This module defines the users blueprint exposing create, get and list endpoints."""

from flask import Blueprint, request

from src.app.auth import token_required
from src.interactor.use_cases.users.users_use_case import UsersUseCase


def users_bp(users_use_case: UsersUseCase, version: str = "v1") -> Blueprint:
    """Build the users blueprint.

    Args:
        users_use_case: Use case the endpoints delegate to.
        version: API version used in the URL prefix.

    Returns:
        The blueprint mounted at ``/api/<version>/users``; every endpoint requires a
        Firebase ID token.
    """
    bp = Blueprint("users_v1", __name__, url_prefix=f"/api/{version}/users")

    @bp.post("")
    @token_required
    def create_user() -> dict:
        """Create a user from the JSON body.

        Returns:
            The success body with the created user.
        """
        payload = request.get_json(force=True)
        return users_use_case.create(payload)

    @bp.get("/<string:uid>")
    @token_required
    def get_user(uid: str) -> dict:
        """Get a user by uid.

        Args:
            uid: Identifier of the user.

        Returns:
            The success body with the user.
        """
        return users_use_case.get(uid)

    @bp.get("")
    @token_required
    def list_users() -> dict:
        """List every user.

        Returns:
            The success body with all users.
        """
        return users_use_case.list()

    return bp
