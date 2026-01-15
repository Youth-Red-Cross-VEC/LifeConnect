from fastapi import HTTPException, status
from typing import Any, Optional


class LifeConnectException(Exception):
    """Base exception for LifeConnect application."""

    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(message)


class EntityNotFoundError(LifeConnectException):
    """Raised when a requested entity is not found."""

    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            message=f"{entity_type} with id '{entity_id}' not found",
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class DuplicateEntityError(LifeConnectException):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_type: str, field: str, value: str):
        super().__init__(
            message=f"{entity_type} with {field} '{value}' already exists",
            details={"entity_type": entity_type, "field": field, "value": value},
        )


class InvalidCredentialsError(LifeConnectException):
    """Raised when authentication credentials are invalid."""

    def __init__(self):
        super().__init__(message="Invalid email or password")


class UnauthorizedError(LifeConnectException):
    """Raised when user is not authorized to perform an action."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message=message)


class ForbiddenError(LifeConnectException):
    """Raised when access to a resource is forbidden."""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message=message)


class ValidationError(LifeConnectException):
    """Raised when input validation fails."""

    def __init__(self, message: str, errors: Optional[list] = None):
        super().__init__(message=message, details={"errors": errors or []})


class ExternalServiceError(LifeConnectException):
    """Raised when an external service call fails."""

    def __init__(self, service_name: str, message: str):
        super().__init__(
            message=f"External service error ({service_name}): {message}",
            details={"service": service_name},
        )


class EmailSendError(ExternalServiceError):
    """Raised when email sending fails."""

    def __init__(self, message: str):
        super().__init__(service_name="Email", message=message)


class GoogleMapsError(ExternalServiceError):
    """Raised when Google Maps API call fails."""

    def __init__(self, message: str):
        super().__init__(service_name="Google Maps", message=message)


class BloodRequestError(LifeConnectException):
    """Raised for blood request related errors."""

    pass


class DonorError(LifeConnectException):
    """Raised for donor related errors."""

    pass


# HTTP Exception factories for consistent error responses


def not_found_exception(entity_type: str, entity_id: str) -> HTTPException:
    """Create a 404 Not Found exception."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entity_type} with id '{entity_id}' not found",
    )


def duplicate_exception(entity_type: str, field: str, value: str) -> HTTPException:
    """Create a 409 Conflict exception for duplicates."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{entity_type} with {field} '{value}' already exists",
    )


def unauthorized_exception(message: str = "Invalid credentials") -> HTTPException:
    """Create a 401 Unauthorized exception."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_exception(message: str = "Access forbidden") -> HTTPException:
    """Create a 403 Forbidden exception."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message,
    )


def validation_exception(message: str) -> HTTPException:
    """Create a 422 Validation Error exception."""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=message,
    )


def bad_request_exception(message: str) -> HTTPException:
    """Create a 400 Bad Request exception."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )


def internal_error_exception(message: str = "Internal server error") -> HTTPException:
    """Create a 500 Internal Server Error exception."""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message,
    )
