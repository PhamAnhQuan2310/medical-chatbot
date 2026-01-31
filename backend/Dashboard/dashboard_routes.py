"""
Dashboard routes for CareBot analytics and overview
"""
import sqlite3
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import os

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Path to the database - Changed to account.db
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "accounts", "Database", "account.db")

def get_db_connection():
    """Connect to account.db database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@router.get("/overview")
async def get_dashboard_overview():
    """Get dashboard overview from account.db chat_history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total sessions from chat_sessions table
        cursor.execute("SELECT COUNT(DISTINCT session_id) as total_sessions FROM chat_sessions WHERE is_active = 1")
        total_sessions = cursor.fetchone()["total_sessions"]
        
        # Get total messages from chat_history table
        cursor.execute("SELECT COUNT(*) as total_messages FROM chat_history WHERE status = 'active'")
        total_messages = cursor.fetchone()["total_messages"]
        
        # Get recent sessions (last 7 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) as recent_sessions 
            FROM chat_sessions 
            WHERE created_at >= datetime('now', '-7 days')
        """)
        recent_sessions = cursor.fetchone()["recent_sessions"]
        
        # Get total users
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()["total_users"]
        
        # Get message type distribution
        cursor.execute("""
            SELECT message_type, COUNT(*) as count
            FROM chat_history
            WHERE status = 'active'
            GROUP BY message_type
        """)
        message_type_distribution = {row["message_type"]: row["count"] for row in cursor.fetchall()}
        
        # Get daily activity for the last 7 days
        daily_activity = []
        for i in range(6, -1, -1):  # 6 days ago to today
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT COUNT(DISTINCT session_id) as sessions
                FROM chat_sessions
                WHERE DATE(created_at) = ?
            """, (date,))
            sessions_count = cursor.fetchone()["sessions"]
            daily_activity.append({
                "date": date,
                "sessions": sessions_count
            })
        
        # Get user activity (messages per user)
        cursor.execute("""
            SELECT u.username, u.role, COUNT(ch.id) as message_count
            FROM users u
            LEFT JOIN chat_history ch ON u.id = ch.user_id
            GROUP BY u.id
            ORDER BY message_count DESC
            LIMIT 10
        """)
        user_activity = [{"username": row["username"], "role": row["role"], "message_count": row["message_count"]} 
                        for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "recent_sessions": recent_sessions,
            "total_users": total_users,
            "message_type_distribution": message_type_distribution,
            "daily_activity": daily_activity,
            "user_activity": user_activity,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")

@router.get("/sessions/recent")
async def get_recent_sessions(limit: int = 10):
    """Get recent chat sessions from account.db"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cs.session_id, cs.title, cs.created_at, cs.last_activity, cs.is_active,
                   u.username, u.role,
                   COUNT(ch.id) as message_count
            FROM chat_sessions cs
            JOIN users u ON cs.user_id = u.id
            LEFT JOIN chat_history ch ON cs.session_id = ch.session_id
            GROUP BY cs.session_id
            ORDER BY cs.last_activity DESC
            LIMIT ?
        """, (limit,))
        
        sessions = []
        for row in cursor.fetchall():
            # Get last message for this session
            cursor.execute("""
                SELECT message, timestamp
                FROM chat_history
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (row["session_id"],))
            
            last_msg = cursor.fetchone()
            last_message = None
            if last_msg and last_msg["message"]:
                content = last_msg["message"]
                last_message = content[:100] + "..." if len(content) > 100 else content
            
            sessions.append({
                "session_id": row["session_id"],
                "title": row["title"],
                "username": row["username"],
                "role": row["role"],
                "created_at": row["created_at"],
                "last_activity": row["last_activity"],
                "message_count": row["message_count"],
                "last_message": last_message,
                "is_active": bool(row["is_active"])
            })
        
        conn.close()
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent sessions: {str(e)}")

@router.get("/analytics/performance")
async def get_performance_analytics():
    """Get performance analytics from chat_history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total sessions
        cursor.execute("SELECT COUNT(DISTINCT session_id) as total FROM chat_sessions")
        total_sessions = cursor.fetchone()["total"]
        
        # Calculate engaged sessions (sessions with more than 2 messages)
        cursor.execute("""
            SELECT session_id, COUNT(*) as msg_count
            FROM chat_history
            WHERE status = 'active'
            GROUP BY session_id
            HAVING COUNT(*) > 2
        """)
        engaged_sessions = len(cursor.fetchall())
        
        # Calculate engagement rate
        engagement_rate = (engaged_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Get messages per day for the last 30 days
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as message_count
            FROM chat_history
            WHERE timestamp >= date('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """)
        daily_messages = [{"date": row["date"], "message_count": row["message_count"]} 
                         for row in cursor.fetchall()]
        
        # Get average messages per session
        cursor.execute("""
            SELECT AVG(msg_count) as avg_messages
            FROM (
                SELECT COUNT(*) as msg_count
                FROM chat_history
                WHERE status = 'active'
                GROUP BY session_id
            )
        """)
        avg_messages = cursor.fetchone()["avg_messages"] or 0
        
        conn.close()
        
        return {
            "engagement_rate": round(engagement_rate, 2),
            "total_sessions": total_sessions,
            "engaged_sessions": engaged_sessions,
            "daily_messages": daily_messages,
            "avg_messages_per_session": round(avg_messages, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching performance analytics: {str(e)}")

@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get full chat history for a specific session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute("""
            SELECT cs.session_id, cs.title, cs.created_at, cs.last_activity,
                   u.username, u.role, u.email
            FROM chat_sessions cs
            JOIN users u ON cs.user_id = u.id
            WHERE cs.session_id = ?
        """, (session_id,))
        
        session_info = cursor.fetchone()
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get all messages in this session
        cursor.execute("""
            SELECT id, message, response, timestamp, message_type, is_private
            FROM chat_history
            WHERE session_id = ? AND status = 'active'
            ORDER BY timestamp ASC
        """, (session_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row["id"],
                "message": row["message"],
                "response": row["response"],
                "timestamp": row["timestamp"],
                "message_type": row["message_type"],
                "is_private": bool(row["is_private"])
            })
        
        conn.close()
        
        return {
            "session_info": {
                "session_id": session_info["session_id"],
                "title": session_info["title"],
                "username": session_info["username"],
                "role": session_info["role"],
                "email": session_info["email"],
                "created_at": session_info["created_at"],
                "last_activity": session_info["last_activity"],
                "message_count": len(messages)
            },
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session history: {str(e)}")

@router.get("/users/stats")
async def get_user_stats():
    """Get statistics for all users"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.username, u.role, u.email, u.created_at,
                   COUNT(DISTINCT ch.session_id) as total_sessions,
                   COUNT(ch.id) as total_messages,
                   MAX(ch.timestamp) as last_activity
            FROM users u
            LEFT JOIN chat_history ch ON u.id = ch.user_id
            GROUP BY u.id
            ORDER BY total_messages DESC
        """)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "email": row["email"],
                "created_at": row["created_at"],
                "total_sessions": row["total_sessions"],
                "total_messages": row["total_messages"],
                "last_activity": row["last_activity"]
            })
        
        conn.close()
        return {"users": users}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user stats: {str(e)}")

@router.get("/users/{user_id}/history")
async def get_user_history(user_id: int, limit: int = 50):
    """Get chat history for a specific user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("SELECT username, role, email FROM users WHERE id = ?", (user_id,))
        user_info = cursor.fetchone()
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's sessions
        cursor.execute("""
            SELECT session_id, title, created_at, last_activity
            FROM chat_sessions
            WHERE user_id = ?
            ORDER BY last_activity DESC
            LIMIT ?
        """, (user_id, limit))
        
        sessions = [dict(row) for row in cursor.fetchall()]
        
        # Get user's message count
        cursor.execute("SELECT COUNT(*) as total FROM chat_history WHERE user_id = ?", (user_id,))
        total_messages = cursor.fetchone()["total"]
        
        conn.close()
        
        return {
            "user_info": {
                "id": user_id,
                "username": user_info["username"],
                "role": user_info["role"],
                "email": user_info["email"],
                "total_messages": total_messages,
                "total_sessions": len(sessions)
            },
            "sessions": sessions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user history: {str(e)}")
