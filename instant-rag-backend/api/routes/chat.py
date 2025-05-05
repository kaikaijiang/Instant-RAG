from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from models.database import get_db
from api.schemas import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessageList,
    ChatQueryRequest,
    SuccessResponse,
    ErrorResponse
)
from services.chat_service import ChatService
from services.project_service import ProjectService

router = APIRouter()

@router.post("/query", response_model=Dict[str, Any])
async def query_chat(
    query: ChatQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a query to the chat and get a response with citations.
    
    Input:
    - project_id: ID of the project
    - question: User's question
    - top_k: Number of top chunks to retrieve (default: 5)
    
    Output:
    - answer: LLM answer text
    - citations: List of citations with document name, page number, source type, and optional images
    """
    try:
        # Check if project exists
        project_service = ProjectService()
        project = await project_service.get_project(db, query.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {query.project_id} not found"
            )
        
        # Process query
        answer, citations = await ChatService.process_rag_query(
            db=db,
            project_id=query.project_id,
            question=query.question,
            top_k=query.top_k
        )
        
        # Save the chat message
        await ChatService.add_message(
            db=db,
            project_id=query.project_id,
            role="user",
            content=query.question
        )
        
        # Save the assistant's response
        await ChatService.add_message(
            db=db,
            project_id=query.project_id,
            role="assistant",
            content=answer,
            citations=citations
        )
        
        # Return the response
        return {
            "answer": answer,
            "citations": citations
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )

@router.get("/history/{project_id}", response_model=ChatMessageList)
async def get_chat_history(
    project_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat history for a project.
    """
    try:
        # Check if project exists
        project_service = ProjectService()
        project = await project_service.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Get chat history
        messages = await ChatService.get_chat_history(db, project_id, limit)
        
        return {
            "messages": [message.to_dict() for message in messages]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat history: {str(e)}"
        )
