"""This module defines the users blueprint exposing the authenticated user's profile."""

from flask import Blueprint, g, request

from src.app.auth import token_required
from src.interactor.use_cases.users.users_use_case import UsersUseCase


def users_bp(users_use_case: UsersUseCase, version: str = "v1") -> Blueprint:
    """Build the users blueprint.

    Every endpoint acts on the profile of the token's owner: the uid and email always come
    from the verified token, never from the request.

    Args:
        users_use_case: Use case the endpoints delegate to.
        version: API version used in the URL prefix.

    Returns:
        The blueprint mounted at ``/api/<version>/users``.
    """
    bp = Blueprint("users_v1", __name__, url_prefix=f"/api/{version}/users")

    @bp.post("/me")
    @token_required
    def create_my_profile() -> tuple[dict, int]:
        """Create the caller's profile from the JSON body.

        Returns:
            The success body with the created profile and status 201.
        """
        payload = request.get_json(force=True)
        return users_use_case.create_profile(g.uid, g.email, payload), 201

    @bp.get("/me")
    @token_required
    def get_my_profile() -> dict:
        """Get the caller's profile.

        Returns:
            The success body with the profile.
        """
        return users_use_case.get_profile(g.uid)

    @bp.patch("/me")
    @token_required
    def update_my_profile() -> dict:
        """Update the caller's profile from the JSON body.

        Returns:
            The success body with the updated profile.
        """
        payload = request.get_json(force=True)
        return users_use_case.update_profile(g.uid, payload)

    return bp
