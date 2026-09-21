import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware, RequestGuardMiddleware, error_payload
from app.db.database import init_database


configure_logging()
logger = logging.getLogger("finsight.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Grounded financial intelligence API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.add_middleware(RequestGuardMiddleware, settings=settings)
app.add_middleware(RequestContextMiddleware)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, exc.message, exc.retryable, _request_id(request)),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_payload(
            "INVALID_REQUEST",
            "The request did not match the expected format.",
            False,
            _request_id(request),
        ),
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("request.failed")
    return JSONResponse(
        status_code=500,
        content=error_payload(
            "INTERNAL_ERROR",
            "An unexpected error occurred.",
            False,
            _request_id(request),
        ),
    )

app.include_router(api_router, prefix="/api/v1")

# Temporary compatibility aliases. They remain hidden from Swagger and can be
# removed after all consumers have migrated to /api/v1.
app.include_router(api_router, include_in_schema=False, deprecated=True)
