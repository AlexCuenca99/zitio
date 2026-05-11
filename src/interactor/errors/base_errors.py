"""This module defines the base error classes for the application"""


class BaseError(Exception):
    """
    Raised when an error occurs.
    """

    def __init__(
        self,
        status_code: int = 400,
        message: str | None = None,
        entity_name: str = "elemento",
        error_code: str | None = None,
        error_type: str | None = None,
        param: str | None = None,
        details: dict | None = None,
    ):
        """
        Initializes the instance with the given parameters.
        Args:
            status_code: The status code of the error.
            message: The message of the error.
            entity_name: The name of the entity.
            error_code: Stable error code (eg. "users.not_found").
            error_type: Error category (eg. "invalid_request_error", "api_error").
            param: Related parameter name (if any).
            details: Extra structured details for debugging/monitoring.
        """
        super().__init__(message or "Error en el servicio.")
        self.status_code = status_code
        self.entity_name = entity_name
        self.error_code = error_code
        self.error_type = error_type
        self.param = param
        self.details = details or {}

    def to_dict(self, request_id: str | None = None) -> dict:
        """Serialize the error into a consistent JSON payload."""
        payload = {
            "error": {
                "type": self.error_type or "invalid_request_error",
                "code": self.error_code,
                "message": str(self),
                "param": self.param,
                "details": self.details or None,
                "request_id": request_id,
            }
        }
        return payload


class BaseParamRequiredError(BaseError):
    """
    Raised when a required parameter is not provided.
    """

    def __init__(
        self,
        status_code: int = 400,
        param_name: str | None = None,
        entity_name: str | None = None,
        error_code: str | None = None,
        error_type: str | None = None,
        details: dict | None = None,
    ):
        """
        Initializes the instance with the given parameters.
        Args:
            status_code: The status code of the error.
            param_name: The name of the parameter.
            entity_name: The name of the entity.
        """
        message = (
            f"El parámetro /{param_name}/ es requerido."
            if param_name
            else "Un parámetro es requerido."
        )
        super().__init__(
            status_code=status_code,
            message=message,
            entity_name=entity_name or "elemento",
            error_code=error_code,
            error_type=error_type,
            param=param_name,
            details=details,
        )


class BaseItemNotFoundError(BaseError):
    """
    Raised when an item is not found.
    """

    def __init__(
        self,
        status_code: int = 404,
        search_params: dict | None = None,
        possibly_unavailable: bool = False,
        possibly_hidden: bool = False,
        entity_name: str = "elemento",
        error_code: str | None = None,
        error_type: str | None = None,
        details: dict | None = None,
    ):
        """Initializes the instance with the given parameters.

        Args:
            status_code: The status code of the error.
            search_params: The parameters used to search the entity.
            possibly_unavailable: Whether the entity could be unavailable.
            possibly_hidden: Whether the entity could be hidden.
            entity_name: The name of the entity.
        """
        message = f"El(la) {entity_name} no fue encontrado(a)."

        if isinstance(search_params, dict) and search_params:
            mapped_search_params = ", ".join(
                f"{key}: {value}" for key, value in search_params.items()
            )
            message = (
                f"El(la) {entity_name} con los parámetros de búsqueda "
                f"{mapped_search_params} no fue encontrado(a)."
            )

        if possibly_unavailable:
            message += f" El(la) {entity_name} podría estar no activo(a) o eliminado(a)."

        if possibly_hidden:
            message += f" El(la) {entity_name} podría estar oculto(a)."

        combined_details = dict(details or {})
        if isinstance(search_params, dict):
            combined_details.setdefault("search_params", search_params)
        combined_details.setdefault("possibly_unavailable", possibly_unavailable)
        combined_details.setdefault("possibly_hidden", possibly_hidden)

        super().__init__(
            status_code=status_code,
            message=message,
            entity_name=entity_name,
            error_code=error_code,
            error_type=error_type,
            details=combined_details,
        )
