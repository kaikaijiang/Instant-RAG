import asyncio
import sys
import os
from sqlalchemy import text

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db

async def inspect_database():
    """Inspect the database schema."""
    async for db in get_db():
        # Get tables using raw SQL
        result = await db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"Tables in the database: {tables}")
        
        # Inspect the projects table using raw SQL
        if 'projects' in tables:
            result = await db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'projects'"))
            rows = result.fetchall()
            print("\nProjects table schema from information_schema:")
            for row in rows:
                print(f"  {row[0]}: {row[1]}")
        else:
            print("\nProjects table not found!")
        
        # Check if user_id column exists in projects table
        result = await db.execute(text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'user_id'"))
        count = result.scalar()
        if count > 0:
            print("\nuser_id column exists in projects table")
        else:
            print("\nuser_id column DOES NOT exist in projects table")
        
        break  # Only need one session

if __name__ == "__main__":
    asyncio.run(inspect_database())
