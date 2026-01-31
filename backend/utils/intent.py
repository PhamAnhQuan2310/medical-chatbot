import requests
import re
from chat_routes.Scripts import is_script_message

def classify_intent(user_message):
    user_message_lower = user_message.lower().strip()
    
    
    if is_script_message(user_message):
        return 'script'
        
    
    if re.search(r"(thông tin|profile|chi tiết).*bệnh nhân.*id là \d+", user_message_lower):
        return 'fhir_patient'
    if re.search(r"bệnh nhân.*id là \d+", user_message_lower):
        return 'fhir_patient'
    
    sql_keywords = [
    'danh sách', 'tổng số', 'số lượng', 'liệt kê', 'thống kê', 'đếm',
    'giới tính', 'địa chỉ', 'hiển thị', 'cho tôi xem',
    'cao nhất', 'thấp nhất', 'trung bình', 'max', 'min', 'average', 'sum', 'count', 'vẽ',
    'bảng', 'dữ liệu', 'database', 'cơ sở dữ liệu', 'select', 'from', 'where', 'group by', 'order by',
    'truy vấn', 'query', 'sql', 'lấy dữ liệu', 'xuất dữ liệu', 'báo cáo', 'report'
    ]
    
   
    if any(keyword in user_message_lower for keyword in sql_keywords):
        return 'sql'
    
 
    return None

def classify_intent_gemini(user_message, GEMINI_API_URL, GEMINI_API_KEY, language="en"):
    prompt = (
        "Classify the user's intent into one of the following categories: "
        "sql, rag,  script. "
        "Return only the category name. "
        "script: greeting, small talk, introduction, help requests. "
        "sql: queries about data, counting, listing, statistics. "
        "rag: questions about specific information or knowledge. "
        f"User message: {user_message}"
    )
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", json=data, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        intent = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip().lower()
        if intent in ['sql', 'rag',  'script']:
            return intent
        return 'rag'
    except Exception:
        return 'rag'

def classify_intent_combined(user_message, GEMINI_API_URL=None, GEMINI_API_KEY=None, language="en"):
    intent = classify_intent(user_message)
    print(f"DEBUG - Rule-based intent: {intent}")
    if intent is not None:
        return intent
    if GEMINI_API_URL and GEMINI_API_KEY:
        gemini_intent = classify_intent_gemini(user_message, GEMINI_API_URL, GEMINI_API_KEY, language)
        print(f"DEBUG - Gemini intent: {gemini_intent}")
        return gemini_intent
    return 'rag'