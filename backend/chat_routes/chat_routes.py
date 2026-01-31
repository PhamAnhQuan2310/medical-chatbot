from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import random, sqlite3, json, os, time
from utils.intent import classify_intent_combined
from chat_routes.chatbotrag import rag_chat
from pydantic import BaseModel
from utils.db_utils import get_chat_sessions, save_chat_sessions
from utils.gemini_utils import get_gemini_response
from rag.rag_utils import rag_retrieve
from rl.Q_Learning import Bandit, QLearningAgent
from rl.q_learning_manager import QLearningManager
from utils.utils import execute_sql_query, analyze_chat_history, normalize_question, analyze_sentiment
from utils.data_import import get_schema_and_context
from chat_routes.Scripts import handle_script_message
from utils.web_search import search_web, generate_web_search_response


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR,'..', 'Data', 'Data.db')
CONTEXT_PATH = os.path.join(BASE_DIR,'..','Data','table_context.json')

schema = get_schema_and_context(DB_PATH)
context = json.load(open(CONTEXT_PATH, 'r', encoding='utf-8'))


ql_manager = QLearningManager(DB_PATH)


test_prompt = """
Dưới đây là cấu trúc các bảng hiện có trong database:
{schema}
Còn đây là ngữ cảnh của các bảng trong database:
{context}
Hãy tạo truy vấn SQL hợp lệ để trả lời câu hỏi sau, chỉ trả về SQL, không giải thích.
Câu hỏi: {user_input}
"""



router = APIRouter()





class Message(BaseModel):
    message: str
    session_key: str = None

class LanguageChange(BaseModel):
    language: str

class DeleteSession(BaseModel):
    session_key: str

@router.post("/chat/")
async def handle_chat(data: Message, request: Request):
    user_message = data.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Tin nhắn trống")
    language = request.session.get("language", "vi")
    session_key = data.session_key or request.session.get("session_key")
    if not session_key:
        session_key = str(random.randint(100000, 999999))
        request.session["session_key"] = session_key


    session_data = get_chat_sessions(session_key, DB_PATH)
    chat_history = session_data.get("chat_history", [])


    start_time = time.time()
    
 
    user_message = normalize_question(user_message)
    intent = classify_intent_combined(user_message, GEMINI_API_URL, GEMINI_API_KEY)
    sentiment = analyze_sentiment(user_message, GEMINI_API_URL, GEMINI_API_KEY)
    

    print(f"DEBUG - User message: {user_message}")
    print(f"DEBUG - Classified intent: {intent}")
    print(f"DEBUG - Sentiment: {sentiment}")
    

    state = f"intent_{intent}_hist_{len(chat_history)}_sent_{sentiment}"
    

    if intent in ['sql', 'script', 'fhir_patient']:
        chosen_action = intent
    else:
        sql_ratio = analyze_chat_history(chat_history, GEMINI_API_URL, GEMINI_API_KEY)
        epsilon = 0.1 if sql_ratio < 0.5 else 0.05
        
        chosen_action = ql_manager.choose_action_bandit(session_key, user_message, {
            "intent": intent,
            "sentiment": sentiment,
            "sql_ratio": sql_ratio
        })
        
 
        if intent == 'rag':
            chosen_action = 'rag'
    

    print(f"DEBUG - Final chosen action: {chosen_action}")
    
    bot_response = ""
    web_sources = []
    from_web = False
    
    
    if intent == 'sql':
        
        chosen_action = 'sql'
        schema_str = "\n".join([f"{tbl['table']}: {', '.join(tbl['columns'])}" for tbl in schema])
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        prompt = test_prompt.format(schema=schema_str, context=context_str,user_input=user_message)
        sql = get_gemini_response(user_message, prompt, GEMINI_API_URL, GEMINI_API_KEY)
        
        if isinstance(sql, tuple):
            sql = sql[0]
        result = execute_sql_query(sql, DB_PATH)
        
        if isinstance(result, dict) and "columns" in result and "rows" in result:
            if result["rows"]:
               
                row_count = len(result["rows"])
                
                
                user_lower = user_message.lower()
                
                if any(keyword in user_lower for keyword in ["bao nhiêu", "số lượng", "tổng số", "đếm", "count"]):                   
                    if row_count == 1 and len(result["columns"]) == 1:                      
                        count_value = result["rows"][0][0]
                        if "bệnh nhân" in user_lower:
                            bot_response = f"Có tổng cộng **{count_value} bệnh nhân** thỏa mãn điều kiện."
                        elif "cuộc hẹn" in user_lower or "appointment" in user_lower:
                            bot_response = f"Có tổng cộng **{count_value} cuộc hẹn** được tìm thấy."
                        elif "bác sĩ" in user_lower or "doctor" in user_lower:
                            bot_response = f"Có tổng cộng **{count_value} bác sĩ** trong hệ thống."
                        else:
                            bot_response = f"Kết quả: **{count_value}**"
                    else:
                        bot_response = f"Tìm thấy **{row_count} kết quả** phù hợp với yêu cầu của bạn."
                elif any(keyword in user_lower for keyword in ["danh sách", "liệt kê", "hiển thị", "cho tôi xem", "tìm"]):
                    if "bệnh nhân" in user_lower:
                        bot_response = f"🏥 **Danh sách {row_count} bệnh nhân:**\n\n"
                    elif "bác sĩ" in user_lower:
                        bot_response = f"👨‍⚕️ **Danh sách {row_count} bác sĩ:**\n\n"
                    elif "cuộc hẹn" in user_lower or "appointment" in user_lower:
                        bot_response = f"📅 **Danh sách {row_count} cuộc hẹn:**\n\n"
                    else:
                        bot_response = f"📋 **Danh sách {row_count} kết quả:**\n\n"
                    
                    for i, row in enumerate(result["rows"][:10], 1):  
                        row_parts = []
                        for j, (col, value) in enumerate(zip(result["columns"], row)):
                            if value is not None and str(value).strip():
                                if "name" in col.lower() or "tên" in col.lower():
                                    row_parts.insert(0, f"**{value}**") 
                                elif "id" in col.lower():
                                    row_parts.append(f"ID: `{value}`")
                                elif "date" in col.lower() or "ngày" in col.lower():
                                    row_parts.append(f"📅 {value}")
                                elif "email" in col.lower():
                                    row_parts.append(f"📧 {value}")
                                elif "phone" in col.lower() or "điện thoại" in col.lower():
                                    row_parts.append(f"📞 {value}")
                                elif "address" in col.lower() or "địa chỉ" in col.lower():
                                    row_parts.append(f"🏠 {value}")
                                elif "gender" in col.lower() or "giới tính" in col.lower():
                                    gender_emoji = "👨" if str(value).lower() in ["male", "nam", "m"] else "👩"
                                    row_parts.append(f"{gender_emoji} {value}")
                                else:
                                    row_parts.append(f"{col}: {value}")
                        
                        if row_parts:
                            bot_response += f"{i}. {' • '.join(row_parts)}\n"
                    
                    if row_count > 10:
                        bot_response += f"\n➕ *Và {row_count - 10} kết quả khác...*"
                        
                else:
                    bot_response = f"📊 **Kết quả truy vấn** ({row_count} dòng):\n\n"
                    

                    headers = result["columns"]
                    
                    if row_count <= 5:
                        bot_response += "| " + " | ".join(headers) + " |\n"
                        bot_response += "|" + "|".join([" --- " for _ in headers]) + "|\n"
                        
                        for row in result["rows"]:
                            row_cells = []
                            for cell in row:
                                if cell is None:
                                    row_cells.append(" ")
                                else:
                                    cell_str = str(cell)
                                    if len(cell_str) > 30:
                                        cell_str = cell_str[:27] + "..."
                                    row_cells.append(cell_str)
                            bot_response += "| " + " | ".join(row_cells) + " |\n"
                    else:                      
                        bot_response += "🔝 **5 kết quả đầu tiên:**\n\n"
                        
                        for i, row in enumerate(result["rows"][:5], 1):
                            bot_response += f"**#{i}**\n"
                            for col, value in zip(headers, row):
                                if value is not None:
                                    bot_response += f"  • **{col}**: {value}\n"
                            bot_response += "\n"
                        
                        bot_response += f"➕ *Và {row_count - 5} kết quả khác...*"
                
                
                bot_response += f"\n\n---\n� **SQL đã thực thi:**\n```sql\n{sql}\n```"
                
            else:
                bot_response = f"❌ **Không tìm thấy dữ liệu** phù hợp với yêu cầu của bạn.\n\n---\n� **SQL đã thực thi:**\n```sql\n{sql}\n```"
        else:
            bot_response = result if result else "Không có kết quả nào phù hợp với truy vấn của bạn."
    elif intent == 'script':
        chosen_action = 'script'
        bot_response = handle_script_message(user_message)
    elif chosen_action == 'rag' or intent == 'rag':
        rag_result = rag_chat(user_message)
        
        
        rag_no_result = False
        
        if isinstance(rag_result, dict):
            answer = rag_result.get("answer", "")
            
            if (not answer or 
                any(phrase in answer.lower() for phrase in [
                    "không tìm thấy", "không có thông tin", 
                    "không cung cấp", "không chứa", "không liên quan",
                    "dữ liệu tham chiếu không", "dữ liệu không", 
                    "không có dữ liệu", "không có trong", "không đề cập"
                ])):
                rag_no_result = True
        else:
            answer = str(rag_result)
            
            if (not answer or 
                any(phrase in answer.lower() for phrase in [
                    "không tìm thấy", "không có thông tin", 
                    "không cung cấp", "không chứa", "không liên quan",
                    "dữ liệu tham chiếu không", "dữ liệu không", 
                    "không có dữ liệu", "không có trong", "không đề cập"
                ])):
                rag_no_result = True
        
        
        time_sensitive_keywords = ["hiện tại", "hôm nay", "gần đây", "tuần này", "tháng này", "năm nay", 
                                "thời sự", "tin tức", "cập nhật", "mới nhất"]
        
        if any(keyword in user_message.lower() for keyword in time_sensitive_keywords):
            if any(phrase in answer.lower() for phrase in ["không cập nhật", "không có dữ liệu thời gian thực"]):
                rag_no_result = True
        
        
        if rag_no_result:
            try:
                
                print(f"RAG không tìm thấy kết quả. Chuyển sang tìm kiếm web cho: {user_message}")
                
                
                search_results = search_web(user_message, num_results=5, serper_api_key=SERPER_API_KEY)
                web_response = generate_web_search_response(
                    user_message, 
                    GEMINI_API_URL, 
                    GEMINI_API_KEY, 
                    search_results
                )
                
                if isinstance(web_response, dict) and "answer" in web_response:                  
                    bot_response = web_response["answer"]
                    web_sources = web_response.get("web_sources", [])
                    from_web = True
                    
                    print(f"Tìm kiếm web thành công cho: {user_message}")
                else:
                    
                    if isinstance(rag_result, dict):
                        bot_response = rag_result.get("answer", "")
                    else:
                        bot_response = str(rag_result)
                    web_sources = []
                    from_web = False
            except Exception as e:
                
                print(f"Lỗi khi tìm kiếm web: {str(e)}")
                
                if isinstance(rag_result, dict):
                    bot_response = rag_result.get("answer", "")
                else:
                    bot_response = str(rag_result)
                web_sources = []
                from_web = False
        else:
            
            if isinstance(rag_result, dict):
                bot_response = rag_result.get("answer", "")
                web_sources = rag_result.get("sources", [])
            else:
                bot_response = str(rag_result)
                web_sources = []
            from_web = False
    elif chosen_action == 'web_search':
        
        try:
            search_results = search_web(user_message, num_results=5, serper_api_key=SERPER_API_KEY)
            web_response = generate_web_search_response(
                user_message, 
                GEMINI_API_URL, 
                GEMINI_API_KEY, 
                search_results
            )
            
            if isinstance(web_response, dict) and "answer" in web_response:
                bot_response = web_response["answer"]
                web_sources = web_response.get("web_sources", [])
                from_web = True
            else:
                bot_response = "Không thể tìm kiếm thông tin trên web."
        except Exception as e:
            bot_response = f"Lỗi khi tìm kiếm web: {str(e)}"
    else:
        
        chosen_action = 'gemini'
        bot_response = get_gemini_response(user_message, GEMINI_API_URL, GEMINI_API_KEY)
  
    
    response_time = time.time() - start_time
    
    
    response_quality = ql_manager.calculate_response_quality(user_message, bot_response, response_time)
    
    
    reward = response_quality  
    
    # Cập nhật Q-Learning
    ql_manager.update_bandit(session_key, chosen_action, reward, user_message, response_quality)
  
    
    chat_history.append({
        'message': user_message,
        'is_user': True,
        'sentiment': sentiment,
        'action': chosen_action,
        'response_time': response_time
    })
    chat_history.append({
        'message': bot_response,
        'is_user': False,
        'sentiment': None,
        'quality_score': response_quality
    })
    session_data["chat_history"] = chat_history
    session_data["message_count"] = len(chat_history)
    save_chat_sessions(session_key, session_data, DB_PATH)
    request.session["session_key"] = session_key

    return JSONResponse({
        'response': bot_response,
        'sentiment': sentiment,
        'action': chosen_action,
        'quality_score': response_quality,
        'response_time': response_time
    })

@router.post("/new_chat/")
async def new_chat(request: Request):
    session_key = str(random.randint(100000, 999999))
    
    save_chat_sessions(session_key, {"chat_history": [], "message_count": 0}, DB_PATH)
    request.session["session_key"] = session_key
    return JSONResponse({"status": "success", "session_key": session_key})

@router.post("/delete_chat/")
async def delete_chat(data: DeleteSession, request: Request):
    session_key_to_delete = data.session_key
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Sessions WHERE session_key = ?", (session_key_to_delete,))
    conn.commit()
    conn.close()
    
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


@router.get("/qlearning/stats/{session_id}")
async def get_qlearning_stats(session_id: str):
    """Lấy thống kê Q-Learning cho một session"""
    stats = ql_manager.get_session_stats(session_id)
    return JSONResponse({"session_stats": stats})

@router.get("/qlearning/overall_stats")
async def get_overall_qlearning_stats():
    """Lấy thống kê Q-Learning tổng quan"""
    stats = ql_manager.get_overall_stats()
    return JSONResponse({"overall_stats": stats})

@router.get("/qlearning/bandit_values/{session_id}")
async def get_bandit_values(session_id: str):
    """Lấy giá trị các arms của bandit cho session"""
    bandit = ql_manager.get_or_create_bandit(session_id)
    return JSONResponse({
        "bandit_values": bandit.values,
        "bandit_counts": bandit.counts
    })