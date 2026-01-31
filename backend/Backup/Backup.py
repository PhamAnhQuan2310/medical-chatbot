import os
import json
import sqlite3
import random
import requests
import numpy as np
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# --- Cấu hình ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Đổi lại domain thực tế khi deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'Data', 'Data.db')
KB_PATH = os.path.join(BASE_DIR, 'Data', 'hospital_info.json')

GENERAL_PROMPT = {
    'vi': """
Bạn là một trợ lý AI thân thiện, cung cấp câu trả lời ngắn gọn, hữu ích bằng tiếng Việt về bệnh viện. Dựa trên thông tin được cung cấp (nếu có) và câu hỏi của người dùng, trả lời một cách tự nhiên và chính xác. Nếu không có thông tin hoặc câu hỏi không rõ, trả về: "Tôi không hiểu rõ câu hỏi của bạn. Vui lòng hỏi cụ thể hơn về bệnh viện hoặc dịch vụ y tế."
Thông tin bổ sung: {context}
Câu hỏi: {user_input}
""",
    'en': """
You are a friendly AI assistant, providing concise and helpful answers in English about hospitals. Based on the provided information (if any) and the user's question, respond naturally and accurately. If the information is insufficient or the question is unclear, return: "I don't fully understand your question. Please ask more specifically about the hospital or medical services."
Additional information: {context}
Question: {user_input}
"""
}
APPOINTMENT_PROMPT = """
Bạn là trợ lý AI giúp người dùng đặt lịch khám bệnh. 
Chỉ trả về duy nhất một trong hai trường hợp sau:
1. Nếu có đủ PatientID, ExaminerID, AppointmentDate (YYYY-MM-DD), AppointmentTime (HH:MM), trả về duy nhất một câu lệnh SQL INSERT, không giải thích, không thêm bất kỳ ký tự hoặc dòng nào khác.
2. Nếu thiếu bất kỳ thông tin nào, trả về duy nhất một câu thông báo yêu cầu đúng thông tin còn thiếu, không giải thích, không thêm ví dụ.

Ví dụ:
Câu hỏi: Đặt lịch cho bệnh nhân ID 1 với bác sĩ ID 2 vào ngày 2025-06-02 lúc 10:00
Trả lời:
INSERT INTO Appointments (PatientID, ExaminerID, AppointmentDate, AppointmentTime) VALUES (1, 2, '2025-06-02', '10:00');

Câu hỏi: Đặt lịch khám với bác sĩ Nguyễn Văn A
Trả lời:
Vui lòng cung cấp thông tin bệnh nhân và bác sĩ (bao gồm ID hoặc thông tin giúp xác định ID).

Chỉ trả về đúng một dòng kết quả, không giải thích, không thêm bất kỳ ký tự nào khác.
Câu hỏi: {user_input}
"""
DOCTOR_SEARCH_PROMPT = """
Bạn là trợ lý AI chuyên tạo câu lệnh SQL SELECT để tìm bác sĩ từ bảng Examiners. Dựa trên câu hỏi của người dùng, tạo câu lệnh SQL để tìm bác sĩ theo chuyên môn (Specialty).

- Bảng Examiners: ExaminerID (INTEGER, PRIMARY KEY), FullName (TEXT), Specialty (TEXT), PhoneNumber (TEXT, có thể NULL), Email (TEXT, có thể NULL), CreatedAt (DATETIME)
- Trả về câu lệnh SQL SELECT, không giải thích, không thêm ```sql.
- Nếu không xác định được chuyên môn, trả về: "Vui lòng cung cấp chuyên môn của bác sĩ (ví dụ: tim mạch, nội khoa)."

Ví dụ:
-- Tìm bác sĩ chuyên khoa tim mạch
SELECT FullName, Specialty FROM Examiners WHERE Specialty LIKE '%tim mạch%';

Câu hỏi: {user_input}
"""

# --- Bandit & QLearningAgent ---
class Bandit:
    def __init__(self, arms, session_key, epsilon=0.1):
        self.arms = arms
        self.epsilon = epsilon
        self.session_key = session_key
        self.counts = {arm: 0 for arm in arms}
        self.values = {arm: 0.0 for arm in arms}

    def select_action(self):
        if np.random.random() < self.epsilon:
            return np.random.choice(self.arms)
        return max(self.values, key=self.values.get)

    def update(self, action, reward):
        self.counts[action] += 1
        n = self.counts[action]
        current_value = self.values[action]
        self.values[action] = current_value + (reward - current_value) / n

    def save_state(self, session):
        if 'bandit_states' not in session:
            session['bandit_states'] = {}
        session['bandit_states'][self.session_key] = {
            'counts': self.counts,
            'values': self.values
        }

    def load_state(self, session):
        if 'bandit_states' not in session or self.session_key not in session['bandit_states']:
            return
        state = session['bandit_states'][self.session_key]
        self.counts.update(state['counts'])
        self.values.update(state['values'])

class QLearningAgent:
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.q_table = {}
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def get_q(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        qs = [self.get_q(state, a) for a in self.actions]
        max_q = max(qs)
        return self.actions[qs.index(max_q)]

    def update(self, state, action, reward, next_state):
        max_next_q = max([self.get_q(next_state, a) for a in self.actions])
        old_q = self.get_q(state, action)
        self.q_table[(state, action)] = old_q + self.alpha * (reward + self.gamma * max_next_q - old_q)

# --- Các hàm xử lý ---
def get_gemini_response(user_input, prompt):
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", json=data, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        candidates = response_data.get('candidates', [])
        if not candidates:
            return "Không có phản hồi từ bot.", False
        content = candidates[0].get('content', {})
        parts = content.get('parts', [])
        if not parts or 'text' not in parts[0]:
            return "Không có phản hồi từ bot.", False
        raw_response = parts[0]['text']
        cleaned_response = raw_response.replace("```sql", "").replace("```", "").strip()
        return cleaned_response, True
    except requests.RequestException as e:
        return f"Lỗi khi gọi Gemini API: {str(e)}", False

def execute_sql_query(query):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        if not result:
            return "Không tìm thấy dữ liệu phù hợp với yêu cầu của bạn.", True
        if len(result) == 1 and len(columns) == 1:
            return f"Kết quả: {result[0][0]}", True
        header = "| " + " | ".join(columns) + " |"
        sep = "| " + " | ".join(["---"] * len(columns)) + " |"
        rows = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in result]
        formatted_result = "\n".join([header, sep] + rows)
        return f"Kết quả truy vấn:\n{formatted_result}", True
    except sqlite3.Error as e:
        return f"Lỗi khi thực thi SQL: {str(e)}", False
    finally:
        conn.close()

def rag_retrieve(user_message):
    try:
        with open(KB_PATH, 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
        questions = [doc['question'] for doc in knowledge_base]
        vectorizer = TfidfVectorizer().fit(questions + [user_message])
        kb_vectors = vectorizer.transform(questions)
        user_vector = vectorizer.transform([user_message])
        sims = cosine_similarity(user_vector, kb_vectors)[0]
        best_idx = sims.argmax()
        if sims[best_idx] > 0.3:
            return knowledge_base[best_idx]['answer'], True
        return "", False
    except Exception as e:
        print(f"Lỗi khi truy xuất tài liệu: {str(e)}")
        return "", False

def classify_intent(user_message):
    user_message_lower = user_message.lower().strip()
    sql_keywords = [
        'danh sách', 'tổng số', 'số lượng', 'tìm', 'liệt kê', 'bao nhiêu', 'có bao nhiêu', 'thống kê', 'đếm',
        'bệnh nhân', 'bác sĩ', 'hồ sơ', 'chẩn đoán', 'ca bệnh', 'khám bệnh', 'giới tính', 'địa chỉ', 'năm', 'tháng',
        'ngày', 'tuổi', 'sinh nhật', 'địa phương', 'địa bàn', 'địa chỉ', 'địa phương', 'địa bàn', 'địa chỉ',
        'được khám', 'chưa khám', 'đã khám', 'chưa từng', 'đã từng', 'có phải', 'có đúng', 'có tồn tại', 'có trong',
        'có ở', 'có thuộc', 'có phải là', 'có phải thuộc', 'có phải ở', 'có phải có', 'có phải là', 'có phải thuộc',
        'có phải ở', 'có phải có', 'có phải là', 'có phải thuộc', 'có phải ở', 'có phải có'
    ]
    procedure_keywords = ['quy trình', 'đăng ký', 'khám bệnh', 'đặt lịch', 'thủ tục']
    medical_history_keywords = ['lịch sử bệnh', 'bệnh lý', 'chẩn đoán trước']
    greeting_keywords = ['xin chào', 'chào', 'hello', 'hi']
    thanks_keywords = ['cảm ơn', 'thank', 'thanks']
    appointment_keywords = ['đặt lịch', 'đăng ký khám', 'hẹn khám', 'lịch khám','đặt hẹn', 'đăng ký hẹn','đặt lịch hẹn']
    doctor_search_keywords = ['tìm bác sĩ', 'chuyên khoa', 'bác sĩ khoa', 'bác sĩ chuyên khoa']
    if any(keyword in user_message_lower for keyword in appointment_keywords):
        return 'appointment'
    if any(keyword in user_message_lower for keyword in greeting_keywords):
        return 'greeting'
    elif any(keyword in user_message_lower for keyword in thanks_keywords):
        return 'thanks'
    elif any(keyword in user_message_lower for keyword in procedure_keywords):
        return 'procedure'
    elif any(keyword in user_message_lower for keyword in medical_history_keywords):
        return 'medical_history'
    elif any(keyword in user_message_lower for keyword in sql_keywords):
        return 'sql'
    elif any(keyword in user_message_lower for keyword in doctor_search_keywords):
        return 'doctor_search'
    return 'general'


def classify_intent_gemini(user_message, language="en"):
    """
    Phân loại intent bằng Gemini API. Trả về: sql, appointment, doctor_search, greeting, thanks, procedure, medical_history, general
    """
    prompt = (
        "Classify the user's intent into one of the following categories: "
        "sql, appointment, doctor_search, greeting, thanks, procedure, medical_history, general. "
        "Return only the category name. "
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
        # Chỉ lấy đúng intent hợp lệ
        valid_intents = ['sql', 'appointment', 'doctor_search', 'greeting', 'thanks', 'procedure', 'medical_history', 'general']
        if intent in valid_intents:
            return intent
        return 'general'
    except Exception:
        return 'general'

def analyze_chat_history(chat_history):
    sql_count = 0
    total_messages = 0
    for message in chat_history:
        if message['is_user']:
            total_messages += 1
            intent = classify_intent_gemini(message['message'])
            if intent in ['sql', 'medical_history']:
                sql_count += 1
    sql_ratio = sql_count / total_messages if total_messages > 0 else 0
    return sql_ratio

def normalize_question(user_message):
    msg = user_message.lower()
    msg = msg.replace("bao nhiêu ca", "số lượng ca")
    msg = msg.replace("bao nhiêu bệnh nhân", "số lượng bệnh nhân")
    msg = msg.replace("liệt kê", "danh sách")
    return msg

def analyze_sentiment(user_input):
    sentiment_prompt = f"Analyze the sentiment of the following text and return only one word: positive, negative, or neutral. Text: {user_input}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": sentiment_prompt}]}]
    }
    try:
        response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", json=data, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        sentiment = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'neutral').strip().lower()
        if sentiment not in ['positive', 'negative', 'neutral']:
            return 'neutral'
        return sentiment
    except requests.RequestException:
        return 'neutral'

# --- Pydantic models ---
class Message(BaseModel):
    message: str
    session_key: str = None

class LanguageChange(BaseModel):
    language: str

class DeleteSession(BaseModel):
    session_key: str

# --- Session helpers ---
def get_chat_sessions(session_key):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT session_data FROM Sessions WHERE session_key = ?", (session_key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    else:
        return {"chat_history": [], "message_count": 0}

def save_chat_sessions(session_key, session_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    data_str = json.dumps(session_data)
    cursor.execute(
        "INSERT OR REPLACE INTO Sessions (session_key, session_data) VALUES (?, ?)",
        (session_key, data_str)
    )
    conn.commit()
    conn.close()

# --- API Endpoints ---
@app.post("/chat/")
async def handle_chat(data: Message, request: Request):
    user_message = data.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Tin nhắn trống")
    language = request.session.get("language", "vi")
    session_key = data.session_key or request.session.get("session_key")
    if not session_key:
        session_key = str(random.randint(100000, 999999))
        request.session["session_key"] = session_key

    # Lấy session_data từ DB (hoặc tạo mới nếu chưa có)
    session_data = get_chat_sessions(session_key)
    chat_history = session_data.get("chat_history", [])

    sql_ratio = analyze_chat_history(chat_history)
    epsilon = 0.1 if sql_ratio < 0.5 else 0.05
    bandit = Bandit(arms=['rag', 'gemini'], session_key=session_key, epsilon=epsilon)
    bandit.load_state(request.session)
    user_message = normalize_question(user_message)
    intent = classify_intent_gemini(user_message)
    sentiment = "neutral" 
    SQL_PROMPT = """
Bạn là một trợ lý AI chuyên tạo câu lệnh SQL SELECT để truy vấn dữ liệu từ hệ thống quản lý bệnh viện sử dụng SQLite. Dưới đây là cấu trúc các bảng:

- Bảng Patients: PatientID (INTEGER, PRIMARY KEY), FullName (TEXT), DateOfBirth (DATE, 'YYYY-MM-DD'), Gender (TEXT, 'Nam'/'Nữ'/'Khác'), PhoneNumber (TEXT, có thể NULL), Address (TEXT, có thể NULL), CreatedAt (DATETIME)
- Bảng Examiners: ExaminerID (INTEGER, PRIMARY KEY), FullName (TEXT), Specialty (TEXT), PhoneNumber (TEXT, có thể NULL), Email (TEXT, có thể NULL), CreatedAt (DATETIME)
- Bảng MedicalRecords: RecordID (INTEGER, PRIMARY KEY), PatientID (INTEGER, FOREIGN KEY), ExaminerID (INTEGER, FOREIGN KEY), ExaminationDate (DATE, 'YYYY-MM-DD'), Diagnosis (TEXT), Notes (TEXT, có thể NULL), CreatedAt (DATETIME)

Hướng dẫn:
1. Tạo câu lệnh SQL SELECT phù hợp dựa trên câu hỏi, có thể dùng WHERE, GROUP BY, HAVING, ORDER BY, DISTINCT, LIMIT, JOIN, COUNT, SUM, AVG, MIN, MAX, LIKE, IS NULL, IS NOT NULL, strftime().
2. Nếu hỏi về tháng/năm/ngày, dùng strftime('%m', ...) hoặc strftime('%Y', ...) hoặc strftime('%d', ...).
3. Nếu hỏi về giới tính, địa chỉ, bệnh lý, chẩn đoán, lọc theo trường tương ứng.
4. Nếu hỏi về thống kê, đếm, tổng hợp, dùng COUNT, SUM, AVG, GROUP BY.
5. Nếu hỏi về danh sách, liệt kê, dùng SELECT * hoặc SELECT các trường phù hợp.
6. Nếu hỏi về bệnh nhân chưa từng khám, dùng NOT IN hoặc LEFT JOIN IS NULL.
7. Nếu hỏi về bệnh nhân đã từng khám, dùng JOIN.
8. Nếu hỏi về số lượng, tổng số, bao nhiêu, dùng COUNT.
9. Nếu hỏi về các trường hợp đặc biệt, hãy cố gắng chuyển thành SQL phù hợp nhất.
10. Trả về duy nhất câu lệnh SQL, không giải thích, không thêm ```sql hoặc ký tự thừa.
11. Nếu không thể tạo SQL, trả về: "Không thể tạo câu lệnh SQL cho yêu cầu này."

Câu hỏi: {user_input}
"""
    if intent == 'sql' or intent == 'medical_history':
        bot_reply, success = get_gemini_response(user_message, SQL_PROMPT.format(user_input=user_message))
        if bot_reply.strip().upper().startswith("SELECT"):
            bot_response, sql_success = execute_sql_query(bot_reply)
            reward = 1 if sql_success else -1
        else:
            bot_response = bot_reply
            reward = -1 if not success else 0
    elif intent == 'greeting':
        bot_response = "Xin chào! Tôi có thể giúp gì cho bạn về thông tin bệnh viện?" if language == 'vi' else "Hello! How can I assist you with hospital information?"
        reward = 1
    elif intent == 'thanks':
        bot_response = "Rất vui được hỗ trợ bạn!" if language == 'vi' else "Glad to assist you!"
        reward = 2
    elif intent == 'doctor_search':
        bot_reply, success = get_gemini_response(user_message, DOCTOR_SEARCH_PROMPT.format(user_input=user_message))
        if bot_reply.strip().upper().startswith("SELECT"):
            bot_response, sql_success = execute_sql_query(bot_reply)
            reward = 1 if sql_success else -1
        else:
            bot_response = bot_reply
            reward = -1 if not success else 0
    elif intent == "appointment":
        bot_reply, success = get_gemini_response(user_message, APPOINTMENT_PROMPT.format(user_input=user_message))
        if bot_reply and bot_reply.strip().upper().startswith("INSERT INTO"):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute(bot_reply)
                conn.commit()
                bot_response = "Đặt lịch thành công!" if language == 'vi' else "Appointment booked successfully!"
                reward = 1
            except sqlite3.Error as e:
                bot_response = f"Lỗi khi đặt lịch: {str(e)}"
                reward = -1
            finally:
                conn.close()
        else:
            bot_response = bot_reply if bot_reply else ("Vui lòng cung cấp thêm thông tin." if language == 'vi' else "Please provide more information.")
            reward = -1
    else:
        action = bandit.select_action()
        if sql_ratio > 0.7:
            action = 'gemini'
        if action == 'rag':
            context, success = rag_retrieve(user_message)
            if context:
                bot_response = context
                reward = 1
            else:
                bot_response = "Tôi không hiểu rõ câu hỏi của bạn. Vui lòng hỏi cụ thể hơn về bệnh viện hoặc dịch vụ y tế." if language == 'vi' else "I don't fully understand your question. Please ask more specifically about the hospital or medical services."
                reward = -1
        else:
            context, _ = rag_retrieve(user_message)
            prompt = GENERAL_PROMPT.get(language, GENERAL_PROMPT['vi']).format(context=context, user_input=user_message)
            bot_reply, success = get_gemini_response(user_message, prompt)
            bot_response = bot_reply
            reward = 0 if success else -1
        sentiment = analyze_sentiment(user_message)
        sentiment_scores = {'positive': 1, 'neutral': 0, 'negative': -1}
        avg_sentiment = sum(sentiment_scores.get(msg['sentiment'], 0) for msg in chat_history if msg['is_user'] and msg['sentiment']) / max(len(chat_history) / 2, 1)
        long_term_reward = reward + avg_sentiment + (len(chat_history) / 10)
        bandit.update(action, long_term_reward)
        bandit.save_state(request.session)

    # Lưu lịch sử chat vào session_data
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
    save_chat_sessions(session_key, session_data)
    request.session["session_key"] = session_key

    return JSONResponse({
        'response': bot_response,
        'sentiment': sentiment
    })
@app.post("/new_chat/")
async def new_chat(request: Request):
    session_key = str(random.randint(100000, 999999))
    # Tạo session mới trong DB
    save_chat_sessions(session_key, {"chat_history": [], "message_count": 0})
    request.session["session_key"] = session_key
    return JSONResponse({"status": "success", "session_key": session_key})

@app.post("/delete_chat/")
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
        save_chat_sessions(new_session_key, {"chat_history": [], "message_count": 0})
        request.session["session_key"] = new_session_key
        return JSONResponse({'status': 'success', 'session_key': new_session_key})
    return JSONResponse({'status': 'success'})

@app.get("/chat_history/")
async def chat_history(session_key: str, request: Request):
    session_data = get_chat_sessions(session_key)
    history = session_data.get("chat_history", [])
    return JSONResponse({"chat_history": history})

@app.get("/sessions/")
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

@app.get("/get_language/")
async def get_language(request: Request):
    lang = request.session.get("language", "vi")
    return JSONResponse({"language": lang})

@app.post("/set_language/")
async def set_language(data: LanguageChange, request: Request):
    request.session["language"] = data.language
    return JSONResponse({"status": "success"})

# --- Chạy server ---
# uvicorn fastapi_app:app --reload