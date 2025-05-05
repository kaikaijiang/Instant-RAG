from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
from uuid import uuid4

from .database import Base

class RagChunk(Base):
    """
    Model for storing RAG chunks extracted from documents.
    """
    __tablename__ = "rag_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_id = Column(String, nullable=False)  # Unique identifier within a document
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)  # 384 dimensions for BGE-small-en
    page_number = Column(Integer, nullable=True)
    doc_name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # pdf, markdown, image
    images_base64 = Column(JSONB, nullable=True)  # Store base64 encoded images as JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="rag_chunks")
    document = relationship("Document", back_populates="rag_chunks")
    
    def to_dict(self):
        """
        Convert the RAG chunk model to a dictionary for API responses.
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "chunk_text": self.chunk_text,
            "page_number": self.page_number,
            "doc_name": self.doc_name,
            "source_type": self.source_type,
            "created_at": self.created_at.isoformat(),
        }
