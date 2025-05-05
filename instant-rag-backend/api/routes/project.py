from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import io
import os
import json

from models.database import get_db
from models.user import User
from services.auth_service import AuthService
from api.schemas import (
    ProjectCreate, 
    ProjectResponse, 
    ProjectList, 
    DocumentResponse,
    DocumentList,
    SuccessResponse,
    ErrorResponse,
    DocumentUploadResponse,
    DocumentChunkInfo,
    EmailSettingsCreate,
    EmailIngestResponse,
    EmailSummaryResponse,
    WebContentUploadRequest,
    WebContentUploadResponse
)
from services.project_service import ProjectService
from services.document_service import DocumentService
from services.email_service import EmailService
from services.logging_service import LoggingService

router = APIRouter()
logger = LoggingService()
document_service = DocumentService()
project_service = ProjectService()
email_service = EmailService()

@router.post("/create", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Create a new project.
    """
    try:
        project = await project_service.create_project(
            db, 
            project_data.name, 
            project_data.description,
            user_id=current_user.id
        )
        return project.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.delete("/{project_id}", response_model=SuccessResponse)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Delete a project by ID. Only the owner can delete a project.
    """
    try:
        success = await project_service.delete_project(db, project_id, user_id=current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        return {
            "success": True,
            "message": f"Project with ID {project_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

@router.get("/list", response_model=ProjectList)
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get a list of all projects belonging to the current user.
    """
    try:
        projects = await project_service.get_all_projects(db, user_id=current_user.id)
        return {
            "projects": [project.to_dict() for project in projects]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )

@router.get("/documents/{project_id}", response_model=DocumentList)
async def get_project_documents(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get all documents for a project. Only the owner can access a project's documents.
    """
    try:
        # Check if project exists and belongs to the current user
        project = await project_service.get_project(db, project_id, user_id=current_user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        documents = await document_service.get_project_documents(db, project_id)
        return {
            "documents": [doc.to_dict() for doc in documents]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project documents: {str(e)}"
        )

@router.post("/upload_docs", response_model=DocumentUploadResponse)
async def upload_documents(
    project_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Upload documents to a project, process them, and create RAG chunks.
    Only the owner can upload documents to a project.
    
    This endpoint:
    1. Accepts multiple files (PDF, Markdown, or image files) via multipart/form-data
    2. Accepts a project_id in the request
    3. For each file:
       - If PDF: Extracts text per page and embedded images
       - If image: Optionally performs OCR and stores as base64
       - If Markdown: Reads as plain text
    4. Creates text chunks for each page or logical section
    5. Embeds the text using BAAI/bge-small-en
    6. Stores the chunks in the rag_chunks table
    7. Returns a summary of the processing
    """
    logger.info(f"Uploading documents to project {project_id}")
    
    try:
        # Check if project exists and belongs to the current user
        project = await project_service.get_project(db, project_id, user_id=current_user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Process each file
        documents_processed = []
        total_chunks = 0
        
        for file in files:
            try:
                logger.info(f"Processing file: {file.filename}")
                
                # Get the file size
                file_size = 0
                content = await file.read()
                file_size = len(content)
                
                # Reset file position for future reads
                await file.seek(0)
                
                # Save and process document
                document, processing_results = await document_service.save_document(
                    db=db,
                    project_id=project_id,
                    file_name=file.filename,
                    file_size=file_size,
                    file_type=file.content_type,
                    file_content=file
                )
                
                # Add processing results to the response
                documents_processed.extend(processing_results)
                
                # Update total chunks count
                for result in processing_results:
                    total_chunks += result["chunks_created"]
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                # Continue with the next file
                continue
        
        if not documents_processed:
            return {
                "success": True,
                "message": f"No documents were successfully processed for project {project_id}",
                "documents_processed": [],
                "total_chunks": 0
            }
        
        return {
            "success": True,
            "message": f"Successfully processed {len(documents_processed)} documents for project {project_id}",
            "documents_processed": [
                DocumentChunkInfo(
                    document_name=doc["document_name"],
                    document_type=doc["document_type"],
                    pages_processed=doc["pages_processed"],
                    chunks_created=doc["chunks_created"]
                ) for doc in documents_processed
            ],
            "total_chunks": total_chunks
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload documents: {str(e)}"
        )

@router.post("/setup_email", response_model=SuccessResponse)
async def setup_email(
    email_settings: EmailSettingsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Set up email settings for a project. Only the owner can set up email for a project.
    
    This endpoint:
    1. Accepts email configuration including IMAP server, credentials, and filters
    2. Securely stores the configuration (with encrypted password)
    3. Returns success status
    """
    logger.info(f"Setting up email for project {email_settings.project_id}")
    
    try:
        # Check if project exists and belongs to the current user
        project = await project_service.get_project(db, email_settings.project_id, user_id=current_user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {email_settings.project_id} not found"
            )
        
        # Save email settings
        await email_service.save_email_settings(
            db=db,
            project_id=email_settings.project_id,
            imap_server=email_settings.imap_server,
            email_address=email_settings.email,
            password=email_settings.password,
            sender_filter=email_settings.sender_filter,
            subject_keywords=email_settings.subject_keywords,
            start_date=email_settings.date_range.start if email_settings.date_range else None,
            end_date=email_settings.date_range.end if email_settings.date_range else None
        )
        
        return {
            "success": True,
            "message": f"Successfully set up email for project {email_settings.project_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set up email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set up email: {str(e)}"
        )

@router.post("/ingest_emails", response_model=EmailIngestResponse)
async def ingest_emails(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Ingest emails for a project based on the configured settings.
    Only the owner can ingest emails for a project.
    
    This endpoint:
    1. Retrieves the IMAP configuration for the project
    2. Connects to the mailbox and applies filters
    3. Fetches matched emails (limited to 50)
    4. Extracts email metadata and content
    5. Stores emails for later processing
    6. Returns count and subjects of fetched emails
    """
    logger.info(f"Ingesting emails for project {project_id}")
    
    try:
        # Check if project exists and belongs to the current user
        project = await project_service.get_project(db, project_id, user_id=current_user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Check if email settings exist
        email_settings = await email_service.get_email_settings(db, project_id)
        if not email_settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No email settings found for project {project_id}"
            )
        
        # Fetch emails
        emails = await email_service.fetch_emails(db, project_id)
        
        return {
            "success": True,
            "message": f"Successfully ingested {len(emails)} emails for project {project_id}",
            "count": len(emails),
            "subjects": [email["subject"] for email in emails]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ingest emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest emails: {str(e)}"
        )

@router.post("/upload_web", response_model=WebContentUploadResponse)
async def upload_web_content(
    web_content: WebContentUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Upload web content to a project, process it, and create RAG chunks.
    Only the owner can upload web content to a project.
    
    This endpoint:
    1. Accepts a URL and project_id
    2. Downloads the web page content using httpx
    3. Parses and cleans the HTML using BeautifulSoup
    4. Takes a screenshot of the web page
    5. Chunks the extracted text
    6. Embeds each chunk using the BGE-small-en model
    7. Stores the chunks in the rag_chunks table
    8. Returns a summary of the processing
    """
    logger.info(f"Uploading web content from URL {web_content.url} to project {web_content.project_id}")
    
    try:
        # Check if project exists and belongs to the current user
        project = await project_service.get_project(db, web_content.project_id, user_id=current_user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {web_content.project_id} not found"
            )
        
        # Process the web content
        document, title, chunks_created = await document_service.save_web_content(
            db=db,
            project_id=web_content.project_id,
            url=str(web_content.url),
            with_screenshot=web_content.with_screenshot
        )
        
        return {
            "status": "success",
            "url": str(web_content.url),
            "title": title,
            "chunks_created": chunks_created
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload web content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload web content: {str(e)}"
        )

@router.post("/summarize_emails", response_model=EmailSummaryResponse)
async def summarize_emails(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Summarize ingested emails for a project using Gemini API.
    Only the owner can summarize emails for a project.
    
    This endpoint:
    1. Loads raw email texts from previous ingestion
    2. For each email, calls Google Gemini Flash 2.0 API to generate a summary
    3. Embeds each summary using the local BGE-small-en model
    4. Stores summaries as RAG chunks with source_type='email'
    5. Returns count and list of generated summaries
    """
    logger.info(f"Summarizing emails for project {project_id}")
    
    try:
        # Check if project exists and belongs to the current user
        project = await project_service.get_project(db, project_id, user_id=current_user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Check if email settings exist
        email_settings = await email_service.get_email_settings(db, project_id)
        if not email_settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No email settings found for project {project_id}"
            )
        
        # Call the email service to summarize emails
        summaries = await email_service.summarize_emails(db, project_id)
        
        return {
            "success": True,
            "message": f"Successfully summarized {len(summaries)} emails for project {project_id}",
            "count": len(summaries),
            "summaries": summaries
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to summarize emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize emails: {str(e)}"
        )
