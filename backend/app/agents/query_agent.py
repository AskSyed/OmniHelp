"""
Query Agent - Analyzes user queries and extracts intent
"""
import json
import re
from typing import TypedDict, Literal
from langchain_openai import ChatOpenAI
from langsmith import traceable
from loguru import logger
from app.core.config import settings


class QueryState(TypedDict):
    """State for query agent"""
    query: str
    intent: Literal["document_search", "metadata_filter", "general", "order_management"]
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
    1. Intent: Choose from:
       - "order_management": Queries about orders, customers, products, inventory, order status, purchases
       - "document_search": General document search
       - "metadata_filter": Specific document/source queries
       - "general": Conversational queries
    2. Search strategy: How to best retrieve relevant information
    
    Order management keywords: order, purchase, customer, product, inventory, stock, status, tracking, shipping, order ID (e.g., #123)
    
    Query: "{query}"
    
    Respond with JSON format:
    {{
        "intent": "order_management" | "document_search" | "metadata_filter" | "general",
        "search_strategy": "vector_similarity_search" | "mcp_sql_query",
        "reasoning": "why this intent",
        "filters": {{}} or {{"source": "filename"}} if metadata filtering needed
    }}
    """
    
    try:
        response = llm.invoke(classification_prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        logger.debug("classify_query LLM raw response: {}", response_text[:500] if response_text else "(empty)")

        # Parse JSON from LLM response
        # Handle potential markdown code blocks
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response_text.strip()
        logger.debug("classify_query extracted JSON string: {}", json_str[:300] if json_str else "(none)")

        # Parse JSON
        classification_result = json.loads(json_str)
        logger.debug("classify_query parsed result: {}", classification_result)
        
        # Extract values from LLM response
        intent = classification_result.get("intent", "document_search")
        search_strategy = classification_result.get("search_strategy", "vector_similarity_search")
        reasoning = classification_result.get("reasoning", f"Classified as {intent} based on LLM analysis")
        filters = classification_result.get("filters", {})
        
        state["intent"] = intent
        state["search_strategy"] = search_strategy
        state["reasoning"] = reasoning
        state["filters"] = filters
        
        # Simple parsing (in production, use structured output)
        # For now, use keyword-based classification
        '''query_lower = query.lower()
        
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
        state["filters"] = filters'''
        
        logger.info(f"Query classified: {intent}, filters: {filters}")
        
    except Exception as e:
        logger.exception("Error classifying query: %s", e)
        state["intent"] = "document_search"
        state["search_strategy"] = "vector_similarity_search"
        state["reasoning"] = f"Default classification due to error: {str(e)}"
        state["filters"] = {}
    
    return state
