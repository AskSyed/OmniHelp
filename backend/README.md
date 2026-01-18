# Omni-Help Backend

FastAPI backend for the Omni-Help intelligent customer support platform.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. Run the server:
   ```bash
   python main.py
   ```

## Project Structure

- `app/agents/`: LangGraph agent workflows
- `app/api/`: FastAPI route handlers
- `app/core/`: Configuration and settings
- `app/db/`: Database utilities (SQLite, ChromaDB)
- `app/models/`: Pydantic data models
- `app/services/`: Business logic layer
- `app/utils/`: Utility functions

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

