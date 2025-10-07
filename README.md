# SQL Agent with Gemini 2.5 Flash
<img width="400" height="400" alt="Gemini_Generated_Image_w19ayjw19ayjw19a" src="https://github.com/user-attachments/assets/4ac892e6-6564-4d08-b72c-b86659a24a2d" />


This project is a **web-based AI SQL assistant** that allows users to interact with a database using **natural language**. Users can upload CSV files, which are converted into a searchable SQLite database. The **Gemini 2.5 Flash LLM** is used to convert natural language questions into SQL queries, validate them, execute them, and return human-readable answers.

The project is a **full-stack application** with a **FastAPI backend** and a **Streamlit frontend**.

---

## Live Application

* **Backend (Render):** [https://sql-agent-mpka.onrender.com/](https://sql-agent-mpka.onrender.com/)
* **Frontend (Streamlit):** [https://llm-based-sql-agent.streamlit.app/](https://llm-based-sql-agent.streamlit.app/)

> The frontend reads the backend URL from `st.secrets["BACKEND_URL"]`.

---

## Project Structure

* `app.py` – **FastAPI backend**. Handles CSV uploads, SQL query generation, validation, execution, and converting results to natural language.
* `frontend.py` – **Streamlit frontend**. User interface for uploading CSVs and asking questions.
* `requirements.txt` – List of Python dependencies.
* `.env` – Environment variables including `GOOGLE_API_KEY`. Ignored by Git.
* `uploaded.db` – SQLite database storing uploaded CSV data.

---

## Features

1. **CSV Upload**
   Upload CSV files and store them as SQLite tables for querying.

2. **Natural Language to SQL**
   Uses **Gemini 2.5 Flash LLM** to generate SQL queries that respect the database schema.

3. **SQL Validation**
   Queries are validated and corrected before execution to ensure correctness and security.

4. **Human-Readable Answers**
   Query results are converted into natural language summaries for easy understanding.

5. **Modular Workflow**
   The backend uses a **state graph workflow**:

   ```
   query_gen → query_check → execute_query → nl_output
   ```

   * `query_gen`: Generate SQL from natural language.
   * `query_check`: Validate and correct SQL.
   * `execute_query`: Run SQL on SQLite.
   * `nl_output`: Convert results into natural language.

---

## Getting Started

### Prerequisites

* Python 3.11+
* A valid **Google Gemini API key**

### Local Setup

1. **Clone the repository**

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
   Create a `.env` file:

```
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

5. **Run backend and frontend locally** (optional)
   In separate terminals:

**Backend:**

```bash
uvicorn app:app --reload
```

**Frontend:**

```bash
streamlit run frontend.py
```

> In deployed mode, the frontend reads the backend URL from `st.secrets["BACKEND_URL"]`.

---

## API Endpoints

| Endpoint  | Method | Description                                                     |
| --------- | ------ | --------------------------------------------------------------- |
| `/upload` | POST   | Upload CSV file and store as a table.                           |
| `/ask`    | POST   | Ask a natural language question. Returns human-readable answer. |
| `/schema` | GET    | Return current database schema (tables + columns).              |
| `/`       | GET    | Basic welcome message.                                          |

---

## Deployment

* **Backend:** Deploy on **Render** (or similar cloud platforms).
* **Frontend:** Deploy on **Streamlit Community Cloud**, linking your GitHub repository.
* **Secrets:** Add `BACKEND_URL` in Streamlit Cloud secrets pointing to your Render backend.

---

## Workflow Architecture

The backend uses a **state graph workflow** to dynamically generate, validate, and execute SQL:

```
START → query_gen → query_check → execute_query → nl_output → END
```

* Dynamic transitions:

  * If LLM returns an error → regenerate SQL.
  * If SQL is valid → execute query.
  * Convert query results into natural language for users.

---

## Example Usage

1. Upload a CSV file as a table.
2. Ask questions like:

   ```
   "List the top 5 customers by total purchase amount."
   ```
3. Receive SQL-generated results in **natural language**:

   ```
   "The top 5 customers are Alice, Bob, Charlie, Dave, and Eve with respective totals of..."
   ```



