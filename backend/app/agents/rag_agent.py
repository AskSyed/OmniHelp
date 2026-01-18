"""
RAG Agent - Handles retrieval from vector database (ChromaDB)
"""
from typing import TypedDict, List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langgraph.graph import StateGraph, END
from loguru import logger
from app.core.config import settings
from app.db.chroma import get_chroma_collection


class RAGState(TypedDict):
    """State for RAG agent"""
    query: str
    context: List[str]
    answer: str
    sources: List[str]


def retrieve_context(state: RAGState) -> RAGState:
    """Retrieve relevant context from vector database"""
    query = state["query"]
    
    try:
        collection = get_chroma_collection()
        embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Query ChromaDB
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
        
        # Extract documents and metadata
        documents = results.get("documents", [])[0] if results.get("documents") else []
        metadatas = results.get("metadatas", [])[0] if results.get("metadatas") else []
        
        state["context"] = documents
        state["sources"] = [meta.get("source", "unknown") for meta in metadatas]
        
        logger.info(f"Retrieved {len(documents)} documents from vector database")
        
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        state["context"] = []
        state["sources"] = []
    
    return state


def generate_answer(state: RAGState) -> RAGState:
    """Generate answer using retrieved context"""
    query = state["query"]
    context = state.get("context", [])
    
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.3
    )
    
    context_text = "\n\n".join(context) if context else "No relevant context found."
    
    prompt = f"""
    You are a helpful customer support assistant. Answer the user's question based on the provided context from product manuals and documentation.
    
    Context:
    {context_text}
    
    User Question: {query}
    
    Provide a clear, accurate answer based on the context. If the context doesn't contain enough information, say so politely.
    """
    
    try:
        response = llm.invoke(prompt)
        state["answer"] = response.content if hasattr(response, "content") else str(response)
        logger.info("Generated answer from RAG agent")
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        state["answer"] = "I apologize, but I encountered an error while processing your question. Please try again."
    
    return state


def create_rag_graph():
    """Create the RAG agent graph"""
    workflow = StateGraph(RAGState)
    
    # Add nodes
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_answer", generate_answer)
    
    # Set entry point
    workflow.set_entry_point("retrieve_context")
    
    # Add edges
    workflow.add_edge("retrieve_context", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    return workflow.compile()


# Create RAG agent instance
rag_agent = create_rag_graph()

