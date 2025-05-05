from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from datetime import datetime
from typing import List, Optional

from models.project import Project
from models.document import Document
from services.logging_service import LoggingService

class ProjectService:
    """
    Service for handling project-related operations.
    """
    
    def __init__(self):
        """
        Initialize the project service.
        """
        self.logger = LoggingService()
    
    async def create_project(self, db: AsyncSession, name: str, description: Optional[str] = None, user_id: str = None) -> Project:
        """
        Create a new project.
        
        Args:
            db: Database session
            name: Name of the project
            description: Optional description of the project
            user_id: ID of the user who owns the project
            
        Returns:
            The created project
        """
        project = Project(name=name, description=description, user_id=user_id)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
    
    async def get_project(self, db: AsyncSession, project_id: str, user_id: Optional[str] = None) -> Optional[Project]:
        """
        Get a project by ID, optionally checking if it belongs to a specific user.
        
        Args:
            db: Database session
            project_id: ID of the project
            user_id: Optional ID of the user to check ownership
            
        Returns:
            The project if found and belongs to the user (if user_id provided), None otherwise
        """
        query = select(Project).where(Project.id == project_id)
        
        # Check ownership if user_id is provided
        if user_id:
            query = query.where(Project.user_id == user_id)
            
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_all_projects(self, db: AsyncSession, user_id: Optional[str] = None) -> List[Project]:
        """
        Get all projects, optionally filtered by user_id.
        
        Args:
            db: Database session
            user_id: Optional ID of the user to filter projects by
            
        Returns:
            List of projects
        """
        query = select(Project).order_by(Project.created_at.desc())
        
        # Filter by user_id if provided
        if user_id:
            query = query.where(Project.user_id == user_id)
            
        result = await db.execute(query)
        return result.scalars().all()
    
    async def delete_project(self, db: AsyncSession, project_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a project by ID, optionally checking if it belongs to a specific user.
        
        Args:
            db: Database session
            project_id: ID of the project
            user_id: Optional ID of the user to check ownership
            
        Returns:
            True if the project was deleted, False otherwise
        """
        # Check if project exists and belongs to the user (if user_id provided)
        project = await self.get_project(db, project_id, user_id)
        if not project:
            return False
        
        # Delete the project
        await db.execute(delete(Project).where(Project.id == project_id))
        await db.commit()
        return True
    
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
