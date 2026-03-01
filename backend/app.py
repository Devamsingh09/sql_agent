from fastapi import UploadFile, File, Form, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.utils import save_csv_to_db
from backend.workflow import app_graph
from backend.database import get_all_tables, get_schema, get_table_schema, drop_table
from langchain_core.messages import HumanMessage


class QueryRequest(BaseModel):
    question:   str
    table_name: str


app = FastAPI(title="SQL Agent API")


# ── Root ──────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "SQL Agent is running. Docs at /docs"}


# ── Upload CSV ────────────────────────────────────────
@app.post("/upload")
async def upload_csv(file: UploadFile = File(...), table_name: str = Form(...)):
    """Upload a CSV file and store it as a SQLite table."""
    try:
        row_count = save_csv_to_db(file.file, table_name)
        return {"message": f"Table '{table_name}' created with {row_count} rows."}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── List Tables ───────────────────────────────────────
@app.get("/tables")
def list_tables():
    """Return all available table names."""
    try:
        tables = get_all_tables()
        return {"tables": tables}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Schema ────────────────────────────────────────────
@app.get("/schema")
def full_schema():
    """Return schema of all tables."""
    try:
        return {"schema": get_schema()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/schema/{table_name}")
def table_schema(table_name: str):
    """Return schema for a specific table."""
    try:
        return {"schema": get_table_schema(table_name)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Ask Question ──────────────────────────────────────
@app.post("/ask")
async def ask_db(request: QueryRequest):
    """Ask a natural language question on a selected table."""
    try:
        initial_state = {
            "messages":    [HumanMessage(content=request.question)],
            "table_name":  request.table_name,
            "sql_query":   "",
            "raw_result":  [],
            "nl_answer":   "",
            "error":       "",
            "retry_count": 0
        }
        response = app_graph.invoke(initial_state)
        return {
            "question":   request.question,
            "table_name": request.table_name,
            "sql_query":  response.get("sql_query", ""),
            "raw_result": response.get("raw_result", []),
            "answer":     response.get("nl_answer", ""),
            "error":      response.get("error", "")
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Delete Table ──────────────────────────────────────
@app.delete("/table/{table_name}")
def delete_table(table_name: str):
    """Delete a table from the database."""
    try:
        drop_table(table_name)
        return {"message": f"Table '{table_name}' deleted successfully."}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Generate Profiling Report ─────────────────────────
@app.get("/profile/{table_name}")
def profile_table(table_name: str):
    """Generate a ydata-profiling HTML report for a table."""
    try:
        import pandas as pd
        import sqlite3
        from ydata_profiling import ProfileReport
        import tempfile, os

        conn = sqlite3.connect("uploaded.db")
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
        conn.close()

        profile = ProfileReport(
            df,
            title=f"Dataset Report — {table_name}",
            explorative=True,
            correlations={"pearson": {"calculate": True}, "spearman": {"calculate": True}},
            missing_diagrams={"bar": True, "matrix": True},
            duplicates={"head": 10},
            progress_bar=False
        )

        # ✅ Windows fix — write to string directly, no temp file needed
        html_str = profile.to_html()
        html_bytes = html_str.encode("utf-8")

        from fastapi.responses import Response
        return Response(
            content=html_bytes,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={table_name}_report.html"}
        )
    except ImportError:
        return JSONResponse(status_code=500, content={"error": "ydata-profiling not installed. Run: pip install ydata-profiling"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})