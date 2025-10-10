# frontend.py
import streamlit as st
import requests

# Get backend URL from Streamlit secrets
BACKEND_URL = st.secrets["BACKEND_URL"]

st.title("AI SQL Assistant")

# ---------------- Upload CSV ----------------
st.header("Upload CSV")
csv_file = st.file_uploader("Choose a CSV file", type="csv")
table_name = st.text_input("Table Name")

if st.button("Upload CSV") and csv_file and table_name:
    files = {"file": (csv_file.name, csv_file, "text/csv")}
    data = {"table_name": table_name}
    try:
        res = requests.post(f"{BACKEND_URL}/upload", files=files, data=data)
        res.raise_for_status()  # raise exception for HTTP errors
        st.success("CSV uploaded successfully!")
        st.json(res.json())
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")

# ---------------- Ask a Question ----------------
st.header("Ask a Question")
question = st.text_input("Your question")

if st.button("Ask") and question:
    try:
        res = requests.post(f"{BACKEND_URL}/ask", json={"question": question})
        res.raise_for_status()
        st.success("Response from backend:")
        
        st.write(data["answer"])
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")

