"""Common exception classes and handlers."""

from fastapi import Request
from fastapi.responses import JSONResponse


class AlfitException(Exception):
    """Base exception for Alfit services."""
    
    def __init__(self, message: str, status_code: int = 500, detail: str | None = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class NotFoundException(AlfitException):
    """Resource not found."""
    
    def __init__(self, resource: str, resource_id: str | int):
        super().__init__(
            message=f"{resource} with ID {resource_id} not found",
            status_code=404,
        )


class UnauthorizedException(AlfitException):
    """Unauthorized access."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(AlfitException):
    """Forbidden access."""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message=message, status_code=403)


class ConflictException(AlfitException):
    """Resource conflict."""
    
    def __init__(self, message: str):
        super().__init__(message=message, status_code=409)


class ValidationException(AlfitException):
    """Validation error."""
    
    def __init__(self, message: str):
        super().__init__(message=message, status_code=422)


async def alfit_exception_handler(request: Request, exc: AlfitException):
    """Handle AlfitException globally."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "detail": exc.detail,
        },
    )
