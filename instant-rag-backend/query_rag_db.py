#!/usr/bin/env python3
import asyncio
import argparse
from models.database import get_db
from models.rag_chunk import RagChunk
from models.document import Document
from sqlalchemy import func, or_
from sqlalchemy.future import select

async def list_projects(db):
    from models.project import Project
    result = await db.execute(select(Project))
    projects = result.scalars().all()
    
    print(f"\nFound {len(projects)} projects:")
    for project in projects:
        print(f"  - Project ID: {project.id}")
        print(f"    Name: {project.name}")
        print(f"    Description: {project.description}")
        print(f"    Created: {project.created_at}")
        print()

async def list_documents(db, project_id=None):
    query = select(Document)
    if project_id:
        query = query.where(Document.project_id == project_id)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    print(f"\nFound {len(documents)} documents:")
    for doc in documents:
        print(f"  - Document ID: {doc.id}")
        print(f"    Name: {doc.name}")
        print(f"    Type: {doc.type}")
        print(f"    Project ID: {doc.project_id}")
        print(f"    Status: {doc.status}")
        print(f"    Uploaded: {doc.uploaded_at}")
        print()

async def list_chunks(db, project_id=None, document_id=None, limit=10):
    query = select(RagChunk)
    if project_id:
        query = query.where(RagChunk.project_id == project_id)
    if document_id:
        query = query.where(RagChunk.document_id == document_id)
    
    query = query.limit(limit)
    result = await db.execute(query)
    chunks = result.scalars().all()
    
    print(f"\nFound {len(chunks)} chunks (limited to {limit}):")
    for chunk in chunks:
        text_sample = chunk.chunk_text[:100] + "..." if len(chunk.chunk_text) > 100 else chunk.chunk_text
        print(f"  - Chunk ID: {chunk.chunk_id}")
        print(f"    Document: {chunk.doc_name}")
        print(f"    Source Type: {chunk.source_type}")
        print(f"    Page Number: {chunk.page_number}")
        print(f"    Text Sample: {text_sample}")
        print(f"    Embedding Vector Size: {len(chunk.embedding)}")
        print(f"    Has Images: {chunk.images_base64 is not None}")
        print()

async def search_chunks(db, query_text, limit=5):
    # Simple text search
    search_pattern = f"%{query_text}%"
    query = select(RagChunk).where(RagChunk.chunk_text.like(search_pattern)).limit(limit)
    
    result = await db.execute(query)
    chunks = result.scalars().all()
    
    print(f"\nFound {len(chunks)} chunks containing \"{query_text}\":")
    for chunk in chunks:
        print(f"  - Chunk ID: {chunk.chunk_id}")
        print(f"    Document: {chunk.doc_name}")
        print(f"    Text: {chunk.chunk_text}")
        print()

async def main():
    parser = argparse.ArgumentParser(description="Query the Instant-RAG database")
    parser.add_argument("--projects", action="store_true", help="List all projects")
    parser.add_argument("--documents", action="store_true", help="List all documents")
    parser.add_argument("--chunks", action="store_true", help="List chunks")
    parser.add_argument("--search", type=str, help="Search for text in chunks")
    parser.add_argument("--project-id", type=str, help="Filter by project ID")
    parser.add_argument("--document-id", type=str, help="Filter by document ID")
    parser.add_argument("--limit", type=int, default=10, help="Limit the number of results")
    
    args = parser.parse_args()
    
    # Default to listing chunks if no specific action is provided
    if not (args.projects or args.documents or args.chunks or args.search):
        args.chunks = True
    
    async for db in get_db():
        try:
            if args.projects:
                await list_projects(db)
            
            if args.documents:
                await list_documents(db, args.project_id)
            
            if args.chunks:
                await list_chunks(db, args.project_id, args.document_id, args.limit)
            
            if args.search:
                await search_chunks(db, args.search, args.limit)
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(main())

