from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
import enum
from uuid import uuid4
from pgvector.sqlalchemy import Vector

from .database import Base

class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class Document(Base):
    """
    Document model representing a file uploaded to a project.
    """
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    content = Column(Text, nullable=True)
    embedding_model = Column(String, nullable=True)
    
    # Vector embedding for the document content
    embedding = Column(Vector(384), nullable=True)  # 384 dimensions for BGE-small-en
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    rag_chunks = relationship("RagChunk", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self):
        """
        Convert the document model to a dictionary for API responses.
        """
        return {
            "id": self.id,
            "name": self.name,
            "size": self.size,
            "type": self.type,
            "project_id": self.project_id,
            "uploaded_at": self.uploaded_at.isoformat(),
            "status": self.status.value,
        }
