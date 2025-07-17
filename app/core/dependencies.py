"""
FastAPI dependencies for database sessions and other common dependencies
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.core.logging import logger


def get_database_session() -> Generator[Session, None, None]:
    """
    Dependency to get database session with proper error handling
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """
    Alias for get_database_session for backward compatibility
    """
    yield from get_database_session()