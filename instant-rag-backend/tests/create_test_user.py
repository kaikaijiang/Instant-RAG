import asyncio
import uuid
import sys
import os

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import only what we need
from models.database import get_db
from models.user import User
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

async def create_test_user():
    # Generate a unique email
    email = f"test_{uuid.uuid4()}@example.com"
    password = "password123"
    
    # Get a database session
    db = await anext(get_db())
    
    try:
        # Check if any users exist
        from sqlalchemy import text
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
        # Create the user
        if user_count > 0:
            print(f"Users already exist. Creating a regular test user: {email}")
            role = "user"
        else:
            print(f"No users exist. Creating an admin test user: {email}")
            role = "admin"
            
        # Create the user directly
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"User created successfully:")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Role: {user.role}")
        
    except Exception as e:
        print(f"Error creating user: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())
