from sqlalchemy import Column, String, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4

from .database import Base

class Project(Base):
    """
    Project model representing a RAG project in the system.
    """
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    rag_chunks = relationship("RagChunk", back_populates="project", cascade="all, delete-orphan")
    email_settings = relationship("EmailSettings", back_populates="project", uselist=False, cascade="all, delete-orphan")
    email_summaries = relationship("EmailSummary", back_populates="project", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="project", cascade="all, delete-orphan")
    
    def to_dict(self):
        """
        Convert the project model to a dictionary for API responses.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
        }
