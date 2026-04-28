import sqlite3

DB_NAME = "tvpi.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    with open("schema.sql", "r") as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()