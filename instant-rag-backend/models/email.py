from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from uuid import uuid4

from .database import Base

class EmailSettings(Base):
    """
    Email settings model for configuring email ingestion for a project.
    """
    __tablename__ = "email_settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    imap_server = Column(String, nullable=False)
    email_address = Column(String, nullable=False)
    password = Column(String, nullable=False)  # Encrypted password
    password_salt = Column(String, nullable=False)  # Salt used for password encryption
    sender_filter = Column(String, nullable=True)
    subject_keywords = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="email_settings")
    
    def to_dict(self):
        """
        Convert the email settings model to a dictionary for API responses.
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "imap_server": self.imap_server,
            "email_address": self.email_address,
            "sender_filter": self.sender_filter,
            "subject_keywords": self.subject_keywords,
            "start_date": self.start_date,
            "end_date": self.end_date,
            # Don't include password in API responses
        }

class EmailSummary(Base):
    """
    Email summary model for storing summarized email content.
    """
    __tablename__ = "email_summaries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="email_summaries")
    
    def to_dict(self):
        """
        Convert the email summary model to a dictionary for API responses.
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "summary": self.summary,
            "timestamp": self.timestamp.isoformat(),
        }
