import sqlite3
import os
import json
import random
from datetime import datetime, timedelta

# Connect to database
db_path = os.path.join(os.path.dirname(__file__), "Data.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Existing tables:", tables)

# Check if Sessions table exists and has data
if "Sessions" in tables:
    cursor.execute("SELECT COUNT(*) FROM Sessions")
    session_count = cursor.fetchone()[0]
    print(f"Sessions table has {session_count} records")
    
    # Show sample data
    cursor.execute("SELECT * FROM Sessions LIMIT 3")
    samples = cursor.fetchall()
    print("Sample Sessions data:", samples)
else:
    print("Sessions table does not exist. Creating it...")
    cursor.execute("""
        CREATE TABLE Sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_data TEXT
        )
    """)
    
    # Insert some sample data
    import json
    from datetime import datetime, timedelta
    
    sample_sessions = []
    for i in range(10):
        session_id = f"session_{i+1}"
        created_at = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S")
        session_data = json.dumps([
            {"role": "user", "content": f"Câu hỏi {i+1}", "intent": "question"},
            {"role": "assistant", "content": f"Trả lời {i+1}", "intent": "response"}
        ])
        sample_sessions.append((session_id, created_at, session_data))
    
    cursor.executemany(
        "INSERT INTO Sessions (session_id, created_at, session_data) VALUES (?, ?, ?)",
        sample_sessions
    )
    print("Inserted sample session data")

# Check if q_learning_logs table exists
if "q_learning_logs" not in tables:
    print("Creating q_learning_logs table...")
    cursor.execute("""
        CREATE TABLE q_learning_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            action TEXT,
            state TEXT,
            q_value REAL,
            reward REAL DEFAULT 0.0,
            user_query TEXT DEFAULT '',
            response_quality REAL DEFAULT 0.0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert sample Q-learning data
    import random
    sample_q_logs = []
    for i in range(20):
        session_id = f"session_{(i%10)+1}"
        action = random.choice(["rag", "gemini", "sql", "web_search", "mcp"])
        state = f"intent_rag_hist_{i%5}_sent_neutral"
        q_value = random.uniform(0.1, 0.9)
        reward = random.uniform(0.2, 0.8)
        user_query = f"Câu hỏi test {i+1}"
        response_quality = random.uniform(0.3, 0.9)
        timestamp = (datetime.now() - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S")
        sample_q_logs.append((session_id, action, state, q_value, reward, user_query, response_quality, timestamp))
    
    cursor.executemany(
        "INSERT INTO q_learning_logs (session_id, action, state, q_value, reward, user_query, response_quality, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        sample_q_logs
    )
    print("Inserted sample Q-learning data")
else:
    # Check if table has new columns, if not add them
    cursor.execute("PRAGMA table_info(q_learning_logs)")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"q_learning_logs columns: {columns}")
    
    if "reward" not in columns:
        print("Adding reward column...")
        cursor.execute("ALTER TABLE q_learning_logs ADD COLUMN reward REAL DEFAULT 0.0")
    
    if "user_query" not in columns:
        print("Adding user_query column...")
        cursor.execute("ALTER TABLE q_learning_logs ADD COLUMN user_query TEXT DEFAULT ''")
    
    if "response_quality" not in columns:
        print("Adding response_quality column...")
        cursor.execute("ALTER TABLE q_learning_logs ADD COLUMN response_quality REAL DEFAULT 0.0")

conn.commit()
conn.close()
print("Database setup completed!")
