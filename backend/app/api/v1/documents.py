"""
Document management API endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from loguru import logger
from app.services.document_service import DocumentService
from app.models.document import DocumentUploadResponse, DocumentInfo

router = APIRouter()
document_service = DocumentService()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF or CSV document
    
    Args:
        file: PDF or CSV file to upload
        
    Returns:
        Document processing results
    """
    try:
        # Validate file type
        filename = file.filename
        if not filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        file_ext = filename.split('.')[-1].lower()
        if file_ext not in ["pdf", "csv"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: PDF, CSV"
            )
        
        # Read file content
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Check file size (50MB default limit)
        from app.core.config import settings
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        logger.info(f"Processing document upload: {filename}")
        
        # Process document
        result = await document_service.process_document(
            content=content,
            filename=filename
        )
        
        return DocumentUploadResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[DocumentInfo])
async def list_documents():
    """
    List all uploaded documents
    
    Returns:
        List of document information
    """
    try:
        documents = document_service.list_documents()
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the vector database
    
    Args:
        document_id: ID of the document to delete
        
    Returns:
        Success message
    """
    try:
        from app.db.chroma import delete_documents
        
        # Delete all chunks for this document
        delete_documents(where={"document_id": document_id})
        
        logger.info(f"Deleted document: {document_id}")
        return {"message": f"Document {document_id} deleted successfully"}
    
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
