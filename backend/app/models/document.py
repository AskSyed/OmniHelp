"""
Document data models
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    document_id: str
    filename: str
    document_type: str
    chunks: int
    file_path: str


class DocumentInfo(BaseModel):
    """Document information model"""
    document_id: str
    filename: str
    document_type: str
    chunks: int
    upload_date: Optional[datetime] = None
