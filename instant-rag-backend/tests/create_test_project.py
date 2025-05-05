import asyncio
import sys
import os
from sqlalchemy import text

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from services.project_service import ProjectService

async def create_test_project():
    """Create a test project."""
    project_service = ProjectService()
    
    async for db in get_db():
        try:
            # Get the first user's ID to use as the owner
            result = await db.execute(text("SELECT id FROM users LIMIT 1"))
            user_id = result.scalar()
            
            if not user_id:
                print("No users found in the database. Please create a user first.")
                return
            
            print(f"Using user_id: {user_id}")
            
            # Create a test project
            project = await project_service.create_project(
                db=db,
                name="Test Project",
                description="This is a test project",
                user_id=user_id
            )
            
            print(f"Project created successfully: {project.to_dict()}")
            
            break  # Only need one session
        except Exception as e:
            print(f"Error creating test project: {e}")
            await db.rollback()
            break

if __name__ == "__main__":
    asyncio.run(create_test_project())
