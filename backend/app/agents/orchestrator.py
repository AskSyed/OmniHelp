"""
Main Orchestrator - Coordinates all agents in a Langgraph workflow
"""
from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langsmith import traceable
from loguru import logger
from app.core.observability import tracer
from app.agents.query_agent import classify_query
from app.agents.retrieval_agent import retrieve_context
from app.agents.sql_agent import execute_sql_query
from app.agents.generation_agent import generate_answer
from app.agents.refinement_agent import refine_answer


class RAGState(TypedDict):
    """Complete RAG workflow state"""
    # Query phase
    query: str
    intent: Literal["document_search", "metadata_filter", "general", "order_management"]
    search_strategy: str
    reasoning: str
    filters: dict
    
    # Retrieval phase (for document search)
    query_embedding: List[float]
    retrieved_chunks: List[Dict[str, Any]]
    context: str
    sources: List[str]
    
    # SQL Agent phase (for order management)
    sql_query: str
    sql_results: List[Dict]
    formatted_context: str
    
    # Generation phase
    generated_answer: str
    
    # Refinement phase
    refined_answer: str
    metadata: Dict[str, Any]
    
    # Final response
    answer: str
    error: str


def route_query(state: dict) -> str:
    """
    Route query based on intent
    
    Args:
        state: Current state with intent
        
    Returns:
        Next node name
    """
    intent = state.get("intent", "document_search")
    
    if intent == "order_management":
        logger.info("Routing to SQL agent for order management")
        return "execute_sql"
    else:
        logger.info("Routing to retrieval agent for document search")
        return "retrieve_context"


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
    workflow.add_node("execute_sql", execute_sql_query)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("refine_answer", refine_answer)
    
    # Set entry point
    workflow.set_entry_point("classify_query")
    
    # Add conditional routing after query classification
    workflow.add_conditional_edges(
        "classify_query",
        route_query,
        {
            "retrieve_context": "retrieve_context",
            "execute_sql": "execute_sql"
        }
    )
    
    # Both paths converge at generation
    workflow.add_edge("retrieve_context", "generate_answer")
    workflow.add_edge("execute_sql", "generate_answer")
    workflow.add_edge("generate_answer", "refine_answer")
    
    # Finalize response
    workflow.add_node("finalize_response", finalize_response)
    workflow.add_edge("refine_answer", "finalize_response")
    workflow.add_edge("finalize_response", END)
    
    return workflow.compile()


@traceable(name="finalize_response")
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


def build_initial_state(query: str, filters: Dict[str, Any] = None) -> RAGState:
    """Build an empty workflow state for a query"""
    return {
        "query": query,
        "intent": "document_search",
        "search_strategy": "",
        "reasoning": "",
        "filters": filters or {},
        "query_embedding": [],
        "retrieved_chunks": [],
        "context": "",
        "sources": [],
        "sql_query": "",
        "sql_results": [],
        "formatted_context": "",
        "generated_answer": "",
        "refined_answer": "",
        "metadata": {},
        "answer": "",
        "error": ""
    }


@traceable(name="process_query")
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
        initial_state = build_initial_state(query, filters)

        # Run workflow
        with tracer.start_as_current_span("rag.workflow") as span:
            result = await rag_workflow.ainvoke(initial_state)
            span.set_attribute("rag.intent", result.get("intent", ""))
            span.set_attribute("rag.sources_count", len(result.get("sources", [])))

        metadata = {**result.get("metadata", {}), "intent": result.get("intent")}
        if result.get("error"):
            metadata["error"] = result["error"]

        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "retrieved_chunks": result.get("retrieved_chunks", []),
            "metadata": metadata
        }
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return {
            "answer": "I apologize, but I encountered an error processing your query.",
            "sources": [],
            "retrieved_chunks": [],
            "metadata": {"error": str(e)}
        }
