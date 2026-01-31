import sqlite3
import bcrypt
from datetime import datetime

DATABASE = "accounts/Database/account.db"

def add_user(username, password, email, role="user"):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    
    # Check if username already exists
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    if cur.fetchone():
        print(f"User '{username}' already exists!")
        conn.close()
        return False
    
    # Hash password
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # Insert new user
    cur.execute(
        "INSERT INTO users (username, email, password, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (username, email, hashed, role, datetime.now(), datetime.now())
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    
    print(f"User '{username}' added successfully with ID: {user_id}")
    return True

if __name__ == "__main__":
    # Add user huey
    add_user(
        username="huey",
        password="huey123",
        email="huey@example.com",
        role="employee"
    )
