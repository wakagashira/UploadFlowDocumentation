import pyodbc
import config

def get_connection():
    print("DEBUG: SQL Username in use:", config.SQL_USERNAME)
    conn = pyodbc.connect(
        f"DRIVER={{{config.SQL_DRIVER}}};"
        f"SERVER={config.SQL_SERVER};"
        f"DATABASE={config.SQL_DATABASE};"
        f"UID={config.SQL_USERNAME};"
        f"PWD={config.SQL_PASSWORD}"
    )
    return conn

def fetch_all(query):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = []
    for row in cursor.fetchall():
        flow_name, status, fieldname, description, usecase = row
        meta = {}
        rows.append((flow_name, status, fieldname, description, usecase, meta))
    conn.close()
    return rows
