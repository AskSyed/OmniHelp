"""
Document parsers for PDF and CSV files
"""
import pandas as pd
from pypdf import PdfReader
from io import BytesIO
from typing import List, Dict
from loguru import logger


def parse_pdf(content: bytes) -> str:
    """
    Parse PDF file and extract text
    
    Args:
        content: PDF file content as bytes
        
    Returns:
        Extracted text from PDF
    """
    try:
        pdf_reader = PdfReader(BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        if not text.strip():
            raise ValueError("No text extracted from PDF")
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text
    
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        raise


def parse_csv(content: bytes) -> List[str]:
    """
    Parse CSV file and convert rows to text chunks
    
    Args:
        content: CSV file content as bytes
        
    Returns:
        List of text chunks, each representing a row with column context
    """
    try:
        df = pd.read_csv(BytesIO(content))
        
        # Convert each row to a text chunk with column names as context
        chunks = []
        for _, row in df.iterrows():
            # Create a text representation: "Column1: value1, Column2: value2, ..."
            row_text = ", ".join([f"{col}: {row[col]}" for col in df.columns])
            chunks.append(row_text)
        
        logger.info(f"Parsed CSV with {len(chunks)} rows")
        return chunks
    
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
        raise


def get_file_type(filename: str) -> str:
    """Get file type from filename"""
    return filename.split('.')[-1].lower()
