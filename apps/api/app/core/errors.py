"""
Standardized Error Handling & Exception Types
Implements RFC 7807 problem details specification.
"""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone
from app.core.logging import logger


class FraudLensException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class DatabaseConnectionError(FraudLensException):
    def __init__(self, message: str = "Database connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_UNAVAILABLE",
            details=details,
        )


class GraphDatabaseError(FraudLensException):
    def __init__(self, message: str = "Neo4j graph database error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="NEO4J_UNAVAILABLE",
            details=details,
        )


class EntityNotFoundError(FraudLensException):
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            message=f"{entity_type} with ID '{entity_id}' was not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ENTITY_NOT_FOUND",
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class AuthenticationFailedError(FraudLensException):
    def __init__(self, message: str = "Authentication or signature verification failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED",
            details=details,
        )


class ValidationFailedError(FraudLensException):
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_FAILED",
            details=details,
        )


async def fraudlens_exception_handler(request: Request, exc: FraudLensException) -> JSONResponse:
    logger.error(f"FraudLens error: [{exc.error_code}] {exc.message} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://fraudlens.io/errors/{exc.error_code.lower()}",
            "title": exc.error_code,
            "status": exc.status_code,
            "detail": exc.message,
            "instance": str(request.url.path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": exc.details,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://fraudlens.io/errors/validation_error",
            "title": "VALIDATION_ERROR",
            "status": 422,
            "detail": "Request payload or parameter validation failed",
            "instance": str(request.url.path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "errors": exc.errors(),
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://fraudlens.io/errors/internal_error",
            "title": "INTERNAL_SERVER_ERROR",
            "status": 500,
            "detail": "An unexpected server error occurred.",
            "instance": str(request.url.path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
