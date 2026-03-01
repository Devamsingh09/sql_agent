import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv(override=True)  # Load .env file, override existing env vars if needed

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)