"""
Document processing service - handles PDF and CSV uploads
"""
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
from app.core.config import settings
from app.utils.parsers import parse_pdf, parse_csv, get_file_type
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.db.chroma import add_documents


class DocumentService:
    """Service for processing and storing documents"""
    
    def __init__(self):
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_document(
        self,
        content: bytes,
        filename: str,
        document_type: Optional[str] = None
    ) -> Dict:
        """
        Process and store a document (PDF or CSV)
        
        Args:
            content: File content as bytes
            filename: Original filename
            document_type: Document type (pdf/csv), auto-detected if None
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Determine document type
            if not document_type:
                document_type = get_file_type(filename)
            
            if document_type not in settings.ALLOWED_EXTENSIONS:
                raise ValueError(f"Unsupported file type: {document_type}")
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Parse document based on type
            if document_type == "pdf":
                text = parse_pdf(content)
                documents = [text]
            elif document_type == "csv":
                documents = parse_csv(content)
            else:
                raise ValueError(f"Unsupported document type: {document_type}")
            
            # Chunk documents
            if document_type == "pdf":
                chunks = self.chunking_service.chunk_text(documents[0])
            else:
                # CSV rows are already chunked
                chunks = documents
            
            # Generate embeddings
            embeddings = self.embedding_service.generate_embeddings(chunks)
            
            # Prepare metadata for each chunk
            metadatas = []
            ids = []
            for i, chunk in enumerate(chunks):
                metadatas.append({
                    "source": filename,
                    "document_id": document_id,
                    "document_type": document_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "upload_date": datetime.now().isoformat()
                })
                ids.append(f"{document_id}_{i}")
            
            # Store in ChromaDB
            add_documents(
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            # Save original file
            file_path = self.upload_dir / f"{document_id}_{filename}"
            file_path.write_bytes(content)
            
            logger.info(
                f"Processed document {filename}: {len(chunks)} chunks, "
                f"document_id: {document_id}"
            )
            
            return {
                "document_id": document_id,
                "filename": filename,
                "document_type": document_type,
                "chunks": len(chunks),
                "file_path": str(file_path)
            }
        
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            raise
    
    def list_documents(self) -> List[Dict]:
        """List all processed documents"""
        # This would typically query a metadata store
        # For now, return empty list - can be enhanced with a metadata database
        return []
