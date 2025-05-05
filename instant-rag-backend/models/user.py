from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.orm import relationship
from uuid import uuid4

from .database import Base

class User(Base):
    """
    User model representing a user in the system.
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        """
        Convert the user model to a dictionary for API responses.
        """
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }
