"""
Tests for service layer
"""
import pytest
from app.services.chunking_service import ChunkingService
from app.utils.parsers import parse_csv, get_file_type


def test_chunking_service():
    """Test text chunking"""
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    text = "This is a test document. " * 10
    chunks = service.chunk_text(text)
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_get_file_type():
    """Test file type detection"""
    assert get_file_type("document.pdf") == "pdf"
    assert get_file_type("data.csv") == "csv"
    assert get_file_type("file.txt") == "txt"
