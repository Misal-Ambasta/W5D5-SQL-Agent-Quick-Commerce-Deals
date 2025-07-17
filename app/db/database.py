"""
Database configuration and connection management for Quick Commerce Deals platform.
This module provides backward compatibility by importing from the new core.database module.
"""

# Import everything from the new database module for backward compatibility
from app.core.database import (
    base_engine as engine,
    SessionLocal,
    Base,
    get_db,
    get_monitored_db_session,
    db_monitor,
    db_health_checker
)

from sqlalchemy import MetaData

# Metadata for schema operations
metadata = MetaData()


def create_tables():
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Drop all tables in the database.
    """
    Base.metadata.drop_all(bind=engine)