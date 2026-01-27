"""
Query Agent - Analyzes user queries and extracts intent
"""
from typing import TypedDict, Literal
from langchain_openai import ChatOpenAI
from loguru import logger
from app.core.config import settings
from langsmith import traceable


class QueryState(TypedDict):
    """State for query agent"""
    query: str
    intent: Literal["document_search", "metadata_filter", "general"]
    search_strategy: str
    reasoning: str
    filters: dict

@traceable(name="classify_query")
def classify_query(state: dict) -> dict:
    """
    Classify query intent and determine search strategy
    
    Args:
        state: Current query state
        
    Returns:
        Updated state with intent and strategy
    """
    query = state["query"]
    
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.1,
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    classification_prompt = f"""
    Analyze the following user query and determine:
    1. Intent: "document_search" (general document search), "metadata_filter" (specific document/source), or "general" (conversational)
    2. Search strategy: How to best retrieve relevant information
    
    Query: "{query}"
    
    Respond with JSON format:
    {{
        "intent": "document_search" | "metadata_filter" | "general",
        "search_strategy": "brief description",
        "reasoning": "why this intent",
        "filters": {{}} or {{"source": "filename"}} if metadata filtering needed
    }}
    """
    
    try:
        response = llm.invoke(classification_prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        
        # Simple parsing (in production, use structured output)
        # For now, use keyword-based classification
        query_lower = query.lower()
        
        # Check for metadata filter keywords
        if any(keyword in query_lower for keyword in ["from", "in document", "in file", "source"]):
            intent = "metadata_filter"
            # Try to extract source filename
            filters = {}
            # Simple extraction - can be enhanced
            if "from" in query_lower:
                parts = query_lower.split("from")
                if len(parts) > 1:
                    potential_source = parts[1].strip().split()[0]
                    filters["source"] = potential_source
        else:
            intent = "document_search"
            filters = {}
        
        state["intent"] = intent
        state["search_strategy"] = "vector_similarity_search"
        state["reasoning"] = f"Classified as {intent} based on query analysis"
        state["filters"] = filters
        
        logger.info(f"Query classified: {intent}, filters: {filters}")
        
    except Exception as e:
        logger.error(f"Error classifying query: {e}")
        state["intent"] = "document_search"
        state["search_strategy"] = "vector_similarity_search"
        state["reasoning"] = f"Default classification due to error: {str(e)}"
        state["filters"] = {}
    
    return state
