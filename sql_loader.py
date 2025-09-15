import pyodbc
import config

def get_connection():
    conn_str = (
        f"DRIVER={{{config.SQL_DRIVER}}};"
        f"SERVER={config.SQL_SERVER};"
        f"DATABASE={config.SQL_DATABASE};"
        f"UID={config.SQL_USERNAME};"
        f"PWD={config.SQL_PASSWORD}"
    )
    return pyodbc.connect(conn_str)

def fetch_one(query: str):
    """Fetch a single row from SQL Server"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def fetch_all(query: str):
    """Fetch all rows from SQL Server"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
