"""
SQL Agent - Handles queries to SQL database for order tracking
"""
from typing import TypedDict, List, Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from loguru import logger
from app.core.config import settings
from app.db.sqlite import get_db_connection


class SQLState(TypedDict):
    """State for SQL agent"""
    query: str
    sql_query: str
    results: List[Dict[str, Any]]
    answer: str
    error: str


def generate_sql_query(state: SQLState) -> SQLState:
    """Generate SQL query from natural language"""
    query = state["query"]
    
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.1
    )
    
    schema_info = """
    Database Schema:
    - orders: id, order_id, customer_id, product_name, product_model, order_date, status, total_amount
    - order_items: id, order_id, item_name, quantity, price
    - customers: id, customer_id, name, email, phone
    """
    
    prompt = f"""
    {schema_info}
    
    Convert the following natural language query to SQL:
    Query: "{query}"
    
    Generate a SQLite-compatible SELECT query. Only return the SQL query, nothing else.
    """
    
    try:
        response = llm.invoke(prompt)
        sql_query = response.content if hasattr(response, "content") else str(response)
        sql_query = sql_query.strip().strip("```sql").strip("```").strip()
        state["sql_query"] = sql_query
        logger.info(f"Generated SQL query: {sql_query}")
    except Exception as e:
        logger.error(f"Error generating SQL query: {e}")
        state["error"] = str(e)
        state["sql_query"] = ""
    
    return state


async def execute_sql_query(state: SQLState) -> SQLState:
    """Execute SQL query and get results"""
    sql_query = state.get("sql_query", "")
    
    if not sql_query:
        state["error"] = "No SQL query generated"
        return state
    
    try:
        async with await get_db_connection() as db:
            db.row_factory = lambda cursor, row: {
                col[0]: row[idx] for idx, col in enumerate(cursor.description)
            }
            cursor = await db.execute(sql_query)
            rows = await cursor.fetchall()
            state["results"] = rows
            logger.info(f"SQL query executed, returned {len(rows)} rows")
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        state["error"] = str(e)
        state["results"] = []
    
    return state


def generate_natural_answer(state: SQLState) -> SQLState:
    """Generate natural language answer from SQL results"""
    query = state["query"]
    results = state.get("results", [])
    error = state.get("error", "")
    
    if error:
        state["answer"] = f"I encountered an error while processing your request: {error}"
        return state
    
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.3
    )
    
    results_text = str(results) if results else "No results found."
    
    prompt = f"""
    The user asked: "{query}"
    
    Database query results: {results_text}
    
    Provide a clear, natural language answer based on these results. Be conversational and helpful.
    """
    
    try:
        response = llm.invoke(prompt)
        state["answer"] = response.content if hasattr(response, "content") else str(response)
        logger.info("Generated natural language answer from SQL results")
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        state["answer"] = f"Here are the results: {results_text}"
    
    return state


def create_sql_graph():
    """Create the SQL agent graph"""
    workflow = StateGraph(SQLState)
    
    # Add nodes
    workflow.add_node("generate_sql_query", generate_sql_query)
    workflow.add_node("execute_sql_query", execute_sql_query)
    workflow.add_node("generate_natural_answer", generate_natural_answer)
    
    # Set entry point
    workflow.set_entry_point("generate_sql_query")
    
    # Add edges
    workflow.add_edge("generate_sql_query", "execute_sql_query")
    workflow.add_edge("execute_sql_query", "generate_natural_answer")
    workflow.add_edge("generate_natural_answer", END)
    
    return workflow.compile()


# Create SQL agent instance
sql_agent = create_sql_graph()
