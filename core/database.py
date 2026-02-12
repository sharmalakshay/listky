import sqlite3
from contextlib import contextmanager

DATABASE = "/app/data/listky.db"

def init_db():
    with sqlite3.connect(DATABASE, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            pin_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_ip_hash TEXT,
            failed_attempts INTEGER DEFAULT 0,
            last_fail DATETIME
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            slug TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            is_public BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS views (
            list_id INTEGER,
            view_date DATE,
            ip_hash TEXT,
            PRIMARY KEY (list_id, view_date, ip_hash),
            FOREIGN KEY (list_id) REFERENCES lists(id)
        )''')
        conn.commit()

@contextmanager
def get_db_context():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

def get_db():
    """FastAPI dependency to get database connection"""
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()