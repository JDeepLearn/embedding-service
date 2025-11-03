from fastapi import Request
from fastapi.responses import JSONResponse
from .logging import get_logger

log = get_logger("errors")

async def http_exception_handler(request: Request, exc):
    log.warning("http_error", path=str(request.url), detail=str(exc.detail))
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

async def unhandled_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=str(request.url), error=str(exc))
    return JSONResponse(status_code=500, content={"detail":"Internal server error"})
