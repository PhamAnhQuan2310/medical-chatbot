from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime
import json
import uuid
from accounts.history import get_current_user

router = APIRouter()

DATABASE = r"D:\TLCN\hoan thien\Hishiro_Chat\backend\accounts\Database\account.db"

def get_db():
    
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_guest_db():
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS guest_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                session_name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
       
        cur.execute("""
            CREATE TABLE IF NOT EXISTS guest_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'hybrid',
                decision_info TEXT,
                FOREIGN KEY (session_id) REFERENCES guest_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_guest_sessions_user_id ON guest_sessions(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_guest_messages_session_id ON guest_messages(session_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_guest_messages_user_id ON guest_messages(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_guest_messages_timestamp ON guest_messages(timestamp)")
        
        conn.commit()
        print("Guest chat database initialized successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"Error initializing guest database: {e}")
    finally:
        conn.close()


init_guest_db()


class GuestChatMessage(BaseModel):
    message: str
    response: str
    session_id: str
    source: Optional[str] = "hybrid"
    decision_info: Optional[Dict[str, Any]] = None

class GuestSessionCreate(BaseModel):
    session_name: str

class GuestSessionResponse(BaseModel):
    id: str
    session_name: str
    created_at: str
    last_activity: str
    message_count: int
    is_active: bool

class GuestMessageResponse(BaseModel):
    id: int
    message: str
    response: str
    timestamp: str
    source: str
    decision_info: Optional[Dict[str, Any]]

@router.post("/guest-chat/session")
def create_guest_session(data: GuestSessionCreate, current_user: dict = Depends(get_current_user)):
    """Tạo session chat mới cho guest"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        session_id = str(uuid.uuid4())
        
        cur.execute(
            """INSERT INTO guest_sessions (id, user_id, session_name) VALUES (?, ?, ?)""",
            (session_id, current_user["id"], data.session_name)
        )
        
        conn.commit()
        
        return {
            "success": True,
            "session_id": session_id,
            "session_name": data.session_name
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")
    finally:
        conn.close()

@router.post("/guest-chat/save")
def save_guest_message(data: GuestChatMessage, current_user: dict = Depends(get_current_user)):
    """Lưu tin nhắn guest chat"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        
        cur.execute(
            """INSERT INTO guest_messages 
               (session_id, user_id, message, response, source, decision_info) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data.session_id, current_user["id"], data.message, data.response, data.source, 
             json.dumps(data.decision_info) if data.decision_info else None)
        )
        
       
        cur.execute(
            """UPDATE guest_sessions 
               SET message_count = message_count + 1,
                   last_activity = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND user_id = ?""",
            (data.session_id, current_user["id"])
        )
        
        conn.commit()
        
        return {"success": True, "message": "Guest message saved"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving message: {str(e)}")
    finally:
        conn.close()

@router.get("/guest-chat/sessions", response_model=List[GuestSessionResponse])
def get_guest_sessions(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(50, description="Number of sessions to return")
):
    """Lấy danh sách session guest chat"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """SELECT id, session_name, created_at, last_activity, message_count, is_active
               FROM guest_sessions 
               WHERE is_active = 1 AND message_count > 0 AND user_id = ?
               ORDER BY last_activity DESC 
               LIMIT ?""",
            (current_user["id"], limit)
        )
        
        rows = cur.fetchall()
        
        return [
            GuestSessionResponse(
                id=row["id"],
                session_name=row["session_name"],
                created_at=row["created_at"],
                last_activity=row["last_activity"],
                message_count=row["message_count"],
                is_active=bool(row["is_active"])
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")
    finally:
        conn.close()

@router.get("/guest-chat/history/{session_id}", response_model=List[GuestMessageResponse])
def get_guest_history(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(50, description="Number of messages to return")
):
    """Lấy lịch sử chat của session guest"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        
        cur.execute(
            "SELECT user_id FROM guest_sessions WHERE id = ?",
            (session_id,)
        )
        session_owner = cur.fetchone()
        
        if not session_owner or session_owner["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        cur.execute(
            """SELECT id, message, response, timestamp, source, decision_info
               FROM guest_messages 
               WHERE session_id = ? AND user_id = ?
               ORDER BY timestamp ASC 
               LIMIT ?""",
            (session_id, current_user["id"], limit)
        )
        
        rows = cur.fetchall()
        
        return [
            GuestMessageResponse(
                id=row["id"],
                message=row["message"],
                response=row["response"],
                timestamp=row["timestamp"],
                source=row["source"] or "hybrid",
                decision_info=json.loads(row["decision_info"]) if row["decision_info"] else None
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")
    finally:
        conn.close()

@router.delete("/guest-chat/session/{session_id}")
def delete_guest_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Xóa session guest chat"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        
        cur.execute(
            "SELECT user_id FROM guest_sessions WHERE id = ?",
            (session_id,)
        )
        session_owner = cur.fetchone()
        
        if not session_owner or session_owner["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        
        cur.execute("DELETE FROM guest_messages WHERE session_id = ? AND user_id = ?", (session_id, current_user["id"]))
        
        
        cur.execute("DELETE FROM guest_sessions WHERE id = ? AND user_id = ?", (session_id, current_user["id"]))
        
        conn.commit()
        
        return {"success": True, "message": "Session deleted"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")
    finally:
        conn.close()

@router.patch("/guest-chat/session/{session_id}/name")
def update_guest_session_name(
    session_id: str, 
    current_user: dict = Depends(get_current_user),
    new_name: str = Query(..., alias="name")
):
    """Cập nhật tên session"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
       
        cur.execute(
            "SELECT user_id FROM guest_sessions WHERE id = ?",
            (session_id,)
        )
        session_owner = cur.fetchone()
        
        if not session_owner or session_owner["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        cur.execute(
            "UPDATE guest_sessions SET session_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (new_name, session_id, current_user["id"])
        )
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        conn.commit()
        
        return {"success": True, "new_name": new_name}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating session name: {str(e)}")
    finally:
        conn.close()

@router.get("/guest-chat/stats")
def get_guest_stats(current_user: dict = Depends(get_current_user)):
    """Lấy thống kê guest chat"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Thống kê tổng quan
        cur.execute(
            """SELECT 
                COUNT(DISTINCT id) as total_sessions,
                SUM(message_count) as total_messages,
                MAX(last_activity) as latest_activity
               FROM guest_sessions 
               WHERE is_active = 1 AND user_id = ?""",
            (current_user["id"],)
        )
        
        stats = cur.fetchone()
        
        return {
            "total_sessions": stats["total_sessions"] or 0,
            "total_messages": stats["total_messages"] or 0,
            "latest_activity": stats["latest_activity"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
    finally:
        conn.close()