import re
import json
import sqlparse
from typing import Annotated, TypedDict, Literal, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.graph import END
from backend.config import llm
from backend.database import get_table_schema, db_query_tool


class State(TypedDict):
    messages:     Annotated[list[AnyMessage], add_messages]
    table_name:   str       # selected table to query
    sql_query:    str       # final formatted SQL
    raw_result:   Any       # list of dicts from DB
    nl_answer:    str       # natural language answer
    error:        str       # any error message
    retry_count:  int       # retry counter


# ─────────────────────────────────────────
# NODE 1 — Generate SQL
# ─────────────────────────────────────────
def query_gen_node(state: State):
    table_name = state.get("table_name", "")
    schema = get_table_schema(table_name)

    system_prompt = f"""You are an expert SQLite query generator.

The user has selected this table:
{schema}

STRICT RULES:
1. Use ONLY SQLite syntax.
2. Only query the table: "{table_name}". Do not reference other tables.
3. Only SELECT statements — never INSERT, UPDATE, DELETE, DROP, ALTER.
4. LIMIT to 50 rows unless user asks for more.
5. For numeric comparisons on TEXT columns use CAST(col AS REAL).
6. Always wrap final SQL in:
```sqlite
SELECT ...
```
7. If question is unclear, make a reasonable assumption and note it.
8. For text filtering always use UPPER() on both sides to handle case mismatch.
   Example: WHERE UPPER(status) = 'SUCCESS'  not  WHERE status = 'Success'
   Same for all text columns: category, payment_mode, bank, status etc.
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])
    message = (prompt | llm).invoke(state)
    return {
        "messages": [message],
        "retry_count": state.get("retry_count", 0)
    }


# ─────────────────────────────────────────
# NODE 2 — Validate SQL
# ─────────────────────────────────────────
def query_validation_node(state: State):
    last_msg = state["messages"][-1]
    match = re.search(r"```sqlite\s+(.*?)```", last_msg.content, re.DOTALL)

    if not match:
        return {
            "messages": [AIMessage(content="Error: No SQL query found in response.")],
            "error": "No SQL query found in LLM response.",
            "retry_count": state.get("retry_count", 0) + 1
        }

    sql_query = match.group(1).strip()
    table_name = state.get("table_name", "")
    schema = get_table_schema(table_name)

    system_prompt = f"""You are a SQL validator.

Schema:
{schema}

SQL to validate:
{sql_query}

Rules:
- Only allow SELECT on table "{table_name}".
- Fix any invalid column or table names based on schema.
- Reject INSERT/UPDATE/DELETE/DROP/ALTER — return error if found.
- Return ONLY the corrected SQL wrapped in:
```sqlite
SELECT ...
```
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Validate and fix the SQL if needed.")
    ])
    checked = (prompt | llm).invoke(state)
    return {
        "messages": [checked],
        "error": ""
    }


# ─────────────────────────────────────────
# NODE 3 — Execute SQL
# ─────────────────────────────────────────
def execute_query_node(state: State):
    last_msg = state["messages"][-1]
    match = re.search(r"```sqlite\s+(.*?)```", last_msg.content, re.DOTALL)

    if not match:
        return {
            "messages": [AIMessage(content="Error: No valid SQL to execute.")],
            "error": "No valid SQL found after validation.",
            "sql_query": "",
            "raw_result": [],
            "retry_count": state.get("retry_count", 0) + 1
        }

    sql_query = match.group(1).strip()
    formatted_sql = sqlparse.format(sql_query, reindent=True, keyword_case="upper")

    try:
        result = db_query_tool(sql_query)
        return {
            "messages": [AIMessage(content=json.dumps({"sql": formatted_sql, "result": result}))],
            "sql_query": formatted_sql,
            "raw_result": result,
            "error": ""
        }
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"Error: SQL execution failed: {str(e)}")],
            "sql_query": formatted_sql,
            "raw_result": [],
            "error": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }


# ─────────────────────────────────────────
# NODE 4 — Natural Language Output
# ─────────────────────────────────────────
def final_output_node(state: State):
    last_msg = state["messages"][-1]
    try:
        parsed = json.loads(last_msg.content)
        sql_query = parsed.get("sql", "")
        result = parsed.get("result", [])
    except Exception:
        return {
            "messages": [AIMessage(content="Could not parse results.")],
            "nl_answer": "Could not parse SQL execution result.",
            "error": "Parse error in final output."
        }

    result_str = json.dumps(result, indent=2).replace("{", "{{").replace("}", "}}")
    sql_escaped = sql_query.replace("{", "{{").replace("}", "}}")

    system_prompt = f"""You are a helpful data analyst assistant.

Convert the following SQL query and its result into a clear, concise natural language summary.

SQL Query:
{sql_escaped}

Result:
{result_str}

Rules:
- Be concise and clear.
- Mention key numbers, names, or totals.
- Use proper punctuation.
- Do not repeat the SQL query.
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Summarize the result in natural language.")
    ])
    message = (prompt | llm).invoke(state)
    return {
        "messages": [message],
        "nl_answer": message.content,
        "error": ""
    }


# ─────────────────────────────────────────
# CONDITIONAL EDGE
# ─────────────────────────────────────────
def should_continue(state: State) -> Literal["query_gen", "execute_query", "__end__"]:
    if state.get("retry_count", 0) >= 3:
        return "__end__"

    last_msg = state["messages"][-1]
    content = getattr(last_msg, "content", "")

    if content.startswith("Error"):
        return "query_gen"

    match = re.search(r"```sqlite\s+(.*?)```", content, re.DOTALL)
    if not match:
        return "query_gen"

    sql = match.group(1).strip().lower()
    forbidden = ["insert", "update", "delete", "drop", "alter"]
    if any(word in sql for word in forbidden):
        return "query_gen"

    return "execute_query"