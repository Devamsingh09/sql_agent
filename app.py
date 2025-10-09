# app.py
import os
import sqlite3
import pandas as pd
import re
import json
import sqlparse
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import AnyMessage, add_messages
from typing import Annotated, Literal, TypedDict

# ------------------- Setup -------------------
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

app = FastAPI(title="CSV Upload + Gemini 2.5 Flash SQL API")

DB_PATH = "uploaded.db"

# ------------------- LLM -------------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def get_db():
    return SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

def get_schema() -> str:
    """Fetch DB schema for prompt injection."""
    db = get_db()
    return db.get_table_info()

def db_query_tool(query: str):
    """Run SQL query against SQLite DB and return results as JSON."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(query, conn)
        return df.to_dict(orient="records")  # JSON-friendly
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

# ------------------- State + Nodes -------------------
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def query_gen_node(state: State):
    """Generate SQL query from natural language question, with schema awareness."""
    schema = get_schema()
    system_prompt = f"""You are a SQL expert.
The database schema is:

{schema}

Given a question, write a syntactically correct SQLite SELECT query.
- Use ONLY the tables and columns shown above.
- Do not guess column names.
- Do not modify data (no INSERT/UPDATE/DELETE).
- Always wrap the SQL in ```sqlite ... ``` fences.
- Never return more than 50 rows unless explicitly asked.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])

    query_gen = prompt | llm
    message = query_gen.invoke(state)
    return {"messages": [message]}

def query_check_node(state: State):
    """Double-check and correct the SQL query before execution."""
    last_msg = state["messages"][-1]

    # Extract SQL
    match = re.search(r"```sqlite\s+(.*?)```", last_msg.content, re.DOTALL)
    if not match:
        return {"messages": [AIMessage(content="Error: No SQL query found in LLM response.")]}
    sql_query = match.group(1).strip()
    schema = get_schema()

    # Validator prompt
    system_prompt = f"""You are a SQL validator.
The database schema is:

{schema}

Check the following SQL for correctness:
{sql_query}

Rules:
- Fix column/table name errors if they don’t exist in schema.
- Do not allow INSERT/UPDATE/DELETE/DROP.
- Ensure it's valid SQLite syntax.
- Always return ONLY the corrected SQL in ```sqlite ... ``` fences.
- Important: SQLite INSTR() only accepts 2 arguments: INSTR(string, substring).
Do NOT use more than 2 parameters. Do NOT use Oracle-style syntax.

"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Validate and correct the SQL query if needed.")
    ])

    query_check = prompt | llm
    checked = query_check.invoke(state)
    return {"messages": [checked]}

def execute_query_gen(state: State):
    """Extract SQL from checked response and run it."""
    last_msg = state["messages"][-1]

    # Extract SQL
    match = re.search(r"```sqlite\s+(.*?)```", last_msg.content, re.DOTALL)
    if not match:
        return {"messages": [AIMessage(content="Error: No SQL query found in LLM response.")]}
    sql_query = match.group(1).strip()

    # Format SQL nicely
    formatted_sql = sqlparse.format(sql_query, reindent=True, keyword_case="upper")

    result = db_query_tool(sql_query)

    return {"messages": [AIMessage(content=json.dumps({"sql": formatted_sql, "result": result}, indent=2))]}

def should_continue(state: State) -> Literal["query_gen", "query_check", END]:
    """
    Decide the next step dynamically:
    - If last message has 'error', regenerate query.
    - If last message has 'tool_calls' (i.e., SQL ready to execute), end workflow.
    - Otherwise, validate/correct the query in query_check.
    """
    last_msg = state["messages"][-1]

    # Case 1: Error detected → go back to query generation
    if getattr(last_msg, "content", "").startswith("Error:"):
        return "query_gen"

    # Case 2: SQL ready to execute → END
    if getattr(last_msg, "tool_calls", None):
        return END

    # Case 3: Query might need validation/correction → query_check
    return "query_check"


def nl_output_node(state: State):
    """Convert SQL result into natural language answer."""
    last_msg = state["messages"][-1]

    try:
        parsed = json.loads(last_msg.content)
        sql_query = parsed.get("sql")
        result = parsed.get("result")
    except Exception:
        return {"messages": [AIMessage(content="Error: Could not parse SQL execution result.")]}

    # Escape JSON to prevent template errors
    result_str = json.dumps(result, indent=2).replace("{", "{{").replace("}", "}}")
    sql_query_escaped = sql_query.replace("{", "{{").replace("}", "}}")

    # Prepare LLM prompt
    system_prompt = f"""
You are a helpful assistant. 
Convert the following SQL query and its result into a concise, natural language answer for a human:

SQL Query:
{sql_query_escaped}

Result (JSON):
{result_str}

Rules:
- Summarize the data in clear sentences.
- Use proper punctuation and commas.
- Mention the relevant values (like names, totals, counts) depending on the query.
- Do not return raw JSON.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Convert the result into natural language.")
    ])

    nl_model = prompt | llm
    message = nl_model.invoke(state)
    return {"messages": [message]}


# ------------------- Workflow -------------------
workflow = StateGraph(State)

workflow.add_node("query_gen", query_gen_node)
workflow.add_node("query_check", query_check_node)
workflow.add_node("execute_query", execute_query_gen)
workflow.add_node("nl_output", nl_output_node)  # ✅ final NL step

workflow.add_edge(START, "query_gen")
workflow.add_conditional_edges("query_gen", should_continue)
workflow.add_edge("query_check", "execute_query")
workflow.add_edge("execute_query", "nl_output")  # run final NL conversion

app_graph = workflow.compile()



# ------------------- FastAPI Endpoints -------------------
@app.post("/upload")
async def upload_csv(file: UploadFile = File(...), table_name: str = Form(...)):
    """Upload CSV and store as SQLite table."""
    try:
        df = pd.read_csv(file.file)
        conn = sqlite3.connect(DB_PATH)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()
        return {"message": f"CSV uploaded and stored as table '{table_name}'."}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

class QueryRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask_db(request: QueryRequest):
    """Ask a question and return NL answer."""
    query = {"messages": [HumanMessage(content=request.question)]}
    try:
        response = app_graph.invoke(query)
        last_msg = response["messages"][-1].content
        return {"answer": last_msg}  # now it's human-readable text
    except Exception as e:
        return {"error": str(e)}


@app.get("/schema")
def schema():
    """Return the current DB schema (tables + columns)."""
    try:
        return {"schema": get_schema()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def root():
    return {"message": "Upload CSV at /upload, check schema at /schema, then query it at /ask"}

