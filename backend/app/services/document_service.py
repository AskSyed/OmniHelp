"""
Document processing service
"""
import uuid
from typing import List, Dict
from loguru import logger
from pypdf import PdfReader
from io import BytesIO
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.db.chroma import get_chroma_collection


async def process_pdf(content: bytes, filename: str) -> Dict:
    """
    Process PDF file and ingest into vector database
    """
    try:
        # Read PDF
        pdf_reader = PdfReader(BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        if not text.strip():
            raise ValueError("No text extracted from PDF")
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        
        # Generate embeddings and store in ChromaDB
        collection = get_chroma_collection()
        document_id = str(uuid.uuid4())
        
        embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Generate embeddings for chunks
        chunk_embeddings = embeddings.embed_documents(chunks)
        
        # Prepare data for ChromaDB
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": filename,
                "document_id": document_id,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            for i in range(len(chunks))
        ]
        
        # Add to ChromaDB
        collection.add(
            ids=ids,
            embeddings=chunk_embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        logger.info(f"Processed {len(chunks)} chunks from {filename}")
        
        return {
            "document_id": document_id,
            "chunks": len(chunks),
            "filename": filename
        }
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise


async def get_document_list() -> List[Dict]:
    """
    Get list of all documents in the vector database
    """
    try:
        collection = get_chroma_collection()
        # Get all documents (this is a simplified version)
        # In production, you'd want to track documents separately
        return []
    except Exception as e:
        logger.error(f"Error getting document list: {e}")
        return []

