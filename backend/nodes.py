
import re
import json
import sqlparse
from typing import Annotated, TypedDict, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.message import AnyMessage, add_messages
from backend.config import llm
from backend.database import get_schema, db_query_tool
from langgraph.graph import END

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def query_gen_node(state: State):
    """Generate SQL query from natural language question."""
    schema = get_schema()
    system_prompt = f"""You are a SQL expert.
Database schema:
{schema}

⚠️ STRICT RULES:
1. Use only SQLite syntax.
2. DO NOT invent new functions. (No INSTR() unless correct args.)
3. Do not use SQLite string functions like INSTR() or LIKE unless the user explicitly asks for pattern matching.

4. For negative amounts: use "column < 0" (preferred).
   If column is TEXT, use "CAST(column AS REAL) < 0" or "column LIKE '-%'".
5. Every query MUST be executable without errors.
6. SELECT only. Never modify data.
7. LIMIT results to 50 unless user requests more.
8. If the question is ambiguous, ask a clarifying question instead of guessing.
9. Wrap final SQL in:
```sqlite
SELECT ...

"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])
    query_gen = prompt | llm
    message = query_gen.invoke(state)
    return {"messages": [message]}

def query_validation_node(state: State):
    """Validate and correct the SQL query before execution."""
    last_msg = state["messages"][-1]
    match = re.search(r"```sqlite\s+(.*?)```", last_msg.content, re.DOTALL)
    if not match:
        return {"messages": [AIMessage(content="Error: No SQL query found in LLM response.")]}
    sql_query = match.group(1).strip()
    schema = get_schema()

    system_prompt = f"""You are a SQL validator.
Database schema:
{schema}

Check SQL:
{sql_query}

Rules:
- Fix invalid column/table names.
- Disallow INSERT/UPDATE/DELETE/DROP.
- Return only corrected SQL in ```sqlite ...``` fences.
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Validate and correct the SQL query if needed.")
    ])
    checked = (prompt | llm).invoke(state)
    return {"messages": [checked]}

def execute_query_gen(state: State):
    """Extract SQL from checked response and run it."""
    last_msg = state["messages"][-1]
    match = re.search(r"```sqlite\s+(.*?)```", last_msg.content, re.DOTALL)
    if not match:
        return {"messages": [AIMessage(content="Error: No SQL query found in LLM response.")]}
    sql_query = match.group(1).strip()
    formatted_sql = sqlparse.format(sql_query, reindent=True, keyword_case="upper")
    result = db_query_tool(sql_query)
    return {"messages": [AIMessage(content=json.dumps({"sql": formatted_sql, "result": result}, indent=2))]}

def should_continue(state: State) -> Literal["query_gen", "execute_query", END]:
    """Decide next step dynamically."""
    retry_count = getattr(state, "retry_count", 0)
    if retry_count >= 3:
        return END
    
    last_msg = state["messages"][-1]
    content = getattr(last_msg, "content", "")

    if content.startswith("Error"):
        return "query_gen"

    match = re.search(r"```sqlite\s+(.*?)```", content, re.DOTALL)
    if not match:
        return "query_gen"
    
    sql_query = match.group(1).strip()
    forbidden = ["insert", "update", "delete", "drop", "alter"]
    if any(f in sql_query.lower() for f in forbidden):
        return "query_gen"

    return "execute_query"

def final_output_node(state: State):
    """Convert SQL result into natural language answer."""
    last_msg = state["messages"][-1]
    try:
        parsed = json.loads(last_msg.content)
        sql_query = parsed.get("sql")
        result = parsed.get("result")
    except Exception:
        return {"messages": [AIMessage(content="Error: Could not parse SQL execution result.")]}
    
    result_str = json.dumps(result, indent=2).replace("{", "{{").replace("}", "}}")
    sql_query_escaped = sql_query.replace("{", "{{").replace("}", "}}")

    system_prompt = f"""
You are a helpful assistant.
Convert the SQL query and result into a concise natural language answer:

SQL Query:
{sql_query_escaped}

Result (JSON):
{result_str}

Rules:
- Summarize clearly.
- Proper punctuation.
- Mention relevant values (names, counts, totals).
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Convert the result into natural language.")
    ])
    message = (prompt | llm).invoke(state)
    return {"messages": [message]}
