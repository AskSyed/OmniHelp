"""
Refinement Agent - Refines and validates generated answers
"""
from typing import TypedDict
from langchain_openai import ChatOpenAI
from loguru import logger
from langsmith import traceable
from app.core.config import settings


class RefinementState(TypedDict):
    """State for refinement agent"""
    query: str
    context: str
    generated_answer: str
    refined_answer: str
    sources: list
    metadata: dict


@traceable(name="refine_answer")
def refine_answer(state: dict) -> dict:
    """
    Refine and validate the generated answer
    
    Args:
        state: Current refinement state
        
    Returns:
        Updated state with refined answer
    """
    query = state["query"]
    generated_answer = state.get("generated_answer", "")
    context = state.get("context", "")
    sources = state.get("sources", [])
    
    if not generated_answer:
        state["refined_answer"] = "I couldn't generate an answer. Please try again."
        state["metadata"] = {"refined": False}
        return state
    
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.2,  # Lower temperature for refinement
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    refinement_prompt = f"""Review and refine the following answer to ensure it:
1. Directly addresses the user's question
2. Is clear and well-structured
3. Accurately reflects the provided context
4. Includes source information when relevant

User Question: {query}

Original Answer:
{generated_answer}

Context Used:
{context[:500]}...

Please provide the refined answer. If the original answer is already good, you can return it as-is or make minor improvements.

Refined Answer:"""
    
    try:
        response = llm.invoke(refinement_prompt)
        refined = response.content if hasattr(response, "content") else str(response)
        
        # If refinement is similar to original, keep original
        # Simple check - in production, use similarity metrics
        if len(refined) < len(generated_answer) * 0.5:
            # Refinement seems too short, keep original
            refined = generated_answer
        
        state["refined_answer"] = refined
        
        # Add metadata
        state["metadata"] = {
            "refined": True,
            "sources_count": len(sources),
            "sources": sources,
            "context_length": len(context)
        }
        
        logger.info("Refined answer generated")
        
    except Exception as e:
        logger.error(f"Error refining answer: {e}")
        # Fallback to original answer
        state["refined_answer"] = generated_answer
        state["metadata"] = {"refined": False, "error": str(e)}
    
    return state
