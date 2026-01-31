from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import sqlite3
import bcrypt
from datetime import datetime

router = APIRouter()

DATABASE = r"D:\TLCN\hoan thien\Hishiro_Chat\backend\accounts\Database\account.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register/")
def register(data: RegisterRequest):
    conn = get_db()
    cur = conn.cursor()
    # Check if username or email exists
    cur.execute("SELECT id FROM users WHERE username=? OR email=?", (data.username, data.email))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    # Hash password
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    cur.execute(
        "INSERT INTO users (username, email, password, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (data.username, data.email, hashed, data.role, datetime.now(), datetime.now())
    )
    conn.commit()
    return {"status": "success", "id": cur.lastrowid}

@router.post("/login/")
def login(data: LoginRequest):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (data.username,))
    user = cur.fetchone()
    if not user or not bcrypt.checkpw(data.password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "status": "success",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "email": user["email"]
        }
    }