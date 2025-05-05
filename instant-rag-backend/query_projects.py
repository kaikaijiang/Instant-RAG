import asyncio
from init_db import DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

async def query_projects():
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT p.id, p.name, p.description, p.created_at, p.user_id, u.email as user_email
            FROM projects p
            JOIN users u ON p.user_id = u.id
        """))
        projects = [dict(row._mapping) for row in result]
        
        print('Projects in database:')
        print('-' * 80)
        for project in projects:
            print(f"ID: {project['id']}")
            print(f"Name: {project['name']}")
            print(f"Description: {project['description']}")
            print(f"Created At: {project['created_at']}")
            print(f"User ID: {project['user_id']}")
            print(f"User Email: {project['user_email']}")
            print('-' * 80)
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(query_projects())
