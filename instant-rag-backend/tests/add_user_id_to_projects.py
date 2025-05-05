import asyncio
import sys
import os
from sqlalchemy import text

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db

async def add_user_id_column():
    """Add user_id column to projects table."""
    async for db in get_db():
        try:
            # Check if user_id column exists
            result = await db.execute(text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'user_id'"))
            count = result.scalar()
            
            if count > 0:
                print("user_id column already exists in projects table")
                return
            
            # Add user_id column to projects table
            print("Adding user_id column to projects table...")
            
            # Get the first user's ID to use as default
            result = await db.execute(text("SELECT id FROM users LIMIT 1"))
            user_id = result.scalar()
            
            if not user_id:
                print("No users found in the database. Please create a user first.")
                return
            
            print(f"Using user_id: {user_id}")
            
            # Add the column with a default value
            await db.execute(text(f"ALTER TABLE projects ADD COLUMN user_id VARCHAR REFERENCES users(id)"))
            await db.execute(text(f"UPDATE projects SET user_id = '{user_id}'"))
            await db.execute(text("ALTER TABLE projects ALTER COLUMN user_id SET NOT NULL"))
            
            # Commit the transaction
            await db.commit()
            
            print("user_id column added to projects table successfully")
            
            # Verify the column was added
            result = await db.execute(text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'user_id'"))
            count = result.scalar()
            
            if count > 0:
                print("Verification: user_id column exists in projects table")
            else:
                print("Verification failed: user_id column does not exist in projects table")
            
            break  # Only need one session
        except Exception as e:
            print(f"Error adding user_id column: {e}")
            await db.rollback()
            break

if __name__ == "__main__":
    asyncio.run(add_user_id_column())
