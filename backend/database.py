# backend/database.py
import sqlite3
import pandas as pd
from langchain_community.utilities import SQLDatabase
from backend.config import DB_PATH



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
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
