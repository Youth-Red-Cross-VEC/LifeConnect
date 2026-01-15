from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)


class Database:
    """
    Async database connection manager with connection pooling.
    
    Optimized for high concurrency with:
    - Connection pooling (default 20 connections)
    - Overflow handling (10 extra during spikes)
    - Connection health checks (pre_ping)
    - Automatic connection recycling
    """

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        echo: bool = False,
    ):
        # Convert sync PostgreSQL URL to async (postgresql:// → postgresql+asyncpg://)
        if database_url.startswith("postgresql://"):
            async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("postgres://"):
            async_url = database_url.replace("postgres://", "postgresql+asyncpg://")
        else:
            async_url = database_url

        self.engine = create_async_engine(
            async_url,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,  # Verify connection health before use
            echo=echo,
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        logger.info(
            f"Database initialized with pool_size={pool_size}, max_overflow={max_overflow}"
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions.
        
        Automatically handles:
        - Session creation
        - Commit on success
        - Rollback on exception
        - Session cleanup
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async generator for FastAPI dependency injection.
        Use with Depends() in route handlers.
        """
        async with self.session() as session:
            yield session

    async def close(self) -> None:
        """Close the database engine and all connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")


# Global database instance (initialized in app startup)
db: Database | None = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Usage:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db)):
            ...
    """
    if db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with db.session() as session:
        yield session


def init_db(
    database_url: str,
    pool_size: int = 20,
    max_overflow: int = 10,
    pool_timeout: int = 30,
    pool_recycle: int = 1800,
) -> Database:
    """Initialize the global database instance."""
    global db
    db = Database(
        database_url=database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
    )
    return db
