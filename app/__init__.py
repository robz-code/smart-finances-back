import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from supabase import Client, create_client

from app.config.settings import get_settings
from app.routes import (
    account_route,
    category_route,
    concept_route,
    reporting_route,
    tag_route,
    transaction_route,
    user_route,
)

settings = get_settings()

# Configure logging: DEBUG level when DEBUG=true, INFO otherwise
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="A FastAPI application for smart finances management",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


def _sanitize_validation_errors(errors: list) -> list:
    """Return only JSON-serializable fields from Pydantic errors (ctx may contain exceptions)."""
    return [
        {k: v for k, v in err.items() if k in ("type", "loc", "msg")}
        for err in errors
    ]


@app.exception_handler(ValidationError)
async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Return 422 with a friendly message for Pydantic validation errors."""
    errors = exc.errors()
    detail = "Validation error"
    if errors and isinstance(errors[0].get("msg"), str):
        msg = errors[0]["msg"]
        # Strip "Value error, " prefix for cleaner messages
        detail = (
            msg.replace("Value error, ", "", 1)
            if msg.startswith("Value error, ")
            else msg
        )
    return JSONResponse(
        status_code=422,
        content={"detail": detail, "errors": _sanitize_validation_errors(errors)},
    )


# Initialize Supabase client only when configuration is provided.
# This prevents runtime errors during tests or environments where
# Supabase is not required.
supabase: Optional[Client] = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Include routers
app.include_router(
    user_route.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"]
)
app.include_router(
    account_route.router,
    prefix=f"{settings.API_V1_STR}/accounts",
    tags=["Accounts"],
)
app.include_router(
    category_route.router,
    prefix=f"{settings.API_V1_STR}/categories",
    tags=["Categories"],
)
app.include_router(
    transaction_route.router,
    prefix=f"{settings.API_V1_STR}/transactions",
    tags=["Transactions"],
)
app.include_router(
    concept_route.router,
    prefix=f"{settings.API_V1_STR}/concept",
    tags=["Transaction Concepts"],
)
app.include_router(
    tag_route.router,
    prefix=f"{settings.API_V1_STR}/tags",
    tags=["Tags"],
)
app.include_router(
    reporting_route.router,
    prefix=f"{settings.API_V1_STR}/reporting",
    tags=["Reporting"],
)


# Root endpoint
@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Welcome to Smart Finances API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }
