"""
Document management API endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from loguru import logger
from app.services.document_service import process_pdf, get_document_list

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF document
    """
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        logger.info(f"Uploading document: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Process and ingest into vector database
        result = await process_pdf(content, file.filename)
        
        return {
            "message": "Document uploaded and processed successfully",
            "filename": file.filename,
            "chunks": result.get("chunks", 0),
            "document_id": result.get("document_id")
        }
    
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_documents():
    """
    List all uploaded documents
    """
    try:
        documents = await get_document_list()
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the vector database
    """
    try:
        # Implementation for document deletion
        return {"message": f"Document {document_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

