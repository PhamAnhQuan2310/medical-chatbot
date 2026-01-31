"""
Rule-based Drug Classifier (Vietnamese + English)
-------------------------------------------------
Tự động phân loại thuốc vào các nhóm chuyên khoa:

- "da"      : da liễu
- "mat"     : mắt / nhãn khoa
- "ho_hap"  : hô hấp / phổi
- "rang"    : nha khoa
- "unknown" : không xác định

Dùng cho RAG + gợi ý thuốc theo chuyên khoa.
"""

import sqlite3
from pathlib import Path

# Database 
DB_PATH = Path(__file__).resolve().parents[1] / "Data" / "Data.db"


# Bộ rule phân loại type thuốc 

def classify_drug_type(text: str) -> str:
    """Phân loại thuốc dựa trên search_indication."""

    if not text:
        return "unknown"

    t = text.lower()

    # Thuốc mắt
    eye_keywords = [

        "mắt", "nhãn khoa", "giác mạc", "kết mạc", "thị lực",
        "viêm kết mạc", "viêm màng bồ đào", "đỏ mắt", "ngứa mắt", "khô mắt",
        "chảy nước mắt", "phù hoàng điểm",

        "eye", "ocular", "ophthalmic", "ophthalmology",
        "conjunctivitis", "retina", "macula", "uveitis",
        "glaucoma", "optic nerve", "visual"
    ]
    if any(k in t for k in eye_keywords):
        return "mat"

    # Thuốc da liễu
    skin_keywords = [

        "da liễu", "viêm da", "mụn", "mụn mủ", "mụn trứng cá",
        "vảy nến", "eczema", "nấm da", "ngứa da", 
        "hắc lào", "lang ben", "viêm da cơ địa", "tổ đỉa",

        "skin", "dermatitis", "eczema", "psoriasis", 
        "rash", "itching", "fungal infection", "topical",
        "ringworm", "athlete's foot", "derma"
    ]
    if any(k in t for k in skin_keywords):
        return "da"

    # Thuốc hô hấp
    lung_keywords = [
        
        "hô hấp", "phổi", "hen", "viêm phế quản", "ho", "khò khè",
        "đờm", "viêm phổi", "khó thở", "hen phế quản", "copd",

        "respiratory", "lung", "asthma", "bronchitis",
        "pneumonia", "airway", "wheezing", "breath"
    ]
    if any(k in t for k in lung_keywords):
        return "ho_hap"

    # Thuốc nha khoa
    dental_keywords = [

        "răng", "đau răng", "lợi", "nướu", "viêm nướu",
        "nha khoa", "sâu răng", "áp xe răng", "viêm lợi",

        "dental", "tooth", "teeth", "gum", "gingivitis",
        "periodontal", "oral infection"
    ]
    if any(k in t for k in dental_keywords):
        return "rang"

    return "unknown"


# Auto update drug types in DB

def update_all_drug_types():
    """
    Chạy 1 lần để:
    - Tự thêm cột `type` nếu chưa có
    - Phân loại toàn bộ thuốc hiện có
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(drugs)")
    cols = [col[1] for col in cur.fetchall()]
    if "type" not in cols:
        cur.execute("ALTER TABLE drugs ADD COLUMN type TEXT")

    # Lấy toàn bộ thuốc
    cur.execute("SELECT id, search_indication FROM drugs")
    rows = cur.fetchall()

    updated_count = 0

    for r in rows:
        sid = r["search_indication"] or ""
        drug_type = classify_drug_type(sid)

        cur.execute("UPDATE drugs SET type = ? WHERE id = ?", (drug_type, r["id"]))
        updated_count += 1

    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "message": f"Updated {updated_count} drugs with type classification."
    }
