import asyncio
from init_db import DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

async def list_tables():
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        tables = [row[0] for row in result]
        
        print('Tables in database:')
        for table in sorted(tables):
            print(f'- {table}')
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(list_tables())
