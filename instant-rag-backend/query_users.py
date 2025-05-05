import asyncio
from init_db import DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

async def query_users():
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, email, role, created_at FROM users"))
        users = [dict(row._mapping) for row in result]
        
        print('Users in database:')
        print('-' * 80)
        for user in users:
            print(f"ID: {user['id']}")
            print(f"Email: {user['email']}")
            print(f"Role: {user['role']}")
            print(f"Created At: {user['created_at']}")
            print('-' * 80)
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(query_users())
