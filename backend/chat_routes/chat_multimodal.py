from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, Dict, Any, List
from pathlib import Path
import sqlite3
import numpy as np
import json
from datetime import datetime

from services.embeddings import embed as get_text_embedding

from services.openai_medical import describe_diagnosis

from detect.disease_router import (
    load_image_from_bytes, run_router,
    diagnose_chest, diagnose_eye, diagnose_skin, diagnose_teeth
)

router = APIRouter(prefix="/chat", tags=["Chat - Multimodal"])

# Database
DB_PATH = Path(__file__).resolve().parents[1] / "Data" / "Data.db"

MIN_SCORE = 0.35
TOP_K = 5


# SESSION STORAGE

def _ensure_sessions_table() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Sessions (
            session_key TEXT PRIMARY KEY,
            session_data TEXT
        )
    """)
    conn.commit()
    conn.close()


def _append_history(session_key: str, msg: Dict[str, Any]) -> None:
    _ensure_sessions_table()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT session_data FROM Sessions WHERE session_key = ?", (session_key,))
    row = cur.fetchone()

    if row and row[0]:
        try:
            data = json.loads(row[0])
        except Exception:
            data = {"chat_history": []}
    else:
        data = {"chat_history": []}

    if "chat_history" not in data:
        data["chat_history"] = []

    data["chat_history"].append(msg)

    payload = json.dumps(data, ensure_ascii=False)
    cur.execute("""
        INSERT INTO Sessions(session_key, session_data)
        VALUES(?, ?)
        ON CONFLICT(session_key) DO UPDATE SET session_data=excluded.session_data
    """, (session_key, payload))

    conn.commit()
    conn.close()



# 1. Phát hiện bệnh từ ảnh

def diagnose_image_bytes(data: bytes) -> Dict[str, Any]:
    img = load_image_from_bytes(data)
    domain, conf = run_router(img)

    if domain == "chest_xray":
        text = diagnose_chest(img)
    elif domain == "retina_oct":
        text = diagnose_eye(img)
    elif domain == "skin_derm":
        text = diagnose_skin(img)
    else:
        text = diagnose_teeth(img)

    return {
        "domain": domain,
        "router_confidence": float(conf),
        "diagnosis": text,
    }



# 2. Chuẩn hóa chuỗi bệnh cho embedding

def build_query_text(domain: str, raw_diag: str) -> str:
    d = raw_diag.lower().strip()

    if domain == "skin_derm":
        return f"{d}, bệnh da liễu, viêm da, ngoài da, dermatology"
    if domain == "retina_oct":
        return f"{d}, bệnh mắt, nhãn khoa, võng mạc, retinal disease, ophthalmology"
    if domain == "chest_xray":
        return f"{d}, bệnh phổi, hô hấp, viêm phổi, đường thở"
    if domain == "teeth_cavity":
        return f"{d}, bệnh răng, nha khoa, sâu răng, viêm nướu"

    return d
# 3. FILTER thuốc theo domain

def match_domain(domain: str, drug_type: str) -> bool:
    if domain == "skin_derm":
        return drug_type == "da"
    if domain == "retina_oct":
        return drug_type == "mat"
    if domain == "chest_xray":
        return drug_type == "ho_hap"
    if domain == "teeth_cavity":
        return drug_type == "rang"
    return True



# 4) Recommendaion system by CosineSimilarity

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(np.dot(a, b) / denom)


def suggest_drugs(query_text: str, domain: str,
                  top_k: int = TOP_K, min_score: float = MIN_SCORE):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, drug_name, search_indication, type
        FROM drugs
        WHERE search_indication IS NOT NULL
          AND TRIM(search_indication) != ''
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return [], "Không có thuốc trong database."

    q_emb = get_text_embedding(query_text)

    scored = []
    seen = set()

    for r in rows:
        name = (r["drug_name"] or "").strip()
        indication = (r["search_indication"] or "").strip()
        drug_type = (r["type"] or "").strip().lower()

        # 1 Filter theo domain
        if not match_domain(domain, drug_type):
            continue

        # 2 Skip trùng tên
        if name.lower() in seen:
            continue

        # 3 Embed indication
        ind_emb = get_text_embedding(indication)
        score = cosine(q_emb, ind_emb)
        if score < min_score:
            continue

        seen.add(name.lower())
        scored.append({
            "id": r["id"],
            "drug_name": name,
            "score": float(score),
            "search_indication": indication[:500]
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    if not scored:
        return [], f"Không có thuốc phù hợp domain {domain} (min_score={min_score})."

    return scored[:top_k], f"Tìm thấy {len(scored)} thuốc phù hợp."



# 5. API

@router.post("/multimodal")
async def chat_multimodal(
    session_key: str = Form(...),
    message: str = Form(""),
    image: Optional[UploadFile] = File(None)
):
    if image is None:
        raise HTTPException(status_code=400, detail="Bạn cần gửi ảnh.")

    _append_history(session_key, {
        "message": f"[Image] {message}",
        "is_user": True,
        "timestamp": datetime.now().isoformat()
    })

    data = await image.read()
    diagnosis = diagnose_image_bytes(data)

    domain = diagnosis["domain"]
    raw_diag = diagnosis["diagnosis"]

    NORMAL_KEYWORDS = ["normal", "no finding", "clear", "healthy", "bình thường"]

    if any(k in raw_diag.lower() for k in NORMAL_KEYWORDS):
        prompt = f"""
Người dùng gửi một hình ảnh y tế.

Kết quả phân tích ảnh:
{raw_diag}

Câu hỏi của người dùng:
{message}

Hãy trả lời ngắn gọn, dễ hiểu, trấn an người dùng.
"""
        answer = describe_diagnosis({"diagnosis": prompt}, "")

        bot_payload = {
            "answer": answer,
            "diagnosis": diagnosis,
            "drug_message": "Bạn bình thường, không cần dùng thuốc.",
            "drug_suggestions": []
        }

        _append_history(session_key, {
            "message": bot_payload,
            "is_user": False,
            "timestamp": datetime.now().isoformat()
        })

        return bot_payload

    query_text = build_query_text(domain, raw_diag.lower())
    drug_suggestions, drug_message = suggest_drugs(query_text, domain)

    prompt = f"""
Người dùng gửi một hình ảnh y tế.

Kết quả phân tích ảnh:
{raw_diag}

Câu hỏi của người dùng:
{message}

Hãy trả lời như một bác sĩ, giải thích rõ ràng, dễ hiểu,
không khẳng định tuyệt đối, không chẩn đoán thay bác sĩ.
"""

    answer = describe_diagnosis({"diagnosis": prompt}, "")

    bot_payload = {
        "answer": answer,
        "diagnosis": diagnosis,
        "drug_message": drug_message,
        "drug_suggestions": drug_suggestions
    }

    _append_history(session_key, {
        "message": bot_payload,
        "is_user": False,
        "timestamp": datetime.now().isoformat()
    })

    return bot_payload
