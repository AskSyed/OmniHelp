"""
Main Orchestrator - Coordinates all agents in a Langgraph workflow
"""
from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from loguru import logger
from app.agents.query_agent import classify_query
from app.agents.retrieval_agent import retrieve_context
from app.agents.generation_agent import generate_answer
from app.agents.refinement_agent import refine_answer


class RAGState(TypedDict):
    """Complete RAG workflow state"""
    # Query phase
    query: str
    intent: Literal["document_search", "metadata_filter", "general"]
    search_strategy: str
    reasoning: str
    filters: dict
    
    # Retrieval phase
    query_embedding: List[float]
    retrieved_chunks: List[Dict[str, Any]]
    context: str
    sources: List[str]
    
    # Generation phase
    generated_answer: str
    
    # Refinement phase
    refined_answer: str
    metadata: Dict[str, Any]
    
    # Final response
    answer: str
    error: str


def create_rag_workflow() -> StateGraph:
    """
    Create the complete RAG workflow using Langgraph
    
    Returns:
        Compiled StateGraph workflow
    """
    workflow = StateGraph(RAGState)
    
    # Add nodes for each agent phase
    workflow.add_node("classify_query", classify_query)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("refine_answer", refine_answer)
    
    # Set entry point
    workflow.set_entry_point("classify_query")
    
    # Define edges - linear flow through all phases
    workflow.add_edge("classify_query", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_answer")
    workflow.add_edge("generate_answer", "refine_answer")
    
    # Finalize response
    workflow.add_node("finalize_response", finalize_response)
    workflow.add_edge("refine_answer", "finalize_response")
    workflow.add_edge("finalize_response", END)
    
    return workflow.compile()


def finalize_response(state: dict) -> dict:
    """
    Finalize the response by setting the final answer
    
    Args:
        state: Current RAG state
        
    Returns:
        Updated state with final answer
    """
    # Use refined answer if available, otherwise generated answer
    state["answer"] = state.get("refined_answer") or state.get("generated_answer", "")
    
    # Ensure sources and metadata are set
    if "sources" not in state:
        state["sources"] = []
    if "metadata" not in state:
        state["metadata"] = {}
    
    logger.info("Response finalized")
    return state


# Create the workflow instance
rag_workflow = create_rag_workflow()


async def process_query(query: str, n_results: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process a query through the complete RAG workflow
    
    Args:
        query: User query string
        n_results: Number of results to retrieve
        filters: Optional metadata filters
        
    Returns:
        Dictionary with answer, sources, and metadata
    """
    try:
        # Initialize state
        initial_state: RAGState = {
            "query": query,
            "intent": "document_search",
            "search_strategy": "",
            "reasoning": "",
            "filters": filters or {},
            "query_embedding": [],
            "retrieved_chunks": [],
            "context": "",
            "sources": [],
            "generated_answer": "",
            "refined_answer": "",
            "metadata": {},
            "answer": "",
            "error": ""
        }
        
        # Run workflow
        result = await rag_workflow.ainvoke(initial_state)
        
        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "retrieved_chunks": result.get("retrieved_chunks", []),
            "metadata": result.get("metadata", {})
        }
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return {
            "answer": "I apologize, but I encountered an error processing your query.",
            "sources": [],
            "retrieved_chunks": [],
            "metadata": {"error": str(e)}
        }
