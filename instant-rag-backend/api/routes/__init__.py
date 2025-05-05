from .project import router as project_router
from .email import router as email_router
from .chat import router as chat_router
from .auth import router as auth_router

__all__ = [
    "project_router",
    "email_router",
    "chat_router",
    "auth_router",
]
