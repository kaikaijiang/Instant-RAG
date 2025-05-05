from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine
import os
from contextlib import asynccontextmanager

# Database URL from environment variable or default to a local PostgreSQL instance
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/instant_rag")

# Create async engine
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True,
)

# Create async session factory
async_session_factory = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Create declarative base for SQLAlchemy models
Base = declarative_base()

# Dependency for FastAPI
async def get_db():
    """
    Dependency to handle the database session lifecycle.
    Usage:
        @app.get("/")
        async def route(db: AsyncSession = Depends(get_db)):
            # Use db session here
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

async def init_db():
    """
    Initialize the database, creating tables and the pgvector extension.
    """
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
