"""
Application entry point.

This module initializes the FastAPI application, configures middleware,
registers API routes, and serves static frontend content.

The application exposes:
- URL shortening API
- redirect endpoints
- statistics endpoints
- health check
- a simple frontend interface
"""


import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import APP_VERSION
from app.database import engine
from app.models import Base
from app.middleware.rate_limit import RateLimitMiddleware
from app.routes import health, urls


# Configure basic logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready")
    yield
    logger.info("Shutting down")


# Initialize FastAPI application with metadata used in OpenAPI docs
app = FastAPI(
    title="URL Shortener",
    lifespan=lifespan,
    description="A simple and clean URL shortening service",
    version=APP_VERSION,
)


# Register rate limiting middleware to protect selected endpoints
app.add_middleware(RateLimitMiddleware)

# Serve static assets (frontend page)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register API routers for health checks and URL management
app.include_router(health.router)
app.include_router(urls.router)


@app.get("/")
def serve_frontend():
    """
    Serve the main frontend page.

    This endpoint returns a simple static interface that allows
    users to interact with the URL shortener API from a browser.
    """

    return FileResponse("static/index.html")