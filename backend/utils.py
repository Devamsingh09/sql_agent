import pandas as pd
import sqlite3
import re
from backend.database import DB_PATH, table_exists


def save_csv_to_db(file, table_name: str):
    """Read CSV file and save as a SQLite table."""

    # Validate table name
    if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
        raise ValueError("Table name can only contain letters, numbers, and underscores.")

    # Check uniqueness
    if table_exists(table_name):
        raise ValueError(f"Table '{table_name}' already exists. Please choose a unique name.")

    df = pd.read_csv(file)

    # Clean column names — remove spaces, special chars
    df.columns = [re.sub(r'[^a-zA-Z0-9_]', '_', col.strip()) for col in df.columns]

    conn = sqlite3.connect(DB_PATH)
    df.to_sql(table_name, conn, if_exists="fail", index=False)
    conn.close()

    return len(df)