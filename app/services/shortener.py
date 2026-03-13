"""
Service layer responsible for URL shortening logic.

This module contains the core business logic for:
- generating short codes
- creating shortened URLs
- retrieving URLs by short code
- tracking click statistics
- soft deletion of URLs

The service uses the database unique constraint on `short_code`
to prevent collisions and retries code generation when necessary.
"""

import logging
import random
import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import URL

logger = logging.getLogger(__name__)

# Character set used to generate short codes
ALPHABET = string.ascii_letters + string.digits

# Default length of generated short codes
CODE_LENGTH = 6

# Maximum number of attempts to generate a unique short code
MAX_RETRIES = 10


def generate_short_code(length: int = CODE_LENGTH) -> str:
    """
    Generate a random short code.

    Args:
        length: Length of the generated code.

    Returns:
        Random alphanumeric string used as the shortened URL identifier.
    """
    return "".join(random.choices(ALPHABET, k=length))


def create_short_url(db: Session, original_url: str) -> URL:
    """
    Create a new shortened URL entry.

    This function generates a short code and attempts to insert it into the
    database. If a collision occurs (due to the unique constraint on
    `short_code`), the function retries with a new code.

    Concurrency safety is achieved primarily through the database
    unique constraint, while the retry loop provides a secondary safeguard.

    Args:
        db: SQLAlchemy database session.
        original_url: The original URL to be shortened.

    Returns:
        URL model instance representing the stored shortened URL.

    Raises:
        RuntimeError: If a unique short code cannot be generated
        within the allowed number of retries.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        code = generate_short_code()
        logger.debug("Attempt %d: trying short code '%s'", attempt, code)

        url_entry = URL(original_url=original_url, short_code=code)
        db.add(url_entry)

        try:
            # Flush sends the INSERT to the database without committing,
            # allowing the unique constraint to trigger immediately
            db.flush()

            db.commit()
            db.refresh(url_entry)
            
            logger.info("Created short code '%s' on attempt %d", code, attempt)
            return url_entry

        except IntegrityError:
            # Collision occurred: rollback and try generating another code
            db.rollback()
            logger.warning(
                "Short code collision on '%s' (attempt %d/%d)",
                code,
                attempt,
                MAX_RETRIES,
            )

    raise RuntimeError(
        f"Failed to generate a unique short code after {MAX_RETRIES} attempts"
    )


def get_url_by_code(db: Session, code: str) -> URL | None:
    """
    Retrieve a URL entry by its short code.

    Deleted URLs are excluded using the soft delete flag.

    Args:
        db: SQLAlchemy database session
        code: Short code identifier

    Returns:
        URL instance or None if not found
    """
    return (
        db.query(URL)
        .filter(URL.short_code == code, URL.is_deleted == False)  # noqa: E712
        .first()
    )


def increment_click(db: Session, url: URL) -> URL:
    """
    Increment the click counter for a shortened URL.

    Args:
        db: SQLAlchemy database session
        url: URL model instance

    Returns:
        Updated URL instance
    """
    url.click_count += 1
    db.commit()
    db.refresh(url)
    return url


def soft_delete(db: Session, url: URL) -> URL:
    """
    Perform a soft delete of a shortened URL.

    Instead of removing the record from the database,
    the `is_deleted` flag is set to True.

    Args:
        db: SQLAlchemy database session
        url: URL model instance

    Returns:
        Updated URL instance
    """
    url.is_deleted = True
    db.commit()
    db.refresh(url)
    logger.info("Soft deleted short code '%s'", url.short_code)
    return url