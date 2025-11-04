import sqlite3
import pandas as pd
from backend.config import DB_PATH

def save_csv_to_db(file_path: str, table_name: str):
    """Save a CSV file into SQLite database."""
    df = pd.read_csv(file_path)
    conn = sqlite3.connect(DB_PATH)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

