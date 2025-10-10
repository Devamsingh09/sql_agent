
from fastapi import UploadFile, File, Form, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.utils import save_csv_to_db
from backend.workflow import app_graph
from backend.nodes import HumanMessage

class QueryRequest(BaseModel):
    question: str

app = FastAPI()
@app.post("/upload")
async def upload_csv(file: UploadFile = File(...), table_name: str = Form(...)):
    """Upload CSV and store as SQLite table."""
    try:
        # Save CSV to SQLite
        save_csv_to_db(file.file, table_name)
        return {"message": f"CSV uploaded and stored as table '{table_name}'."}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/ask")
async def ask_db(request: QueryRequest):
    """Ask a question and return natural language answer."""
    query = {"messages": [HumanMessage(content=request.question)]}
    try:
        response = app_graph.invoke(query)
        last_msg = response["messages"][-1].content
        return {"answer": last_msg}
    except Exception as e:
        return {"error": str(e)}

@app.get("/schema")
def schema():
    """Return the current DB schema."""
    try:
        from database import get_schema
        return {"schema": get_schema()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def root():
    return {"message": "Upload CSV at /upload, check schema at /schema, then query it at /ask"}
