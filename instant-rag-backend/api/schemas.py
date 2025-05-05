from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid

# Authentication schemas
class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password", min_length=8)

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class UserResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    email: EmailStr = Field(..., description="User email address")
    role: str = Field(..., description="User role (admin or user)")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")

# Project schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project")

class ProjectResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the project")
    name: str = Field(..., description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True

class ProjectList(BaseModel):
    projects: List[ProjectResponse]

# Document schemas
class DocumentResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the document")
    name: str = Field(..., description="Name of the document")
    size: int = Field(..., description="Size of the document in bytes")
    type: str = Field(..., description="MIME type of the document")
    project_id: str = Field(..., description="ID of the project this document belongs to")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    status: str = Field(..., description="Processing status of the document")

    class Config:
        from_attributes = True

class DocumentList(BaseModel):
    documents: List[DocumentResponse]

# Date range schema for email filtering
class DateRange(BaseModel):
    start: str = Field(..., description="Start date in ISO format")
    end: Optional[str] = Field(None, description="End date in ISO format")

# Email schemas
class EmailSettingsCreate(BaseModel):
    project_id: str = Field(..., description="ID of the project")
    imap_server: str = Field(..., description="IMAP server address")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Email password")
    sender_filter: Optional[str] = Field(None, description="Filter emails by sender")
    subject_keywords: Optional[List[str]] = Field(None, description="Filter emails by subject keywords")
    date_range: Optional[DateRange] = Field(None, description="Date range for filtering emails")

class EmailSettingsResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the email settings")
    project_id: str = Field(..., description="ID of the project these settings belong to")
    imap_server: str = Field(..., description="IMAP server address")
    email_address: str = Field(..., description="Email address")
    sender_filter: Optional[str] = Field(None, description="Filter emails by sender")
    subject_keywords: Optional[str] = Field(None, description="Filter emails by subject keywords")
    start_date: Optional[str] = Field(None, description="Start date for email range")
    end_date: Optional[str] = Field(None, description="End date for email range")

    class Config:
        from_attributes = True

class EmailSummary(BaseModel):
    id: str = Field(..., description="Unique identifier for the email summary")
    subject: str = Field(..., description="Email subject")
    summary: str = Field(..., description="Summary text")

class EmailIngestResponse(BaseModel):
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    count: int = Field(..., description="Number of emails ingested")
    subjects: List[str] = Field(..., description="List of email subjects")

class EmailSummaryResponse(BaseModel):
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    count: int = Field(..., description="Number of emails summarized")
    summaries: List[EmailSummary] = Field(..., description="List of email summaries")

class EmailSummaryList(BaseModel):
    summaries: List[EmailSummary]

# Chat schemas
class Citation(BaseModel):
    doc_name: str = Field(..., description="Name of the cited document")
    page_number: Optional[int] = Field(None, description="Page number in the document")
    source_type: str = Field(..., description="Type of the source (pdf, markdown, image, email)")
    images_base64: Optional[List[str]] = Field(None, description="Base64 encoded images")

class ChatMessageCreate(BaseModel):
    content: str = Field(..., description="Message content")

class ChatQueryRequest(BaseModel):
    project_id: str = Field(..., description="ID of the project")
    question: str = Field(..., description="User's question")
    top_k: int = Field(5, description="Number of top chunks to retrieve")

class ChatMessageResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the message")
    project_id: str = Field(..., description="ID of the project this message belongs to")
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    citations: Optional[List[Citation]] = Field(None, description="Document citations")
    images: Optional[List[str]] = Field(None, description="Base64 encoded images")

    class Config:
        from_attributes = True

class ChatMessageList(BaseModel):
    messages: List[ChatMessageResponse]

# Document upload response schemas
class DocumentChunkInfo(BaseModel):
    document_name: str = Field(..., description="Name of the document")
    document_type: str = Field(..., description="Type of the document (pdf, markdown, image)")
    pages_processed: int = Field(..., description="Number of pages processed")
    chunks_created: int = Field(..., description="Number of chunks created")

class DocumentUploadResponse(BaseModel):
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    documents_processed: List[DocumentChunkInfo] = Field(..., description="Information about processed documents")
    total_chunks: int = Field(..., description="Total number of chunks created")

# Web content upload schema
class WebContentUploadRequest(BaseModel):
    project_id: str = Field(..., description="ID of the project")
    url: HttpUrl = Field(..., description="URL of the web page to upload")
    with_screenshot: bool = Field(True, description="Whether to take a screenshot of the web page")

class WebContentUploadResponse(BaseModel):
    status: str = Field("success", description="Status of the operation")
    url: str = Field(..., description="URL of the web page")
    title: str = Field(..., description="Title of the web page")
    chunks_created: int = Field(..., description="Number of chunks created")

# Generic response schemas
class SuccessResponse(BaseModel):
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")

class ErrorResponse(BaseModel):
    success: bool = Field(False, description="Operation success status")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
