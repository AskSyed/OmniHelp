"""
FastAPI application entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import os

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.chroma import init_chroma_db
from app.utils.logger import logger as app_logger
from app.services.mcp_client_service import initialize_mcp_client, shutdown_mcp_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
   
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_TRACING_V2"] = settings.LANGSMITH_TRACING_V2
        if settings.LANGSMITH_PROJECT:
            os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
        if settings.LANGSMITH_ENDPOINT:
            os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        app_logger.info("LangSmith tracing enabled")
    else:
        app_logger.info("LangSmith tracing disabled (no API key configured)")
    
    # Startup
    app_logger.info("Initializing RAG Application...")
    
    # Initialize ChromaDB
    try:
        init_chroma_db()
        app_logger.info("ChromaDB initialized successfully")
    except Exception as e:
        app_logger.error(f"Failed to initialize ChromaDB: {e}")
        raise
    
    # Create data directories
    from pathlib import Path
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
    
    # Initialize MCP Client
    if settings.MCP_SERVER_ENABLED:
        try:
            await initialize_mcp_client()
            app_logger.info("MCP client initialized successfully")
        except Exception as e:
            app_logger.error(f"Failed to initialize MCP client: {e}")
            app_logger.warning("MCP functionality will be disabled")
    else:
        app_logger.info("MCP client disabled by configuration")
    
    app_logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    app_logger.info("Shutting down RAG Application...")
    
    # Shutdown MCP Client
    if settings.MCP_SERVER_ENABLED:
        try:
            await shutdown_mcp_client()
            app_logger.info("MCP client shutdown successfully")
        except Exception as e:
            app_logger.error(f"Error shutting down MCP client: {e}")


app = FastAPI(
    title="RAG Application API",
    description="Retrieval-Augmented Generation application with Langgraph, FastAPI, and ChromaDB",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Application API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from app.db.chroma import get_collection_count
        from app.services.mcp_client_service import get_mcp_client
        
        count = get_collection_count()
        
        # Check MCP server connection
        mcp_status = "disabled"
        if settings.MCP_SERVER_ENABLED:
            mcp_client = get_mcp_client()
            mcp_connected = await mcp_client.check_connection()
            mcp_status = "connected" if mcp_connected else "disconnected"
        
        return {
            "status": "healthy",
            "documents": count,
            "mcp_server": mcp_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
