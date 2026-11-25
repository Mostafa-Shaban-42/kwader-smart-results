"""Typed API errors. Never expose stack traces to client."""
from fastapi import HTTPException

class AppError(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str):
        super().__init__(status_code=status_code, detail={"error_code": error_code, "message": message})

def bad_request(error_code: str, message: str) -> AppError:
    return AppError(400, error_code, message)

def unauthorized(error_code: str = "UNAUTHORIZED", message: str = "Unauthorized") -> AppError:
    return AppError(401, error_code, message)

def not_found(error_code: str = "NOT_FOUND", message: str = "Not found") -> AppError:
    return AppError(404, error_code, message)

def forbidden(error_code: str = "FORBIDDEN", message: str = "Forbidden") -> AppError:
    return AppError(403, error_code, message)