"""
Database session management and configuration.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import AsyncGenerator, Generator, Optional
import asyncio
import logging

from config import settings
from db.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for handling connections and sessions."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager."""
        self.database_url = database_url or settings.database_url
        self.engine = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Set up SQLAlchemy engine."""
        connect_args = {}
        
        # SQLite specific configuration
        if self.database_url.startswith("sqlite"):
            connect_args = {
                "check_same_thread": False,
                "poolclass": StaticPool,
            }
        
        self.engine = create_engine(
            self.database_url,
            connect_args=connect_args,
            echo=False,  # Set to True for SQL logging
            pool_pre_ping=True,
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database engine configured for: {self.database_url}")
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_instance(self) -> Session:
        """Get a new database session instance."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()


# Global database manager instance
db_manager = DatabaseManager()


def get_db_session() -> Session:
    """Dependency function to get database session."""
    return db_manager.get_session_instance()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager to get database session."""
    with db_manager.get_session() as session:
        yield session


def init_database():
    """Initialize database - create tables if they don't exist."""
    try:
        db_manager.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def reset_database():
    """Reset database - drop and recreate all tables."""
    try:
        db_manager.drop_tables()
        db_manager.create_tables()
        logger.info("Database reset successfully")
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise


# Database session dependency for dependency injection
def get_db_dependency():
    """Database session dependency for handlers."""
    session = db_manager.get_session_instance()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()