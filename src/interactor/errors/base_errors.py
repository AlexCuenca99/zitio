"""This module defines the error classes the API raises, one per kind of failure."""

from src.interactor.errors.catalog import ERROR_CATALOG


class BaseError(Exception):
    """Base class of every error the API answers with.

    Subclasses model the kind of failure (not found, invalid parameter, internal...).
    The code is data: it names the entity and event (e.g. "users.not_found") and must
    exist in ``ERROR_CATALOG``, which supplies its status, type and entity name. Add a
    subclass only for a domain rule that callers catch on its own or that builds its
    message from its own data.

    ``scope`` (stored in ``details``) names where the error happened: the operation for
    an entity error (e.g. "get") or the owning flow for a generic one. It never changes
    the code, which is the client contract; it only enriches ``log_event``.

    Attributes:
        message: Internal technical message in English, used in logs.
        client_message: User-facing message in Spanish, used in API responses.
        status_code: HTTP status code for the error.
        entity_name: Spanish name of the entity involved.
        error_code: Stable dot-notation code (e.g. "users.not_found").
        error_type: Error category ("invalid_request_error" or "api_error").
        param: Related parameter name, if any.
        details: Extra structured data for debugging and monitoring.
    """

    def __init__(
        self,
        status_code: int = 400,
        message: str | None = None,
        client_message: str | None = None,
        entity_name: str = "elemento",
        error_code: str = "base",
        error_type: str | None = None,
        param: str | None = None,
        details: dict | None = None,
    ):
        """Initialize the error.

        Args:
            status_code: HTTP status code for the error.
            message: Internal technical message in English, used in logs.
            client_message: User-facing message in Spanish, used in API responses.
                Falls back to message if not provided.
            entity_name: Spanish name of the entity involved.
            error_code: Stable dot-notation code (e.g. "users.not_found").
            error_type: Error category ("invalid_request_error" or "api_error").
            param: Related parameter name, if any.
            details: Extra structured data for debugging and monitoring.
        """
        msg = message or "Error en el servicio."
        super().__init__(msg)
        self.message = msg
        self.client_message = client_message
        self.status_code = status_code
        self.entity_name = entity_name
        self.error_code = error_code
        self.error_type = error_type
        self.param = param
        self.details = details or {}

    def to_dict(self, request_id: str | None = None) -> dict:
        """Serialize the error into the API error body.

        Args:
            request_id: Trace id of the request, so the client can report it.

        Returns:
            The body ``{"status": "fail", "error": {...}}`` every error response shares.
        """
        return {
            "status": "fail",
            "error": {
                "type": self.error_type or "invalid_request_error",
                "code": self.error_code,
                "message": self.client_message or str(self),
                "param": self.param,
                "details": self.details or None,
                "request_id": request_id,
            },
        }

    @property
    def log_event(self) -> str:
        """Build the observability key for structured logging.

        Returns:
            ``<entity>.<scope>.<event>`` when the error has a scope (e.g.
            "users.get.not_found"), otherwise the error code itself.
        """
        scope = self.details.get("scope")
        if not scope or "." not in self.error_code:
            return self.error_code
        entity, event = self.error_code.split(".", 1)
        return f"{entity}.{str(scope).lower()}.{event}"


def _from_catalog(code: str, default_status: int) -> dict:
    """Resolve the BaseError keyword arguments a catalog code defines.

    Args:
        code: Error code to look up in ``ERROR_CATALOG``.
        default_status: Status used when the code is missing from the catalog.

    Returns:
        The ``status_code``, ``error_code``, ``error_type``, ``message`` and
        ``client_message`` keyword arguments for ``BaseError``.
    """
    entry = ERROR_CATALOG.get(code, {})
    status_code = entry.get("http_status", default_status)
    return {
        "status_code": status_code,
        "error_code": code,
        "error_type": entry.get(
            "type", "api_error" if status_code >= 500 else "invalid_request_error"
        ),
        "message": entry.get("message"),
        "client_message": entry.get("client_message"),
    }


class ParamRequiredError(BaseError):
    """Raised when a required parameter is missing."""

    def __init__(
        self,
        code: str = "request.param_required",
        *,
        param_name: str | None = None,
        scope: str | None = None,
    ):
        """Initialize the error from its catalog code.

        Args:
            code: Error code from the catalog (e.g. "users.param_required").
            param_name: Dot-notation path of the missing parameter.
            scope: Operation or model the parameter belongs to.
        """
        message = (
            f"El parámetro /{param_name}/ es requerido."
            if param_name
            else "Un parámetro es requerido."
        )
        kwargs = _from_catalog(code, 400)
        kwargs.update(message=message, client_message=message)
        super().__init__(
            **kwargs,
            param=param_name,
            details={"scope": scope, "param_name": param_name},
        )


class ParamInvalidError(BaseError):
    """Raised when a parameter is present but does not meet its constraints."""

    def __init__(
        self,
        code: str = "request.param_invalid",
        *,
        param_name: str | None = None,
        reason: str | None = None,
        scope: str | None = None,
        errors: list[dict] | None = None,
    ):
        """Initialize the error from its catalog code.

        Args:
            code: Error code from the catalog.
            param_name: Dot-notation path of the offending parameter.
            reason: Technical reason in English, used in logs.
            scope: Operation or model the validation belongs to.
            errors: Every validation error found, not just the first one.
        """
        kwargs = _from_catalog(code, 400)
        kwargs.update(
            message=f"{param_name}: {reason}" if reason else "Invalid parameter.",
            client_message=f"El parámetro /{param_name}/ es inválido.",
        )
        super().__init__(
            **kwargs,
            param=param_name,
            details={"scope": scope, "param_name": param_name, "errors": errors},
        )


class NotFoundError(BaseError):
    """Raised when a resource is not found, whatever the lookup criteria."""

    def __init__(
        self,
        code: str = "resource.not_found",
        *,
        search_params: dict | None = None,
        scope: str | None = None,
    ):
        """Initialize the error from its catalog code.

        Args:
            code: Error code from the catalog (e.g. "users.not_found").
            search_params: Every criterion the lookup used, e.g. ``{"uid": "..."}`` or
                ``{"first_name": "Ana", "last_name": "Pérez"}``. Its keys become
                ``param``, comma separated.
            scope: Operation or flow where the lookup happened (e.g. "get").
        """
        search_params = search_params or {}
        entity_name = ERROR_CATALOG.get(code, {}).get("entity_name", "elemento")
        message = f"El(la) {entity_name} no fue encontrado(a)."
        if search_params:
            criteria = ", ".join(f"{key}: {value}" for key, value in search_params.items())
            message = (
                f"El(la) {entity_name} con los parámetros de búsqueda {criteria} "
                "no fue encontrado(a)."
            )

        kwargs = _from_catalog(code, 404)
        kwargs.update(message=message, client_message=message)
        super().__init__(
            **kwargs,
            entity_name=entity_name,
            param=", ".join(search_params) or None,
            details={"scope": scope, "search_params": search_params},
        )


class InternalError(BaseError):
    """Raised when the service fails on its own side; the client never sees the cause."""

    def __init__(
        self,
        code: str = "internal_error",
        *,
        message: str | None = None,
        scope: str | None = None,
        details: dict | None = None,
    ):
        """Initialize the error from its catalog code.

        Args:
            code: Error code from the catalog (e.g. "users.internal_error").
            message: Technical reason in English, used in logs only.
            scope: Operation or flow that failed (e.g. "create").
            details: Extra structured data for the logs.
        """
        kwargs = _from_catalog(code, 500)
        if message:
            kwargs["message"] = message
        # The technical message must never reach the client.
        kwargs["client_message"] = kwargs["client_message"] or "Ocurrió un error interno."
        super().__init__(**kwargs, details={**(details or {}), "scope": scope})
