from logging import Logger

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .logger import log_json


def install_exception_handlers(app: FastAPI, logger: Logger) -> None:
    """
    Register global exception handlers for the FastAPI app.

    - HTTPException: returns the given status code and message.
    - RequestValidationError: returns 422 with validation details.
    - Exception: returns 500 with a generic error and logs details.

    All responses include a request_id if the middleware has set it.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", None)
        log_json(
            logger,
            "http_error",
            request_id=request_id,
            status_code=exc.status_code,
            detail=str(exc.detail),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "request_id": request_id,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        errors = exc.errors()
        log_json(
            logger,
            "validation_error",
            request_id=request_id,
            errors=errors,
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Request validation failed",
                "details": errors,
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        log_json(
            logger,
            "unhandled_error",
            request_id=request_id,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "Internal server error",
                "request_id": request_id,
            },
        )
