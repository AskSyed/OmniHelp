"""
Main Orchestrator - Coordinates router, RAG, and SQL agents
"""
from typing import TypedDict, Literal
from loguru import logger
from app.agents.router_agent import router_agent
from app.agents.rag_agent import rag_agent
from app.agents.sql_agent import sql_agent


class OrchestratorState(TypedDict):
    """State for orchestrator"""
    query: str
    intent: str
    route_to: Literal["vector_db", "sql_db", "general_llm"]
    answer: str
    sources: list
    error: str


async def route_query(query: str) -> dict:
    """
    Main orchestration function that routes queries to appropriate agents
    """
    try:
        # Step 1: Route query
        router_result = router_agent.invoke({"query": query})
        
        route_to = router_result.get("route_to", "general_llm")
        intent = router_result.get("intent", "unknown")
        
        logger.info(f"Query routed to: {route_to} (intent: {intent})")
        
        # Step 2: Execute appropriate agent
        if route_to == "vector_db":
            # Use RAG agent
            rag_result = rag_agent.invoke({"query": query})
            return {
                "answer": rag_result.get("answer", ""),
                "sources": rag_result.get("sources", []),
                "intent": intent,
                "route_to": route_to
            }
        
        elif route_to == "sql_db":
            # Use SQL agent
            sql_result = await sql_agent.ainvoke({"query": query})
            return {
                "answer": sql_result.get("answer", ""),
                "sources": [],
                "intent": intent,
                "route_to": route_to,
                "sql_results": sql_result.get("results", [])
            }
        
        else:
            # General LLM response
            from langchain_openai import ChatOpenAI
            from app.core.config import settings
            
            llm = ChatOpenAI(model=settings.OPENAI_MODEL)
            response = llm.invoke(f"Answer this question: {query}")
            
            return {
                "answer": response.content if hasattr(response, "content") else str(response),
                "sources": [],
                "intent": intent,
                "route_to": route_to
            }
    
    except Exception as e:
        logger.error(f"Error in orchestrator: {e}")
        return {
            "answer": "I apologize, but I encountered an error processing your request.",
            "sources": [],
            "intent": "unknown",
            "route_to": "error",
            "error": str(e)
        }

