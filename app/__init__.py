from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client, create_client

from app.config.settings import get_settings
from app.routes import (
    account_route,
    category_route,
    tag_route,
    transaction_route,
    user_route,
)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="A FastAPI application for smart finances management",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
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
    tag_route.router,
    prefix=f"{settings.API_V1_STR}/tags",
    tags=["Transaction Tags"],
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
