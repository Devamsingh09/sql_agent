# frontend.py
import streamlit as st
import requests
import pandas as pd

BACKEND_URL = "uvicorn app:app --host 0.0.0.0 --port $PORT"

st.set_page_config(page_title="AI SQL Assistant", layout="wide")

st.title("🤖 AI SQL Assistant for CSV + SQLite")

# ------------------- Upload Section -------------------
st.header("📤 Upload CSV")
with st.form("upload_form", clear_on_submit=True):
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    table_name = st.text_input("Table name in database", value="employees")
    submit = st.form_submit_button("Upload")

    if submit and uploaded_file:
        files = {"file": uploaded_file.getvalue()}
        data = {"table_name": table_name}
        res = requests.post(f"{BACKEND_URL}/upload", files={"file": uploaded_file}, data=data)
        if res.status_code == 200:
            st.success(res.json()["message"])
        else:
            st.error(res.json().get("error", "Upload failed."))

# ------------------- Schema Viewer -------------------
st.header("📊 Database Schema")
if st.button("Show Schema"):
    res = requests.get(f"{BACKEND_URL}/schema")
    if res.status_code == 200:
        st.json(res.json())
    else:
        st.error("Failed to fetch schema.")

# ------------------- Ask Questions -------------------
st.header("❓ Ask Your Database")
question = st.text_area("Enter your question", "Who has the lowest salary?")

if st.button("Ask"):
    payload = {"question": question}
    res = requests.post(f"{BACKEND_URL}/ask", json=payload)

    if res.status_code == 200:
        data = res.json()

        if "sql" in data:
            st.subheader("📝 Generated SQL Query")
            st.code(data["sql"], language="sql")

        if isinstance(data.get("answer"), list):
            st.subheader("📄 Query Results")
            df = pd.DataFrame(data["answer"])
            st.dataframe(df, use_container_width=True)
        else:
            st.subheader("⚠️ Response")
            st.json(data)
    else:
        st.error(res.json().get("error", "Query failed."))
        


