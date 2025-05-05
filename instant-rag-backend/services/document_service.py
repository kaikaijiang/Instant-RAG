from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, insert
from datetime import datetime
from typing import List, Optional, BinaryIO, Dict, Any, Tuple, Union
from fastapi import UploadFile
import os
import aiofiles
import json
import io
import time
from uuid import uuid4
import numpy as np
import tiktoken
import httpx

from models.document import Document, DocumentStatus
from models.rag_chunk import RagChunk
from services.embedding_service import EmbeddingService
from services.document_processor import DocumentProcessor
from services.logging_service import LoggingService

# Directory to store uploaded documents
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Tokenizer for counting tokens
tokenizer = tiktoken.get_encoding("cl100k_base")

class DocumentService:
    """
    Service for handling document-related operations.
    """
    
    def __init__(self):
        """
        Initialize the document service.
        """
        self.embedding_service = EmbeddingService()
        self.document_processor = DocumentProcessor()
        self.logger = LoggingService()
    
    async def save_web_content(
        self,
        db: AsyncSession,
        project_id: str,
        url: str,
        with_screenshot: bool = True
    ) -> Tuple[Document, str, int]:
        """
        Save web content to the database, process it, and create RAG chunks.
        
        Args:
            db: Database session
            project_id: ID of the project
            url: URL of the web page
            with_screenshot: Whether to take a screenshot of the web page
            
        Returns:
            A tuple containing:
                - The created document
                - The title of the web page
                - The number of chunks created
        """
        self.logger.info(f"Saving web content from URL: {url} for project {project_id}")
        
        # Create document record
        document = Document(
            name=url,
            size=0,  # We don't know the size yet
            type="text/html",
            project_id=project_id,
            uploaded_at=datetime.now(),
            status=DocumentStatus.PENDING
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Update document status to processing
        await self.update_document_status(db, document.id, DocumentStatus.PROCESSING)
        
        try:
            # Process the web content
            processing_results = await self.process_web_content(db, document, url, with_screenshot)
            
            # Update document status to completed
            await self.update_document_status(db, document.id, DocumentStatus.COMPLETED)
            
            return document, processing_results[0], processing_results[1]
        except Exception as e:
            self.logger.error(f"Error processing web content from URL {url}: {str(e)}")
            
            # Update document status to error
            await self.update_document_status(db, document.id, DocumentStatus.ERROR)
            
            # Re-raise the exception
            raise
    
    async def process_web_content(
        self,
        db: AsyncSession,
        document: Document,
        url: str,
        with_screenshot: bool = True
    ) -> Tuple[str, int]:
        """
        Process web content by downloading, cleaning, and creating RAG chunks.
        
        Args:
            db: Database session
            document: The document to process
            url: URL of the web page
            with_screenshot: Whether to take a screenshot of the web page
            
        Returns:
            A tuple containing:
                - The title of the web page
                - The number of chunks created
        """
        start_time = time.time()
        
        # Log the start of web content processing
        self.logger.info(f"Processing web content from URL: {url} for project {document.project_id}")
        
        try:
            # Process the web content to extract text and optionally take screenshot
            chunks, title, chunks_count = await self.document_processor.process_web_content(url, with_screenshot)
            
            if not chunks:
                self.logger.warning(f"No chunks extracted from web content at URL {url}")
                return title, 0
            
            # Calculate average tokens per chunk for monitoring
            total_tokens = 0
            for chunk in chunks:
                total_tokens += len(tokenizer.encode(chunk["chunk_text"]))
            avg_tokens_per_chunk = total_tokens / len(chunks) if chunks else 0
            
            # Start embedding generation time measurement
            embedding_start_time = time.time()
            
            # Separate regular chunks from image chunks
            regular_chunks = [chunk for chunk in chunks if not chunk.get("is_image_chunk", False)]
            image_chunks = [chunk for chunk in chunks if chunk.get("is_image_chunk", False)]
            
            # Generate embeddings only for regular chunks in batch
            chunk_texts = [chunk["chunk_text"] for chunk in regular_chunks]
            embeddings = await self.embedding_service.generate_embeddings(chunk_texts)
            
            # Normalize embeddings
            normalized_embeddings = [
                self._normalize_embedding(embedding) for embedding in embeddings
            ]
            
            # Log embedding generation metrics
            embedding_time_ms = int((time.time() - embedding_start_time) * 1000)
            self.logger.embedding_generation_metrics(
                num_chunks=len(chunks),
                processing_time_ms=embedding_time_ms,
                avg_tokens_per_chunk=avg_tokens_per_chunk
            )
            
            # Use a transaction to ensure all chunks are created atomically
            async with db.begin():
                # Create RAG chunks for regular chunks in the database
                for i, chunk in enumerate(regular_chunks):
                    # Regular chunks don't store images
                    images_json = None
                    
                    # Create RAG chunk
                    rag_chunk = RagChunk(
                        project_id=document.project_id,
                        document_id=document.id,
                        chunk_id=chunk["chunk_id"],
                        chunk_text=chunk["chunk_text"],
                        embedding=normalized_embeddings[i],
                        page_number=chunk["page_number"],
                        doc_name=chunk["doc_name"],  # Use the web page title as the document name
                        source_type=chunk["source_type"],
                        images_base64=images_json
                    )
                    
                    db.add(rag_chunk)
                
                # Create RAG chunks for image chunks in the database
                for chunk in image_chunks:
                    # Convert images to JSON
                    images_json = json.dumps(chunk["images"]) if chunk["images"] else None
                    
                    # Create RAG chunk for image chunk (no embedding)
                    rag_chunk = RagChunk(
                        project_id=document.project_id,
                        document_id=document.id,
                        chunk_id=chunk["chunk_id"],
                        chunk_text=chunk["chunk_text"],
                        embedding=None,  # No embedding for image chunks
                        page_number=chunk["page_number"],
                        doc_name=chunk["doc_name"],  # Use the web page title as the document name
                        source_type=chunk["source_type"],
                        images_base64=images_json
                    )
                    
                    db.add(rag_chunk)
            
            # Calculate total processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Log the completion of web content processing
            self.logger.info(
                f"Processed web content from URL: {url} - {len(chunks)} chunks, "
                f"processing time: {processing_time_ms}ms"
            )
            
            # Update the document name to the web page title
            await db.execute(
                update(Document)
                .where(Document.id == document.id)
                .values(name=title)
            )
            await db.commit()
            
            return title, len(chunks)
        except Exception as e:
            self.logger.error(f"Error processing web content from URL {url}: {str(e)}")
            # Re-raise the exception to be handled by the caller
            raise
    
    async def save_document(
        self,
        db: AsyncSession, 
        project_id: str, 
        file_name: str, 
        file_size: int, 
        file_type: str, 
        file_content: Union[BinaryIO, UploadFile]
    ) -> Tuple[Document, List[Dict[str, Any]]]:
        """
        Save a document to the database and file system, process it, and create RAG chunks.
        
        Args:
            db: Database session
            project_id: ID of the project
            file_name: Name of the file
            file_size: Size of the file in bytes
            file_type: MIME type of the file
            file_content: File content as a binary stream
            
        Returns:
            A tuple containing:
                - The created document
                - A list of processing results for each document
        """
        self.logger.info(f"Saving document: {file_name} for project {project_id}")
        
        # Create document record
        document = Document(
            name=file_name,
            size=file_size,
            type=file_type,
            project_id=project_id,
            uploaded_at=datetime.now(),
            status=DocumentStatus.PENDING
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Create directory for project if it doesn't exist
        project_dir = os.path.join(UPLOAD_DIR, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Save file to disk
        file_path = os.path.join(project_dir, f"{document.id}_{file_name}")
        
        # Create a copy of the file content for processing
        content = await file_content.read()
        
        # Save the original file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # Create a BytesIO object for processing
        if isinstance(file_content, io.BytesIO):
            # If it's already a BytesIO, we need to get the bytes
            file_content_copy = content
        else:
            # Otherwise, use the content directly
            file_content_copy = content
        
        # Update document status to processing
        await self.update_document_status(db, document.id, DocumentStatus.PROCESSING)
        
        try:
            # Process the document
            processing_results = await self.process_document(db, document, file_content_copy)
            
            # Update document status to completed
            await self.update_document_status(db, document.id, DocumentStatus.COMPLETED)
            
            return document, processing_results
        except Exception as e:
            self.logger.error(f"Error processing document {file_name}: {str(e)}")
            
            # Update document status to error
            await self.update_document_status(db, document.id, DocumentStatus.ERROR)
            
            # Re-raise the exception
            raise
    
    async def get_document(self, db: AsyncSession, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            db: Database session
            document_id: ID of the document
            
        Returns:
            The document if found, None otherwise
        """
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalars().first()
    
    async def get_project_documents(self, db: AsyncSession, project_id: str) -> List[Document]:
        """
        Get all documents for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            List of documents for the project
        """
        result = await db.execute(
            select(Document)
            .where(Document.project_id == project_id)
            .order_by(Document.uploaded_at.desc())
        )
        return result.scalars().all()
    
    async def update_document_status(self, db: AsyncSession, document_id: str, status: DocumentStatus) -> bool:
        """
        Update the status of a document.
        
        Args:
            db: Database session
            document_id: ID of the document
            status: New status
            
        Returns:
            True if the document was updated, False otherwise
        """
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status=status)
        )
        await db.commit()
        return True
    
    async def process_document(
        self, 
        db: AsyncSession, 
        document: Document, 
        file_content: bytes
    ) -> List[Dict[str, Any]]:
        """
        Process a document by extracting text, generating embeddings, and creating RAG chunks.
        
        Args:
            db: Database session
            document: The document to process
            file_content: The file content as a binary stream
            
        Returns:
            A list of processing results for each document
        """
        start_time = time.time()
        
        # Log the start of document processing
        self.logger.document_processing_start(
            document_name=document.name,
            project_id=document.project_id,
            file_type=document.type
        )
        
        try:
            # Process the document to extract text and images
            chunks, pages_processed = self.document_processor.process_file(
                file_content=file_content,
                file_name=document.name,
                file_type=document.type
            )
            
            if not chunks:
                self.logger.warning(f"No chunks extracted from document {document.name}")
                return []
            
            # Calculate average tokens per chunk for monitoring
            total_tokens = 0
            for chunk in chunks:
                total_tokens += len(tokenizer.encode(chunk["chunk_text"]))
            avg_tokens_per_chunk = total_tokens / len(chunks) if chunks else 0
            
            # Start embedding generation time measurement
            embedding_start_time = time.time()
            
            # Separate regular chunks from image chunks
            regular_chunks = [chunk for chunk in chunks if not chunk.get("is_image_chunk", False)]
            image_chunks = [chunk for chunk in chunks if chunk.get("is_image_chunk", False)]
            
            # Generate embeddings only for regular chunks in batch
            chunk_texts = [chunk["chunk_text"] for chunk in regular_chunks]
            embeddings = await self.embedding_service.generate_embeddings(chunk_texts)
            
            # Normalize embeddings
            normalized_embeddings = [
                self._normalize_embedding(embedding) for embedding in embeddings
            ]
            
            # Log embedding generation metrics
            embedding_time_ms = int((time.time() - embedding_start_time) * 1000)
            self.logger.embedding_generation_metrics(
                num_chunks=len(chunks),
                processing_time_ms=embedding_time_ms,
                avg_tokens_per_chunk=avg_tokens_per_chunk
            )
            
            # Use a transaction to ensure all chunks are created atomically
            async with db.begin():
                # Create RAG chunks for regular chunks in the database
                for i, chunk in enumerate(regular_chunks):
                    # Regular chunks don't store images
                    images_json = None
                    
                    # Create RAG chunk
                    rag_chunk = RagChunk(
                        project_id=document.project_id,
                        document_id=document.id,
                        chunk_id=chunk["chunk_id"],
                        chunk_text=chunk["chunk_text"],
                        embedding=normalized_embeddings[i],
                        page_number=chunk["page_number"],
                        doc_name=chunk["doc_name"],
                        source_type=chunk["source_type"],
                        images_base64=images_json
                    )
                    
                    db.add(rag_chunk)
                
                # Create RAG chunks for image chunks in the database
                for chunk in image_chunks:
                    # Convert images to JSON
                    images_json = json.dumps(chunk["images"]) if chunk["images"] else None
                    
                    # Create RAG chunk for image chunk (no embedding)
                    rag_chunk = RagChunk(
                        project_id=document.project_id,
                        document_id=document.id,
                        chunk_id=chunk["chunk_id"],
                        chunk_text=chunk["chunk_text"],
                        embedding=None,  # No embedding for image chunks
                        page_number=chunk["page_number"],
                        doc_name=chunk["doc_name"],
                        source_type=chunk["source_type"],
                        images_base64=images_json
                    )
                    
                    db.add(rag_chunk)
            
            # Calculate total processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Log the completion of document processing
            self.logger.document_processing_complete(
                document_name=document.name,
                project_id=document.project_id,
                chunks_created=len(chunks),
                pages_processed=pages_processed,
                processing_time_ms=processing_time_ms
            )
            
            # Return processing results
            return [{
                "document_name": document.name,
                "document_type": chunks[0]["source_type"],
                "pages_processed": pages_processed,
                "chunks_created": len(chunks)
            }]
        except Exception as e:
            self.logger.error(f"Error processing document {document.name}: {str(e)}")
            # Re-raise the exception to be handled by the caller
            raise
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize an embedding vector to unit length.
        
        Args:
            embedding: The embedding vector to normalize
            
        Returns:
            The normalized embedding vector
        """
        # Convert to numpy array
        embedding_np = np.array(embedding)
        
        # Calculate the L2 norm
        norm = np.linalg.norm(embedding_np)
        
        # Normalize the embedding
        if norm > 0:
            normalized = embedding_np / norm
        else:
            normalized = embedding_np
        
        # Convert back to list
        return normalized.tolist()
    
    async def get_document_chunks(
        self, 
        db: AsyncSession, 
        document_id: str
    ) -> List[RagChunk]:
        """
        Get all RAG chunks for a document.
        
        Args:
            db: Database session
            document_id: ID of the document
            
        Returns:
            List of RAG chunks for the document
        """
        result = await db.execute(
            select(RagChunk)
            .where(RagChunk.document_id == document_id)
            .order_by(RagChunk.page_number, RagChunk.id)
        )
        return result.scalars().all()
    
    async def get_project_chunks(
        self, 
        db: AsyncSession, 
        project_id: str
    ) -> List[RagChunk]:
        """
        Get all RAG chunks for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            List of RAG chunks for the project
        """
        result = await db.execute(
            select(RagChunk)
            .where(RagChunk.project_id == project_id)
            .order_by(RagChunk.doc_name, RagChunk.page_number, RagChunk.id)
        )
        return result.scalars().all()
