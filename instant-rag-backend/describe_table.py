import asyncio
from init_db import DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

async def describe_table(table_name):
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.connect() as conn:
        result = await conn.execute(text(f"""
            SELECT 
                column_name, 
                data_type, 
                is_nullable
            FROM 
                information_schema.columns
            WHERE 
                table_name = '{table_name}'
            ORDER BY 
                ordinal_position
        """))
        
        columns = [(row[0], row[1], row[2]) for row in result]
        
        print(f'Structure of table "{table_name}":')
        print(f'{"Column":<20} {"Data Type":<30} {"Nullable":<10}')
        print('-' * 60)
        for col_name, data_type, is_nullable in columns:
            print(f'{col_name:<20} {data_type:<30} {is_nullable:<10}')
    
    await engine.dispose()

if __name__ == "__main__":
    # Check the users table
    asyncio.run(describe_table('users'))
