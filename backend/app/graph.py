"""
LangGraph Studio server file - exposes the RAG workflow graph
"""
from app.agents.orchestrator import rag_workflow, RAGState

# Expose the graph for LangGraph Studio
graph = rag_workflow

# Expose the state schema
State = RAGState