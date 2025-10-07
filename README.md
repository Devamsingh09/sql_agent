

# SQL Agent with Gemini 1.5 Flash

This project is a web application that acts as a natural language interface for a database. It allows users to upload a CSV file, which is then converted into a searchable SQLite database. The application uses the **Gemini 1.5 Flash** large language model (LLM) to convert natural language questions into SQL queries, executes the queries, and returns the results.

The project is a **full-stack application** composed of a FastAPI backend and a Streamlit frontend.

---

## Live Application

The backend is deployed on **Render**, and the frontend is deployed on **Streamlit Community Cloud**.

* **Backend URL:** `https://sql-agent-mpka.onrender.com/`
* **Frontend:** [https://llm-based-sql-agent.streamlit.app/](https://llm-based-sql-agent.streamlit.app/)

> The frontend uses `st.secrets["BACKEND_URL"]` to communicate with the backend.

---

## Project Structure

* `app.py` – The **FastAPI backend**. Contains API endpoints for uploading CSVs, generating SQL queries, and executing them. Orchestrates the LangChain agent and interacts with the SQLite database.
* `frontend.py` – The **Streamlit frontend**. Provides a web interface to upload CSV files and ask questions about the data.
* `requirements.txt` – Lists all necessary Python libraries for the project.
* `.env` – Stores environment variables, including the **GOOGLE_API_KEY**. This file is ignored by Git.
* `uploaded.db` – The SQLite database where uploaded CSV data is stored.

---

## Features

* **CSV Upload:** Upload and convert CSV files into a persistent SQLite database table.
* **Natural Language to SQL:** Uses Gemini 1.5 Flash LLM to generate accurate SQLite queries from user questions.
* **API-driven:** Separation of frontend and backend allows for modular and scalable design.
* **Interactive UI:** Simple Streamlit interface to upload files and ask questions about the data.

---

## Getting Started

### Prerequisites

* Python 3.11+
* A valid **Google Gemini API key**

### Local Setup

1. **Clone the repository:**

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

2. **Create and activate a virtual environment:**

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add your API key:

```
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

5. **Run backend and frontend locally (optional):**
   In separate terminals:

**Backend:**

```bash
uvicorn app:app --reload
```

**Frontend:**

```bash
streamlit run frontend.py
```

> Note: The frontend will read the backend URL from `st.secrets["BACKEND_URL"]` in deployed environments.

---

## Deployment

The application is designed for **two-part deployment**:

* **Backend:** Can be deployed on platforms like **Render**.
* **Frontend:** Can be deployed on **Streamlit Community Cloud**, which integrates directly with GitHub.

**Important:** Configure the backend URL as a secret in Streamlit Cloud. Example:

```python
# In Streamlit Cloud Secrets
BACKEND_URL = "https://sql-agent-mpka.onrender.com"
```

---

## Architecture Diagram

Here’s a high-level workflow of the backend (`app.py`):

```
[CSV Upload] ---> [SQLite DB] ---> [LangChain + Gemini 1.5 Flash] ---> [SQL Query] ---> [Query Result]
            \                                                      /
             ------------------- Frontend ------------------------
```

