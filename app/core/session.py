from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

# Create the async engine
# Note: we disable echo in production, but keep it on for debug.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Create an async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get an async database session.
    """
    async with AsyncSessionLocal() as session:
        yield session
