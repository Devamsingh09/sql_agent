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

app = FastAPI(title="CSV Upload + Gemini 1.5 Flash SQL API")

DB_PATH = "uploaded.db"

# ------------------- LLM -------------------
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

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

def execute_query_gen(state: State):
    """Extract SQL from LLM response and run it."""
    last_msg = state["messages"][-1]

    # Extract SQL from fenced block
    match = re.search(r"```sqlite\s+(.*?)```", last_msg.content, re.DOTALL)
    if not match:
        return {"messages": [AIMessage(content="Error: No SQL query found in LLM response.")]}

    sql_query = match.group(1).strip()

    # Format SQL nicely
    formatted_sql = sqlparse.format(sql_query, reindent=True, keyword_case="upper")

    result = db_query_tool(sql_query)

    # Store as string inside AIMessage
    return {"messages": [AIMessage(content=json.dumps({"sql": formatted_sql, "result": result}, indent=2))]}

def should_continue(state: State) -> Literal["execute_query", END]:
    """Always continue to execute query after generation."""
    return "execute_query"

# ------------------- Workflow -------------------
workflow = StateGraph(State)
workflow.add_node("query_gen", query_gen_node)
workflow.add_node("execute_query", execute_query_gen)
workflow.add_edge(START, "query_gen")
workflow.add_conditional_edges("query_gen", should_continue)

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
    """Ask a question in natural language and get DB results."""
    query = {"messages": [HumanMessage(content=request.question)]}
    try:
        response = app_graph.invoke(query)
        last_msg = response["messages"][-1].content

        # Try to parse JSON if possible
        try:
            parsed = json.loads(last_msg)
            return {"sql": parsed.get("sql"), "answer": parsed.get("result")}
        except Exception:
            return {"answer": last_msg}
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
