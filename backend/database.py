import sqlite3
import re

DB_PATH = "uploaded.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_schema() -> str:
    """Return full schema of all tables."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    schema_parts = []
    for table in tables:
        cursor.execute(f'PRAGMA table_info("{table}");')
        cols = cursor.fetchall()
        col_defs = ", ".join([f"{col[1]} ({col[2]})" for col in cols])
        schema_parts.append(f"Table: {table}\nColumns: {col_defs}")
    conn.close()
    return "\n\n".join(schema_parts) if schema_parts else "No tables found."


def get_table_schema(table_name: str) -> str:
    """Return schema for a specific table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table_name}");')
    cols = cursor.fetchall()
    conn.close()
    if not cols:
        return f"Table '{table_name}' not found."
    col_defs = ", ".join([f"{col[1]} ({col[2]})" for col in cols])
    return f"Table: {table_name}\nColumns: {col_defs}"


def get_all_tables() -> list:
    """Return list of all table names."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def table_exists(table_name: str) -> bool:
    """Check if a table already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def db_query_tool(sql: str) -> list:
    """Execute a SELECT query and return results as list of dicts."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def drop_table(table_name: str):
    """Safely drop a table by name."""
    if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
        raise ValueError(f"Invalid table name: '{table_name}'")
    if not table_exists(table_name):
        raise ValueError(f"Table '{table_name}' does not exist.")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'DROP TABLE "{table_name}";')
    conn.commit()
    conn.close()