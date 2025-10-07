# frontend.py
import streamlit as st
import requests

st.title("AI SQL Assistant")

# Upload CSV
st.header("Upload CSV")
csv_file = st.file_uploader("Choose a CSV file", type="csv")
table_name = st.text_input("Table Name")

if st.button("Upload CSV") and csv_file and table_name:
    files = {"file": (csv_file.name, csv_file, "text/csv")}
    data = {"table_name": table_name}
    res = requests.post("http://127.0.0.1:8000/upload", files=files, data=data)
    st.write(res.json())

# Ask a question
st.header("Ask a question")
question = st.text_input("Your question")

if st.button("Ask") and question:
    res = requests.post("http://127.0.0.1:8000/ask", json={"question": question})
    st.write(res.json())
