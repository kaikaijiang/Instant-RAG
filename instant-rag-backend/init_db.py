import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

from models.database import Base
from models.project import Project
from models.document import Document, DocumentStatus
from models.email import EmailSettings, EmailSummary
from models.chat import ChatMessage, ChatRole
from models.rag_chunk import RagChunk
from models.user import User

# Load environment variables
load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/instant_rag")

async def init_db():
    """
    Initialize the database by creating all tables and the pgvector extension.
    """
    # Create async engine
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
    )
    
    async with engine.begin() as conn:
        # Create pgvector extension if it doesn't exist
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Drop all tables if they exist (for clean initialization)
        # Use CASCADE to handle dependencies
        await conn.execute(text("DROP TABLE IF EXISTS rag_chunks CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS chat_messages CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS email_summaries CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS email_settings CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS projects CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Close the engine
    await engine.dispose()
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    # Run the initialization
    asyncio.run(init_db())
