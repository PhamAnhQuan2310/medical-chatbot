import sqlite3
import json

def get_chat_sessions(session_key, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT session_data FROM Sessions WHERE session_key = ?", (session_key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    else:
        return {"chat_history": [], "message_count": 0}

def save_chat_sessions(session_key, session_data, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    data_str = json.dumps(session_data)
    cursor.execute(
        "INSERT OR REPLACE INTO Sessions (session_key, session_data) VALUES (?, ?)",
        (session_key, data_str)
    )
    conn.commit()
    conn.close()