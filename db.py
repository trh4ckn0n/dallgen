import sqlite3
from datetime import datetime

DB_NAME = 'history.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        with open("schema.sql", "r") as f:
            conn.executescript(f.read())

def insert_image(prompt, url):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO images (prompt, image_url, timestamp) VALUES (?, ?, ?)",
                    (prompt, url, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

def get_history():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT prompt, image_url, timestamp FROM images ORDER BY id DESC")
        return cur.fetchall()
