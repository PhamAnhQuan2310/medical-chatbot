from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime
import json

router = APIRouter()

DATABASE = r"D:\TLCN\hoan thien\Hishiro_Chat\backend\accounts\Database\account.db"

def get_db():
    
    conn = sqlite3.connect(DATABASE) #Kết nối database với row factory
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user(authorization: str = Header(None)):
    """Lấy thông tin user hiện tại từ header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        # Format: "Bearer user_id" hoặc "user_id"
        if authorization.startswith("Bearer "):
            user_id = int(authorization.split(" ")[1])
        else:
            user_id = int(authorization)
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return dict(user)
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

# Pydantic Models
class ChatMessageCreate(BaseModel):
    message: str
    response: str
    session_id: Optional[str] = None
    is_private: Optional[bool] = True
    message_type: Optional[str] = "text"

class ChatHistoryResponse(BaseModel):
    id: int
    user_id: int
    message: str
    response: str
    timestamp: str
    session_id: Optional[str]
    is_private: bool
    status: str
    message_type: str

class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: str
    last_activity: str
    message_count: int
    is_active: bool

class UserChatStats(BaseModel):
    total_messages: int
    total_sessions: int
    first_chat_time: Optional[str]
    last_chat_time: Optional[str]

# API Endpoints
@router.post("/chat/save")
def save_chat_message(data: ChatMessageCreate, user: dict = Depends(get_current_user)):
    """Lưu tin nhắn chat cho user hiện tại"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        print(f"DEBUG - Saving chat for user {user['id']}: {data.message[:50]}...")
        
  
        if data.session_id:
            words = data.message.split()[:4]  
            session_title = " ".join(words)
            if len(data.message.split()) > 4:
                session_title += "..."
            
            cur.execute(
                "INSERT OR IGNORE INTO chat_sessions (session_id, user_id, title) VALUES (?, ?, ?)",
                (data.session_id, user["id"], session_title)
            )
        
        # Lưu chat message
        cur.execute(
            """INSERT INTO chat_history 
               (user_id, message, response, session_id, is_private, message_type) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user["id"], data.message, data.response, data.session_id, 
             data.is_private, data.message_type)
        )
        
        message_id = cur.lastrowid
        conn.commit()
        
        print(f"DEBUG - Chat saved successfully with ID: {message_id}")
        
        return {
            "status": "success", 
            "id": message_id,
            "user_id": user["id"],
            "session_id": data.session_id
        }
        
    except Exception as e:
        conn.rollback()
        print(f"ERROR - Failed to save chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving chat: {str(e)}")
    finally:
        conn.close()

@router.get("/chat/history", response_model=List[ChatHistoryResponse])
def get_user_chat_history(
    user: dict = Depends(get_current_user),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(50, description="Number of messages to return"),
    offset: int = Query(0, description="Offset for pagination"),
    message_type: Optional[str] = Query(None, description="Filter by message type")
):
    """Lấy lịch sử chat của user hiện tại"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        query = """
            SELECT id, user_id, message, response, timestamp, session_id, 
                   is_private, status, message_type 
            FROM chat_history 
            WHERE user_id = ? AND status = 'active'
        """
        params = [user["id"]]
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
            
        if message_type:
            query += " AND message_type = ?"
            params.append(message_type)
            
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        return [
            ChatHistoryResponse(
                id=row["id"],
                user_id=row["user_id"],
                message=row["message"],
                response=row["response"],
                timestamp=row["timestamp"],
                session_id=row["session_id"],
                is_private=bool(row["is_private"]),
                status=row["status"],
                message_type=row["message_type"]
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")
    finally:
        conn.close()

@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
def get_user_chat_sessions(user: dict = Depends(get_current_user)):
    """Lấy danh sách session chat của user"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                cs.session_id,
                cs.title,
                cs.created_at,
                cs.last_activity,
                cs.is_active,
                COUNT(ch.id) as message_count
            FROM chat_sessions cs
            LEFT JOIN chat_history ch ON cs.session_id = ch.session_id AND ch.status = 'active'
            WHERE cs.user_id = ?
            GROUP BY cs.session_id, cs.title, cs.created_at, cs.last_activity, cs.is_active
            ORDER BY cs.last_activity DESC
        """, (user["id"],))
        
        rows = cur.fetchall()
        
        return [
            ChatSessionResponse(
                session_id=row["session_id"],
                title=row["title"],
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

@router.get("/chat/stats", response_model=UserChatStats)
def get_user_chat_stats(user: dict = Depends(get_current_user)):
    """Lấy thống kê chat của user"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                COUNT(ch.id) as total_messages,
                COUNT(DISTINCT ch.session_id) as total_sessions,
                MIN(ch.timestamp) as first_chat_time,
                MAX(ch.timestamp) as last_chat_time
            FROM chat_history ch
            WHERE ch.user_id = ? AND ch.status = 'active'
        """, (user["id"],))
        
        row = cur.fetchone()
        
        return UserChatStats(
            total_messages=row["total_messages"] or 0,
            total_sessions=row["total_sessions"] or 0,
            first_chat_time=row["first_chat_time"],
            last_chat_time=row["last_chat_time"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
    finally:
        conn.close()

@router.delete("/chat/history/{message_id}")
def delete_chat_message(message_id: int, user: dict = Depends(get_current_user)):
    """Xóa một tin nhắn cụ thể (soft delete)"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Kiểm tra quyền sở hữu
        cur.execute(
            "SELECT user_id FROM chat_history WHERE id = ? AND user_id = ?",
            (message_id, user["id"])
        )
        
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Message not found or access denied")
        
        # Soft delete
        cur.execute(
            "UPDATE chat_history SET status = 'deleted', updated_at = ? WHERE id = ?",
            (datetime.now(), message_id)
        )
        
        conn.commit()
        return {"status": "success", "message": "Message deleted"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting message: {str(e)}")
    finally:
        conn.close()

@router.delete("/chat/session/{session_id}")
def delete_chat_session(session_id: str, user: dict = Depends(get_current_user)):
    """Xóa toàn bộ session chat (hard delete)"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "SELECT user_id FROM chat_sessions WHERE session_id = ? AND user_id = ?",
            (session_id, user["id"])
        )
        
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Session not found or access denied")
        
        cur.execute(
            "DELETE FROM chat_history WHERE session_id = ? AND user_id = ?",
            (session_id, user["id"])
        )
        

        cur.execute(
            "DELETE FROM chat_sessions WHERE session_id = ? AND user_id = ?",
            (session_id, user["id"])
        )
        
        deleted_count = cur.rowcount
        conn.commit()
        
        return {"status": "success", "deleted_messages": deleted_count}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")
    finally:
        conn.close()

@router.patch("/chat/session/{session_id}/title")
def update_session_title(
    session_id: str, 
    title: str, 
    user: dict = Depends(get_current_user)
):
    """Cập nhật tiêu đề session"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE session_id = ? AND user_id = ?",
            (title, datetime.now(), session_id, user["id"])
        )
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
        
        conn.commit()
        return {"status": "success", "new_title": title}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating session title: {str(e)}")
    finally:
        conn.close()


@router.get("/admin/chat/all")
def get_all_chat_history(
    user: dict = Depends(get_current_user),
    limit: int = Query(100, description="Number of messages to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """Admin: Xem tất cả lịch sử chat (chỉ admin)"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                ch.id, ch.user_id, u.username, u.role,
                ch.message, ch.response, ch.timestamp, ch.session_id,
                ch.is_private, ch.status, ch.message_type
            FROM chat_history ch
            JOIN users u ON ch.user_id = u.id
            WHERE ch.status = 'active'
            ORDER BY ch.timestamp DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cur.fetchall()
        
        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "username": row["username"],
                "user_role": row["role"],
                "message": row["message"],
                "response": row["response"],
                "timestamp": row["timestamp"],
                "session_id": row["session_id"],
                "is_private": bool(row["is_private"]),
                "status": row["status"],
                "message_type": row["message_type"]
            }
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all chat history: {str(e)}")
    finally:
        conn.close()

@router.get("/admin/stats/overview")
def get_system_chat_stats(user: dict = Depends(get_current_user)):
    """Admin: Thống kê tổng quan hệ thống"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                u.role,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(ch.id) as total_messages,
                COUNT(DISTINCT cs.session_id) as total_sessions,
                MAX(ch.timestamp) as last_activity
            FROM users u
            LEFT JOIN chat_history ch ON u.id = ch.user_id AND ch.status = 'active'
            LEFT JOIN chat_sessions cs ON u.id = cs.user_id AND cs.is_active = 1
            GROUP BY u.role
            ORDER BY user_count DESC
        """)
        
        rows = cur.fetchall()
        
        return {
            "stats_by_role": [
                {
                    "role": row["role"],
                    "user_count": row["user_count"],
                    "total_messages": row["total_messages"] or 0,
                    "total_sessions": row["total_sessions"] or 0,
                    "last_activity": row["last_activity"]
                }
                for row in rows
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching system stats: {str(e)}")
    finally:
        conn.close()