import sqlite3
import requests
from utils.intent import classify_intent_combined

def format_table_string(columns, rows):
    
    col_widths = [max(len(str(col)), max((len(str(row[i])) for row in rows), default=0)) for i, col in enumerate(columns)]
    
    header = " | ".join(str(col).ljust(col_widths[i]) for i, col in enumerate(columns))
    sep = "-+-".join('-' * w for w in col_widths)
   
    row_lines = [" | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) for row in rows]
    return "\n".join([header, sep] + row_lines)

def execute_sql_query(query, db_path):
    try:
        query = query.strip().split(';')[0]
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        if not result:
           
            return {
                "message": "Không tìm thấy dữ liệu phù hợp với yêu cầu của bạn.",
                "sql": query
            }, True
        if len(result) == 1 and len(columns) == 1:
            return {
                "message": f"Có {result[0][0]} kết quả.",
                "sql": query
            }, True
        return {
            "columns": columns,
            "rows": [list(row) for row in result],
            "sql": query
        }, True
    except sqlite3.Error as e:
        return {"message": f"Lỗi khi thực thi SQL: {str(e)}", "sql": query}, False
    finally:
        conn.close()
def analyze_chat_history(chat_history, gemini_api_url, gemini_api_key):
    sql_count = 0
    total_messages = 0
    for message in chat_history:
        if message['is_user']:
            total_messages += 1
            intent = classify_intent_combined(message['message'], gemini_api_url, gemini_api_key)
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

def analyze_sentiment(user_input, gemini_api_url, gemini_api_key):
    sentiment_prompt = f"Analyze the sentiment of the following text and return only one word: positive, negative, or neutral. Text: {user_input}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": sentiment_prompt}]}]
    }
    try:
        response = requests.post(f"{gemini_api_url}?key={gemini_api_key}", json=data, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        sentiment = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'neutral').strip().lower()
        if sentiment not in ['positive', 'negative', 'neutral']:
            return 'neutral'
        return sentiment
    except requests.RequestException:
        return 'neutral'