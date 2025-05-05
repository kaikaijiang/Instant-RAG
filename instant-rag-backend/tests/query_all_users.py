import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User
from init_db import DATABASE_URL

async def query_users():
    """
    Query all users in the database.
    """
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    # Create async session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Query users
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print('Users in database:')
        print('-' * 50)
        for user in users:
            print(f'ID: {user.id}')
            print(f'Email: {user.email}')
            print(f'Role: {user.role}')
            print(f'Created At: {user.created_at}')
            print('-' * 50)
    
    # Close the engine
    await engine.dispose()

if __name__ == "__main__":
    # Run the query
    asyncio.run(query_users())
