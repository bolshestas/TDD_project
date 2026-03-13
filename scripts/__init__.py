"""
Database initialisation script.

Usage:
    python -m scripts.init_db

Run this once before starting the application for the first time,
or after adding new models. In production, prefer Alembic migrations.
"""

import logging
import sys

from sqlalchemy import inspect

from app.database import engine
from app.models import Base

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def init_db() -> None:
    try:
        logger.info("Connecting to database at: %s", engine.url)
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info("Database initialised. Tables: %s", tables)
    except Exception as exc:
        logger.error("Failed to initialise database: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    init_db()