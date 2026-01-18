"""
Generation Agent - Generates answers using retrieved context
"""
from typing import TypedDict
from langchain_openai import ChatOpenAI
from loguru import logger
from app.core.config import settings


class GenerationState(TypedDict):
    """State for generation agent"""
    query: str
    context: str
    generated_answer: str
    retrieved_chunks: list


def generate_answer(state: dict) -> dict:
    """
    Generate answer using retrieved context
    
    Args:
        state: Current generation state
        
    Returns:
        Updated state with generated answer
    """
    query = state["query"]
    context = state.get("context", "")
    
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    if not context:
        state["generated_answer"] = "I couldn't find relevant information to answer your question. Please try rephrasing or upload relevant documents."
        return state
    
    prompt = f"""You are a helpful assistant that answers questions based on the provided context from documents.

Context from documents:
{context}

User Question: {query}

Instructions:
- Answer the question based solely on the provided context
- If the context doesn't contain enough information, say so clearly
- Be concise but comprehensive
- Cite specific details from the context when relevant
- If the question cannot be answered from the context, politely explain that

Answer:"""
    
    try:
        response = llm.invoke(prompt)
        answer = response.content if hasattr(response, "content") else str(response)
        state["generated_answer"] = answer
        logger.info("Generated answer from context")
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        state["generated_answer"] = "I apologize, but I encountered an error while generating an answer. Please try again."
    
    return state
