

### SQL Agent with Gemini 1.5 Flash

This project is a web application that acts as a natural language interface for a database. It allows users to upload a CSV file, which is then converted into a searchable SQLite database. The application uses the **Gemini 1.5 Flash** large language model (LLM) to convert natural language questions into SQL queries, executes the queries, and returns the results.

The project is a full-stack application composed of a **FastAPI backend** and a **Streamlit frontend**.

-----

### Live Application

**Currently running on**: [https://llm-based-sql-agent.streamlit.app/](https://llm-based-sql-agent.streamlit.app/)

-----

### Project Structure

  * **`app.py`**: The FastAPI backend. This file contains the API endpoints for uploading CSVs, generating SQL queries, and executing them. It orchestrates the LangChain agent and interacts with the database.
  * **`frontend.py`**: The Streamlit frontend. This file provides the web-based user interface, allowing users to interact with the backend API.
  * **`requirements.txt`**: Lists all the necessary Python libraries for the project.
  * **`.env`**: Stores environment variables, including the `GOOGLE_API_KEY`. This file is ignored by Git for security.
  * **`uploaded.db`**: The SQLite database file where uploaded CSV data is stored.

-----

### Features

  * **CSV Upload**: Uploads and converts CSV files into a persistent SQLite database table.
  * **Natural Language to SQL**: Uses Google's Gemini 1.5 Flash model to generate accurate SQLite queries from user questions.
  * **API-driven**: The separation of the frontend and backend allows for a modular and scalable design.
  * **Interactive UI**: A simple Streamlit interface to upload files and ask questions about the data.

-----

### Getting Started

#### Prerequisites

  * Python 3.11+
  * A valid Google Gemini API key

#### Local Setup

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Create and activate a virtual environment**:

    ```bash
    python -m venv venv
    venv\Scripts\activate  # On Windows
    source venv/bin/activate  # On macOS/Linux
    ```

3.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables**:
    Create a `.env` file in the root directory and add your API key:

    ```
    GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

5.  **Run the backend and frontend**:
    In two separate terminal windows, run the backend and frontend simultaneously:

    **Terminal 1 (Backend)**:

    ```bash
    uvicorn app:app --reload
    ```

    **Terminal 2 (Frontend)**:

    ```bash
    streamlit run frontend.py
    ```

-----

### Deployment

The application is designed for two-part deployment:

  * **Backend**: Can be deployed as a web service on platforms like **Render**.
  * **Frontend**: Can be deployed on **Streamlit Community Cloud**, which directly integrates with GitHub.

Remember to configure the backend URL as a secret in your Streamlit Cloud deployment.

-----

Here's the architecture diagram for your `app.py` backend:

[http://googleusercontent.com/image_generation_content/0](https://github.com/Devamsingh09/sql_agent)
