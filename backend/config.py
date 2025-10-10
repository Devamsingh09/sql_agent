import os
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
DB_PATH = "uploaded.db"

# LLM instance
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

app = FastAPI(title="CSV Upload + Gemini 2.5 Flash SQL API")


