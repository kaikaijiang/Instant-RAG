import asyncio
from models.database import get_db
from models.rag_chunk import RagChunk
from sqlalchemy import func
from sqlalchemy.future import select

async def check_chunks():
    # Get database session
    async for db in get_db():
        try:
            # Count total chunks
            result = await db.execute(select(func.count(RagChunk.id)))
            count = result.scalar()
            print(f"Total chunks in database: {count}")
            
            # Show sample chunk data
            result = await db.execute(select(RagChunk).limit(3))
            chunks = result.scalars().all()
            
            for chunk in chunks:
                print("\nChunk ID:", chunk.chunk_id)
                print("Document:", chunk.doc_name)
                print("Source Type:", chunk.source_type)
                print("Page Number:", chunk.page_number)
                print("Text Sample:", chunk.chunk_text[:100] + "..." if len(chunk.chunk_text) > 100 else chunk.chunk_text)
                
            # Show a sample of the embedding vector
            if chunks:
                print("\nEmbedding vector sample (first 5 values):")
                print(chunks[0].embedding[:5])
                
            # Check if images are stored
            if chunks and chunks[0].images_base64:
                print("\nImages are stored as base64 strings")
                
            break
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await db.close()

# Run the async function
asyncio.run(check_chunks())

