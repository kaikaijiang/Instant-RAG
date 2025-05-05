from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import enum
from uuid import uuid4

from .database import Base

class ChatRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"

class ChatMessage(Base):
    """
    Chat message model for storing conversation history.
    """
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    citations = Column(JSON, nullable=True)  # Store document citations as JSON
    images = Column(JSON, nullable=True)  # Store base64 encoded images as JSON array
    
    # Relationships
    project = relationship("Project", back_populates="chat_messages")
    
    def to_dict(self):
        """
        Convert the chat message model to a dictionary for API responses.
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "citations": self.citations,
            "images": self.images,
        }
