from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import json
import os
import sqlite3
from datetime import datetime
import statistics

router = APIRouter(tags=["chat_history"])


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'Data', 'Data.db')

@router.get("/chat/history")
async def get_chat_history():
    """Lấy danh sách tất cả các cuộc hội thoại"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        

        cursor.execute("PRAGMA table_info(Sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Sessions table columns: {columns}")
        
  
        cursor.execute("""
            SELECT session_key, MAX(session_data) as last_activity, COUNT(*) as message_count
            FROM Sessions 
            GROUP BY session_key 
            ORDER BY session_key DESC
        """)
        
        sessions = cursor.fetchall()
        history = []
        
        for session_key, session_data, message_count in sessions:

            try:
  
                if session_data and session_data.startswith('{"chat_history"'):
                    import json
                    data = json.loads(session_data)
                    chat_history = data.get('chat_history', [])
                    

                    actual_message_count = len(chat_history)
                    

                    q_scores = []
                    for msg in chat_history:
                        if isinstance(msg, dict) and 'q_score' in msg:
                            q_scores.append(msg['q_score'])
                    
                    avg_q_score = statistics.mean(q_scores) if q_scores else 0
                    

                    last_timestamp = None
                    if chat_history:
                        last_msg = chat_history[-1]
                        if isinstance(last_msg, dict) and 'timestamp' in last_msg:
                            last_timestamp = last_msg['timestamp']
                    
                    if not last_timestamp:

                        last_timestamp = datetime.now().isoformat()
                    
                    history.append({
                        "id": str(session_key),
                        "timestamp": last_timestamp,
                        "message_count": actual_message_count,
                        "q_score": round(avg_q_score, 2)
                    })
                else:

                    history.append({
                        "id": str(session_key),
                        "timestamp": datetime.now().isoformat(),
                        "message_count": 0,
                        "q_score": 0
                    })
                    
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error parsing session_data for session {session_key}: {e}")
                # Fallback data
                history.append({
                    "id": str(session_key),
                    "timestamp": datetime.now().isoformat(),
                    "message_count": 0,
                    "q_score": 0
                })
            
        conn.close()
        return {"success": True, "history": history}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Lỗi khi lấy lịch sử chat: {str(e)}"}

@router.get("/chat/detail/{conversation_id}")
async def get_chat_detail(conversation_id: str):
    """Lấy chi tiết của một cuộc hội thoại cụ thể"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_data
            FROM Sessions 
            WHERE session_key = ?
        """, (conversation_id,))
        
        row = cursor.fetchone()
        
        if not row or not row[0]:
            return {"success": False, "message": f"Không tìm thấy hội thoại với ID {conversation_id}"}
        
        session_data = row[0]
        
        try:
            data = json.loads(session_data)
            chat_history = data.get('chat_history', [])
            
            if not chat_history:
                return {"success": False, "message": "Không có lịch sử chat trong session này"}
            
            messages = []
            q_history = []
            actions = set()
            q_scores = []
            
            for i, msg in enumerate(chat_history):
                if isinstance(msg, dict):
                    # Xử lý tin nhắn dạng dict
                    content = msg.get('message', msg.get('content', ''))
                    is_user = msg.get('isUser', msg.get('is_user', i % 2 == 0)) 
                    timestamp = msg.get('timestamp', datetime.now().isoformat())
                    intent = msg.get('intent')
                    sentiment = msg.get('sentiment')
                    q_score = msg.get('q_score')
                    action = msg.get('action')
                    state = msg.get('state')
                elif isinstance(msg, str):
                    content = msg
                    is_user = i % 2 == 0  
                    timestamp = datetime.now().isoformat()
                    intent = None
                    sentiment = None
                    q_score = None
                    action = None
                    state = None
                else:
                    continue  
                
                messages.append({
                    "content": content,
                    "isUser": bool(is_user),
                    "timestamp": timestamp,
                    "intent": intent,
                    "sentiment": sentiment
                })
                

                if q_score is not None and action is not None:
                    q_history.append({
                        "timestamp": timestamp,
                        "action": action,
                        "state": state or "unknown",
                        "score": q_score
                    })
                    q_scores.append(q_score)
                    if action:
                        actions.add(action)
            

            summary = generate_conversation_summary(messages)
            

            avg_q_score = statistics.mean(q_scores) if q_scores else 0
            max_q_score = max(q_scores) if q_scores else 0
            
            detail = {
                "summary": summary,
                "avg_q_score": round(avg_q_score, 2),
                "max_q_score": round(max_q_score, 2),
                "action_count": len(actions),
                "q_history": q_history,
                "messages": messages
            }
            
            conn.close()
            return {"success": True, "detail": detail}
            
        except json.JSONDecodeError as e:
            return {"success": False, "message": f"Lỗi parse JSON: {str(e)}"}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Lỗi khi lấy chi tiết hội thoại: {str(e)}"}

def generate_conversation_summary(messages):
    """
    Tạo tóm tắt đơn giản từ cuộc hội thoại
    """
    if not messages:
        return "Không có tin nhắn trong cuộc hội thoại này."
    

    user_messages = [m for m in messages if m["isUser"]]
    bot_messages = [m for m in messages if not m["isUser"]]
    

    intents = {}
    for msg in bot_messages:
        if msg.get("intent"):
            intent = msg["intent"]
            intents[intent] = intents.get(intent, 0) + 1
    
    most_common_intent = max(intents.items(), key=lambda x: x[1])[0] if intents else "chưa xác định"
    
 
    sentiments = {}
    for msg in user_messages:
        if msg.get("sentiment"):
            sentiment = msg["sentiment"]
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
    
    dominant_sentiment = max(sentiments.items(), key=lambda x: x[1])[0] if sentiments else "trung tính"
    

    summary = f"Cuộc hội thoại gồm {len(user_messages)} tin nhắn từ người dùng và {len(bot_messages)} phản hồi từ bot. "
    summary += f"Chủ đề chính: {most_common_intent}. "
    summary += f"Cảm xúc chủ đạo: {dominant_sentiment}."
    
    return summary


@router.get("/chat/debug/tables")
async def debug_tables():
    """Debug endpoint để kiểm tra cấu trúc database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        

        cursor.execute("PRAGMA table_info(Sessions)")
        sessions_columns = [{"name": col[1], "type": col[2]} for col in cursor.fetchall()]
        

        cursor.execute("SELECT session_key, SUBSTR(session_data, 1, 100) as sample_data FROM Sessions LIMIT 3")
        sample_data = [{"session_key": row[0], "sample_data": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "success": True,
            "database_path": DB_PATH,
            "tables": tables,
            "sessions_structure": sessions_columns,
            "sample_sessions": sample_data
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}