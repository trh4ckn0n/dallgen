import os
import sqlite3
from datetime import datetime

DB_NAME = 'history.db'

def init_db():
    schema_sql = """
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt TEXT NOT NULL,
        image_url TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """
    with sqlite3.connect(DB_NAME) as conn:
        conn.executescript(schema_sql)

def reset_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()

def insert_image(prompt, url):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO images (prompt, image_url, timestamp) VALUES (?, ?, ?)",
            (prompt, url, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()

def get_history():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, prompt, image_url, timestamp FROM images ORDER BY id DESC")
        return cur.fetchall()

def delete_image(image_id):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM images WHERE id=?", (image_id,))
        conn.commit()
