import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


def error_response(status: int, code: str, message: str, headers=None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        headers=headers,
        content={"error": {"code": code, "message": message, "status": status}},
    )


async def http_error(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    code = {404: "not_found", 503: "service_unavailable"}.get(exc.status_code, "http_error")
    message = str(detail)
    if isinstance(detail, dict):
        code = detail.get("code", code)
        message = detail.get("message", "Request failed")
    return error_response(exc.status_code, code, message, exc.headers)


async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = sorted({".".join(str(part) for part in error["loc"]) for error in exc.errors()})
    return error_response(422, "validation_error", "Invalid fields: " + ", ".join(fields))


async def unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled request exception", exc_info=exc)
    return error_response(500, "internal_error", "An unexpected error occurred")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_error)
    app.add_exception_handler(RequestValidationError, validation_error)
    app.add_exception_handler(Exception, unexpected_error)
