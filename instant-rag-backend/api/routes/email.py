from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from models.database import get_db
from api.schemas import (
    EmailSettingsCreate,
    EmailSettingsResponse,
    EmailSummaryResponse,
    EmailSummaryList,
    SuccessResponse,
    ErrorResponse
)
from services.email_service import EmailService
from services.project_service import ProjectService

router = APIRouter()

@router.post("/setup_email", response_model=EmailSettingsResponse)
async def setup_email(
    project_id: str,
    settings: EmailSettingsCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Set up email settings for a project.
    """
    try:
        # Check if project exists
        project = await ProjectService.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Save email settings
        email_settings = await EmailService.save_email_settings(
            db=db,
            project_id=project_id,
            imap_server=settings.imapServer,
            email_address=settings.emailAddress,
            password=settings.password,
            sender_filter=settings.senderFilter,
            subject_keywords=settings.subjectKeywords,
            start_date=settings.startDate,
            end_date=settings.endDate
        )
        
        return email_settings.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set up email: {str(e)}"
        )

@router.post("/ingest_emails", response_model=SuccessResponse)
async def ingest_emails(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest emails for a project.
    """
    try:
        # Check if project exists
        project = await ProjectService.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Check if email settings exist
        email_settings = await EmailService.get_email_settings(db, project_id)
        if not email_settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No email settings found for project {project_id}"
            )
        
        # Fetch emails
        emails = await EmailService.fetch_emails(db, project_id)
        
        return {
            "success": True,
            "message": f"Successfully ingested {len(emails)} emails for project {project_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest emails: {str(e)}"
        )

@router.post("/summarize_emails", response_model=EmailSummaryResponse)
async def summarize_emails(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Summarize emails for a project.
    """
    try:
        # Check if project exists
        project = await ProjectService.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Check if email settings exist
        email_settings = await EmailService.get_email_settings(db, project_id)
        if not email_settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No email settings found for project {project_id}"
            )
        
        # Summarize emails
        summaries = await EmailService.summarize_emails(db, project_id)
        
        # Format the response according to EmailSummaryResponse schema
        return {
            "success": True,
            "message": f"Successfully summarized {len(summaries)} emails for project {project_id}",
            "count": len(summaries),
            "summaries": summaries
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize emails: {str(e)}"
        )

@router.get("/summaries/{project_id}", response_model=EmailSummaryList)
async def get_email_summaries(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all email summaries for a project.
    """
    try:
        # Check if project exists
        project = await ProjectService.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Get email summaries
        summaries = await EmailService.get_email_summaries(db, project_id)
        
        return {
            "summaries": [summary.to_dict() for summary in summaries]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email summaries: {str(e)}"
        )
