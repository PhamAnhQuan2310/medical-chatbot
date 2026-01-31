from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from chat_routes.chatbotrag import rag_chat
from utils.db_utils import get_chat_sessions, save_chat_sessions
from utils.utils import analyze_sentiment
import random, os, sqlite3, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'Data', 'Data.db')

router = APIRouter()

class Message(BaseModel):
    message: str
    session_key: str = None

class LanguageChange(BaseModel):
    language: str

class DeleteSession(BaseModel):
    session_key: str

@router.post("/chat_rag/")
async def handle_chat_rag(data: Message, request: Request):
    user_message = data.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Tin nhắn trống")
    session_key = data.session_key or request.session.get("session_key")
    if not session_key:
        session_key = str(random.randint(100000, 999999))
        request.session["session_key"] = session_key

    session_data = get_chat_sessions(session_key, DB_PATH)
    chat_history = session_data.get("chat_history", [])

    rag_result = rag_chat(user_message, top_k=5)
    bot_response = rag_result["answer"]
    sentiment = analyze_sentiment(user_message, "", "")

    # Lưu lịch sử chat
    chat_history.append({
        'message': user_message,
        'is_user': True,
        'sentiment': sentiment
    })
    chat_history.append({
        'message': bot_response,
        'is_user': False,
        'sentiment': None
    })
    session_data["chat_history"] = chat_history
    session_data["message_count"] = len(chat_history)
    save_chat_sessions(session_key, session_data, DB_PATH)
    request.session["session_key"] = session_key

    if isinstance(bot_response, dict):
        return JSONResponse({
            'response': bot_response,
            'sentiment': sentiment
        })
    else:
        return JSONResponse({
            'response': bot_response,
            'sentiment': sentiment,
            'sources': rag_result.get("sources", [])
        })

@router.post("/new_chat/")
async def new_chat(request: Request):
    session_key = str(random.randint(100000, 999999))
    # Tạo session mới trong DB
    save_chat_sessions(session_key, {"chat_history": [], "message_count": 0}, DB_PATH)
    request.session["session_key"] = session_key
    return JSONResponse({"status": "success", "session_key": session_key})

@router.post("/delete_chat/")
async def delete_chat(data: DeleteSession, request: Request):
    session_key_to_delete = data.session_key
    # Xóa session trong DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Sessions WHERE session_key = ?", (session_key_to_delete,))
    conn.commit()
    conn.close()
    # Nếu xóa session hiện tại, tạo session mới
    if session_key_to_delete == request.session.get("session_key"):
        new_session_key = str(random.randint(100000, 999999))
        save_chat_sessions(new_session_key, {"chat_history": [], "message_count": 0}, DB_PATH)
        request.session["session_key"] = new_session_key
        return JSONResponse({'status': 'success', 'session_key': new_session_key})
    return JSONResponse({'status': 'success'})

@router.get("/chat_history/")
async def chat_history(session_key: str, request: Request):
    session_data = get_chat_sessions(session_key, DB_PATH)
    history = session_data.get("chat_history", [])
    return JSONResponse({"chat_history": history})

@router.get("/sessions/")
async def get_sessions(request: Request):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT session_key, session_data FROM Sessions")
    rows = cursor.fetchall()
    conn.close()
    sessions = []
    for session_key, session_data in rows:
        data = json.loads(session_data)
        sessions.append({"session_key": session_key, "message_count": data.get("message_count", 0)})
    return JSONResponse({"sessions": sessions})

@router.get("/get_language/")
async def get_language(request: Request):
    lang = request.session.get("language", "vi")
    return JSONResponse({"language": lang})

@router.post("/set_language/")
async def set_language(data: LanguageChange, request: Request):
    request.session["language"] = data.language
    return JSONResponse({"status": "success"})