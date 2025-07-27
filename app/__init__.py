from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from supabase import create_client, Client
from app.config.database import engine, Base
from app.routes import (
    user_route,
    account_route,
    transaction_route,
    category_route,
    tag_route,
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="A FastAPI application for smart finances management",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

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
app.include_router(user_route.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(account_route.router, prefix=f"{settings.API_V1_STR}/accounts", tags=["Accounts"])
app.include_router(category_route.router, prefix=f"{settings.API_V1_STR}/categories", tags=["Categories"])
app.include_router(transaction_route.router, prefix=f"{settings.API_V1_STR}/transactions", tags=["Transactions"])
app.include_router(tag_route.router, prefix=f"{settings.API_V1_STR}/tags", tags=["Transaction Tags"])


# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "Welcome to Smart Finances API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }