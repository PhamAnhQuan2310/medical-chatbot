from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import easyocr
import numpy as np
import cv2
import re
import sqlite3
from pathlib import Path
from .google_ai import search_indication

# Router

router = APIRouter(
    prefix="/thuoc_ocr",
    tags=["Admin - OCR Thuoc"],
)

# EasyOCR 
reader = easyocr.Reader(['en', 'vi'], gpu=False)

# Pydantic models

class DrugDraft(BaseModel):
    drug_name: Optional[str] = None
    concentration: Optional[str] = None
    dosage_form: Optional[str] = None
    manufacturer: Optional[str] = None
    exp_date: Optional[str] = None
    indication: Optional[str] = None
    warning: Optional[str] = None
    raw_text: str
    search_indication: Optional[str] = None

class DrugRecord(BaseModel):
    drug_name: str
    concentration: Optional[str] = None
    dosage_form: Optional[str] = None
    manufacturer: Optional[str] = None
    exp_date: Optional[str] = None
    indication: Optional[str] = None
    warning: Optional[str] = None
    raw_text: str

# Database 

DB_PATH = Path(__file__).resolve().parents[1] / "Data" / "Data.db"

def init_drug_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # CREATE TABLE 
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS drugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_name   TEXT NOT NULL,
            concentration TEXT,
            dosage_form TEXT,
            manufacturer TEXT,
            exp_date    TEXT,
            indication  TEXT,
            search_indication TEXT,
            warning     TEXT,
            raw_text    TEXT,
            type        TEXT,      
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    conn.commit()
    conn.close()

init_drug_table()


# Bộ rule phân loại type thuốc

def classify_drug_type(text: str) -> str:
    if not text:
        return "unknown"

    t = text.lower()

    groups = {
        "mat": [
            "mắt", "nhãn khoa", "giác mạc", "kết mạc", "thị lực",
            "viêm kết mạc", "viêm màng bồ đào", "viêm giác mạc",
            "đỏ mắt", "ngứa mắt", "mụn lẹo", "viêm bờ mi",
            "khô mắt", "chảy nước mắt", "phù hoàng điểm",
            "thoái hóa điểm vàng",

            "eye", "ocular", "ophthalmic", "ophthalmology",
            "conjunctivitis", "retina", "retinal", "macula",
            "uveitis", "glaucoma", "optic nerve", "visual", "dry eye"
        ],

        "da": [
            "da liễu", "viêm da", "viêm da cơ địa",
            "mụn", "mụn mủ", "mụn đầu đen", "mụn trứng cá",
            "viêm nang lông", "nấm da", "nấm kẽ", "lang ben",
            "hắc lào", "eczema", "vảy nến", "ngứa da",
            "mụn nước", "dị ứng da", "phản ứng da",

            "skin", "dermatitis", "psoriasis",
            "rash", "itching", "fungal infection", "derma",
            "topical", "ringworm", "athlete's foot"
        ],

        "ho_hap": [
            "hô hấp", "phổi", "hen", "viêm phế quản",
            "ho", "đờm", "khò khè", "khó thở",
            "viêm phổi", "hen phế quản", "copd",
            "viêm đường hô hấp", "viêm mũi họng",

            "respiratory", "lung", "asthma", "bronchitis",
            "pneumonia", "airway", "wheezing", "breath",
            "chest congestion"
        ],

        "rang": [
            "răng", "đau răng", "nhức răng", "sâu răng",
            "viêm nướu", "lợi", "nướu", "viêm lợi",
            "nha khoa", "áp xe răng", "viêm chân răng",

            "dental", "tooth", "teeth", "gum", "gingivitis",
            "periodontal", "oral infection", "toothache"
        ]
    }

    # Đếm số keyword match
    scores = {}
    for drug_type, keywords in groups.items():
        scores[drug_type] = sum(1 for kw in keywords if kw in t)

    # Lấy điểm cao nhất
    max_score = max(scores.values())
    if max_score == 0:
        return "unknown"

    # Các nhóm có cùng điểm cao nhất
    tied_types = [k for k, v in scores.items() if v == max_score]

    # Ưu tiên nếu bằng điểm
    priority_order = ["ho_hap", "da", "mat", "rang"]
    for p in priority_order:
        if p in tied_types:
            return p

    # fallback 
    return tied_types[0]


NAME_BAD_KEYS = [
    "CÔNG TY", "PHARMA", "COMPANY", "HƯỚNG DẪN",
    "BẢO QUẢN", "HSD", "EXP", "NSX", "LOT", "SỐ LÔ"
]

def extract_drug_name(lines: list[str]) -> Optional[str]:
    candidates = lines[:10]

    def score(line: str) -> int:
        u = line.upper()
        if any(bad in u for bad in NAME_BAD_KEYS):
            return -100
        if sum(c.isdigit() for c in line) > 5:
            return -10

        score = 0
        if u == line.upper():
            score += 5
        if 4 <= len(line) <= 30:
            score += 5
        return score

    best = None
    best_score = -999
    for l in candidates:
        s = score(l)
        if s > best_score:
            best_score = s
            best = l

    return best.strip() if best_score > 0 else None


# bộ Rule trích các thông tin từ text đọc được

def parse_drug_info(raw_text: str) -> DrugDraft:
    text = raw_text.replace("\r", "\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    upper_text = text.upper()

    drug_name = extract_drug_name(lines)

    conc_match = re.search(
        r"\b\d+(?:[\.,]\d+)?\s*(MG|G|ML|MCG|IU|%)\b",
        upper_text
    )
    concentration = conc_match.group(0) if conc_match else None

    exp_match = re.search(
        r"(HSD|EXP|EXPIRY)[^0-9]*"
        r"(\d{2}[\/\-]\d{2}[\/\-]\d{2,4}|\d{2}[\/\-]\d{4})",
        upper_text
    )
    exp_date = exp_match.group(2) if exp_match else None

    dosage_form = None
    for line in lines:
        u = line.upper()
        if any(kw in u for kw in ["TABLET", "CAPSULE", "SUSPENSION", "SYRUP"]):
            dosage_form = line.strip()
            break

    manufacturer = None
    for line in lines:
        u = line.upper()
        if any(kw in u for kw in ["PHARMA", "JSC", "CO.,", "COMPANY", "CÔNG TY"]):
            manufacturer = line.strip()
            break

    indication = None
    for line in lines:
        u = line.upper()
        if any(kw in u for kw in ["GIẢM ĐAU", "HẠ SỐT", "KHÁNG SINH", "CHỈ ĐỊNH"]):
            indication = line.strip()
            break

    warning = None
    for line in lines:
        u = line.upper()
        if any(kw in u for kw in ["CHỐNG CHỈ ĐỊNH", "THẬN TRỌNG", "CẢNH BÁO"]):
            warning = line.strip()
            break

    return DrugDraft(
        drug_name=drug_name,
        concentration=concentration,
        dosage_form=dosage_form,
        manufacturer=manufacturer,
        exp_date=exp_date,
        indication=indication,
        warning=warning,
        raw_text=raw_text,
    )

# API 1: OCR 

@router.post("/ocr-image", response_model=DrugDraft)
async def ocr_drug_image(file: UploadFile = File(...)):
    try:
        data = await file.read()
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Ảnh không hợp lệ")

        results = reader.readtext(img, detail=0, paragraph=True)

        raw_text = "\n".join([t for t in results if t]).strip()
        if not raw_text:
            raise HTTPException(status_code=400, detail="Không đọc được văn bản từ ảnh")

        return parse_drug_info(raw_text)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR error: {e}")

# API 2: Lưu thuốc

@router.post("/save", summary="Lưu thuốc vào Data.db")
def save_drug(record: DrugRecord):
    if not record.drug_name:
        raise HTTPException(status_code=400, detail="Thiếu tên thuốc")

    # 1. Lấy công dụng bằng Google và AI
    google_indication = search_indication(record.drug_name, record.raw_text)

    # 2. Tự động phân loại thuốc bằng rule
    drug_type = classify_drug_type(google_indication)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 3. Lưu vào DB 
    cur.execute(
        """
        INSERT INTO drugs
        (drug_name, concentration, dosage_form, manufacturer, exp_date,
         indication, search_indication, warning, raw_text, type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.drug_name,
            record.concentration,
            record.dosage_form,
            record.manufacturer,
            record.exp_date,
            record.indication,
            google_indication,
            record.warning,
            record.raw_text,
            drug_type,  
        ),
    )

    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return {
        "ok": True,
        "id": new_id,
        "type": drug_type,
        "search_indication": google_indication,
    }
