"""This module defines the decorator that requires a Firebase ID token on an endpoint."""

# Natives
from collections.abc import Callable
from functools import wraps

# Third-parties
from flask import current_app, g, request

# Locals
from src.interactor.errors import UnauthenticatedError

# app.config key holding the function that turns an ID token into a uid.
VERIFIER_CONFIG_KEY = "ID_TOKEN_VERIFIER"


def token_required(view: Callable) -> Callable:
    """Require a valid ``Authorization: Bearer <token>`` header on a view.

    The verified uid is stored in ``flask.g.uid`` for the view to use.

    Args:
        view: Flask view function to protect.

    Returns:
        The wrapped view.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        """Verify the Bearer token, then call the view.

        Args:
            *args: Positional arguments of the view.
            **kwargs: Keyword arguments of the view (URL parameters).

        Returns:
            Whatever the view returns.

        Raises:
            UnauthenticatedError: If the header is missing or not a Bearer token
                ("auth.token_missing"), or the token is invalid or expired.
        """
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        token = token.strip()
        if scheme.lower() != "bearer" or not token:
            raise UnauthenticatedError("auth.token_missing")

        g.uid = current_app.config[VERIFIER_CONFIG_KEY](token)
        return view(*args, **kwargs)

    return wrapper
