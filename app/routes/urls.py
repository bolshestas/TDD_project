"""
API routes for URL shortening operations.

This module defines HTTP endpoints responsible for:
- creating shortened URLs
- redirecting short codes to their original URLs
- retrieving statistics for shortened URLs

The routes delegate business logic to the service layer
(`app.services.shortener`) to keep API handlers thin and maintainable.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.constants import ERR_CODE_NOT_FOUND
from app.database import get_db
from app.schemas.url import ShortenRequest, ShortenResponse
from app.schemas.stats import StatsResponse
from app.services.shortener import create_short_url, get_url_by_code, increment_click

logger = logging.getLogger(__name__)

# Router for URL-related endpoints
router = APIRouter(tags=["urls"])


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
def shorten_url(payload: ShortenRequest, request: Request, db: Session = Depends(get_db)):
    """
    Create a shortened URL.

    Receives an original URL and generates a short code for it.
    The full short URL is constructed dynamically based on the
    current request's base URL.

    Args:
        payload: Request body containing the original URL
        request: FastAPI request object used to determine base URL
        db: Database session dependency

    Returns:
        ShortenResponse containing the short code and full short URL
    """

    # Delegate creation logic to service layer
    url_entry = create_short_url(db, str(payload.url))

    # Construct full shortened URL using the request base URL
    base_url = str(request.base_url).rstrip("/")
    short_url = f"{base_url}/{url_entry.short_code}"

    logger.info("Created short URL: %s -> %s", short_url, url_entry.original_url)

    return ShortenResponse(
        short_code=url_entry.short_code,
        short_url=short_url,
        original_url=url_entry.original_url,
    )


@router.get("/stats/{code}", response_model=StatsResponse)
def get_stats(code: str, db: Session = Depends(get_db)):
    """
    Retrieve statistics for a shortened URL.

    Args:
        code: Short URL identifier
        db: Database session

    Returns:
        StatsResponse containing usage statistics for the URL

    Raises:
        HTTPException(404): If the short code does not exist
    """

    url_entry = get_url_by_code(db, code)
    if not url_entry:
        raise HTTPException(status_code=404, detail=ERR_CODE_NOT_FOUND.format(code=code))
    return url_entry


@router.get("/{code}")
def redirect_to_url(code: str, db: Session = Depends(get_db)):
    """
    Redirect a short code to its original URL.

    When a valid short code is requested:
    1. The corresponding URL is retrieved
    2. The click counter is incremented
    3. The client is redirected to the original URL

    Args:
        code: Short URL identifier
        db: Database session

    Returns:
        HTTP 302 redirect response to the original URL

    Raises:
        HTTPException(404): If the short code does not exist
    """

    url_entry = get_url_by_code(db, code)
    if not url_entry:
        raise HTTPException(status_code=404, detail=ERR_CODE_NOT_FOUND.format(code=code))

    # Track click before redirecting
    increment_click(db, url_entry)
    logger.info("Redirect: /%s -> %s (clicks: %d)",
                code,
                url_entry.original_url,
                url_entry.click_count
                )

    return RedirectResponse(url=url_entry.original_url, status_code=302)