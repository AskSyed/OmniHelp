"""
Router Agent - Classifies user intent and routes to appropriate data source
"""
from typing import TypedDict, Literal
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from loguru import logger
from app.core.config import settings


class RouterState(TypedDict):
    """State for router agent"""
    query: str
    intent: Literal["policy_document", "order_tracking", "general", "unknown"]
    confidence: float
    reasoning: str
    route_to: Literal["vector_db", "sql_db", "general_llm"]


def classify_intent(state: RouterState) -> RouterState:
    """
    Classify user intent using LLM
    Routes to:
    - vector_db: For policy documents, product manuals, FAQs
    - sql_db: For order tracking, customer queries, transactional data
    - general_llm: For general questions
    """
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.1
    )
    
    query = state["query"]
    
    classification_prompt = f"""
    Analyze the following customer query and classify the intent.
    
    Query: "{query}"
    
    Classify into one of these categories:
    1. "policy_document" - Questions about product manuals, policies, documentation, how-to guides
    2. "order_tracking" - Questions about orders, order status, order history, customer orders
    3. "general" - General questions that don't fit the above categories
    
    Respond in JSON format:
    {{
        "intent": "one of the categories above",
        "confidence": 0.0-1.0,
        "reasoning": "brief explanation",
        "route_to": "vector_db" or "sql_db" or "general_llm"
    }}
    """
    
    try:
        response = llm.invoke(classification_prompt)
        # Parse response (simplified - in production, use structured output)
        # For now, we'll use a simple keyword-based approach
        query_lower = query.lower()
        
        # Order tracking keywords
        order_keywords = ["order", "track", "status", "delivery", "shipment", "purchase", "transaction"]
        if any(keyword in query_lower for keyword in order_keywords):
            intent = "order_tracking"
            route_to = "sql_db"
            confidence = 0.8
            reasoning = "Query contains order-related keywords"
        
        # Policy/document keywords
        elif any(keyword in query_lower for keyword in ["manual", "document", "policy", "how to", "guide", "instruction"]):
            intent = "policy_document"
            route_to = "vector_db"
            confidence = 0.8
            reasoning = "Query appears to be about documentation or manuals"
        
        else:
            intent = "general"
            route_to = "general_llm"
            confidence = 0.6
            reasoning = "General query, no specific intent detected"
        
        state["intent"] = intent
        state["confidence"] = confidence
        state["reasoning"] = reasoning
        state["route_to"] = route_to
        
        logger.info(f"Intent classified: {intent} -> {route_to} (confidence: {confidence})")
        
    except Exception as e:
        logger.error(f"Error classifying intent: {e}")
        state["intent"] = "unknown"
        state["confidence"] = 0.0
        state["reasoning"] = f"Error: {str(e)}"
        state["route_to"] = "general_llm"
    
    return state


def create_router_graph():
    """Create the router agent graph"""
    workflow = StateGraph(RouterState)
    
    # Add nodes
    workflow.add_node("classify_intent", classify_intent)
    
    # Set entry point
    workflow.set_entry_point("classify_intent")
    
    # Add edges
    workflow.add_edge("classify_intent", END)
    
    return workflow.compile()


# Create router agent instance
router_agent = create_router_graph()

