from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3

router = APIRouter()

DATABASE = r"D:\TLCN\hoan thien\Hishiro_Chat\backend\accounts\Database\account.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

class RoleChangeRequest(BaseModel):
    username: str
    new_role: str

@router.put("/change-role/")
def change_user_role(data: RoleChangeRequest):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (data.username,))
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cur.execute("UPDATE users SET role=? WHERE username=?", (data.new_role, data.username))
    conn.commit()
    return {"status": "success", "username": data.username, "new_role": data.new_role}

@router.get("/users/")
def list_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, email, role FROM users")
    users = [dict(row) for row in cur.fetchall()]
    return {"status": "success", "users": users}