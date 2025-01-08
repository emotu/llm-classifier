"""
__init__.py

@author: Emotu Balogun
@created: December 1, 2024

Database initialization and session management for the FastAPI application.

This module handles database connection setup, session management, and initialization
of SQLModel-based database models. It provides async database operations using SQLAlchemy
and SQLModel with PostgreSQL.

Key Features:
    - Async database engine configuration
    - Session management and dependency injection
    - Database initialization and table creation
    - SQLModel integration for type-safe database operations

Usage:
    The module exposes key database functions and objects:
    - get_session: Async session generator for dependency injection
    - init_db: Database initialization function
    - async_engine: Configured async SQLAlchemy engine

Example:
    >>> from app.db import get_session
    >>> async with get_session() as session:
    ...     result = await session.execute(query)

:module: app.db
:requires: sqlalchemy, sqlmodel, asyncpg
"""

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

from . import assets as assets

# DATABASE_URL = URL.create(
#     "postgresql+asyncpg",
#     username=settings.DB_USER,
#     password=settings.DB_PASS,
#     host=None,
#     database=settings.DB_NAME,
#     query={"host": settings.INSTANCE_UNIX_SOCKET},
# )

DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@/{settings.DB_NAME}?host={settings.DB_CONNECTION_NAME}"

async_engine = create_async_engine(DATABASE_URL, echo=settings.DB_ECHO)


async def get_session() -> AsyncSession:  # type: ignore
    """
    Asynchronous database session generator for dependency injection.

    Creates and yields an async database session using SQLModel and SQLAlchemy.
    The session is automatically closed when the generator exits.

    Yields:
        AsyncSession: An async SQLAlchemy session for database operations

    Example:
        >>> async def get_user(session: AsyncSession = Depends(get_session)):
        ...     result = await session.execute(select(User))
        ...     return result.first()
    """
    async_session = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


async def init_db():
    """
    Initialize the database by creating all tables defined in SQLModel metadata.

    This asynchronous function creates all database tables based on the SQLModel
    definitions in the application. It should be called during application startup
    or when setting up a new database instance.

    Note:
        This function will create tables only if they don't already exist.
        It will not modify existing tables or data.

    Example:
        >>> from app.db import init_db
        >>> await init_db()
    """
    async with async_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


async def drop_db():
    """
    Drop all database tables defined in SQLModel metadata.

    This asynchronous function drops all database tables based on the SQLModel
    definitions in the application. It should be used with caution as it will
    permanently delete all data in the tables.

    Note:
        This is a destructive operation that cannot be undone.
        All data in the database tables will be lost.

    Example:
        >>> from app.db import drop_db
        >>> await drop_db()
    """
    async with async_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.drop_all)


async def create_session() -> AsyncSession:
    """
    Creates and returns a new database session without dependency injection.

    Returns:
        AsyncSession: An async SQLAlchemy session for database operations
    """
    async_session = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )()  # Note: We call the sessionmaker immediately here
    return async_session
