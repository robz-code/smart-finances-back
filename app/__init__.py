from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.config.database import engine, Base
from app.routes import (
    user_route
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
app.include_router(user_route.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])


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