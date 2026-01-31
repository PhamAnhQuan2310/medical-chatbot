import requests
import re
from openai import OpenAI


# API KEYS


# Bộ Rule

EYE = [
    "mắt", "nhãn khoa", "giác mạc", "kết mạc", "thị lực",
    "viêm kết mạc", "viêm màng bồ đào", "viêm giác mạc",
    "đỏ mắt", "ngứa mắt", "mụn lẹo", "viêm bờ mi",
    "khô mắt", "chảy nước mắt", "phù hoàng điểm",
    "thoái hóa điểm vàng",

    "eye", "ocular", "ophthalmic", "ophthalmology",
    "conjunctivitis", "retina", "retinal", "macula",
    "uveitis", "glaucoma", "optic nerve", "visual", "dry eye"
]

SKIN = [
    "da", "da liễu", "viêm da", "viêm da cơ địa",
    "mụn", "mụn mủ", "mụn đầu đen", "mụn trứng cá",
    "viêm nang lông", "nấm da", "nấm kẽ", "lang ben",
    "hắc lào", "eczema", "vảy nến", "ngứa da",
    "mụn nước", "dị ứng da", "phản ứng da",

    "skin", "dermatitis", "eczema", "psoriasis",
    "rash", "itching", "fungal infection", "derma",
    "topical", "ringworm", "athlete's foot"
]

LUNG = [
    "hô hấp", "phổi", "hen", "viêm phế quản",
    "ho", "đờm", "khò khè", "khó thở",
    "viêm phổi", "hen phế quản", "copd",
    "viêm đường hô hấp", "viêm mũi họng",

    "respiratory", "lung", "asthma", "bronchitis",
    "pneumonia", "airway", "wheezing", "breath",
    "chest congestion"
]

TEETH = [
    "răng", "đau răng", "nhức răng", "sâu răng",
    "viêm nướu", "lợi", "nướu", "viêm lợi",
    "nha khoa", "áp xe răng", "viêm chân răng",

    "dental", "tooth", "teeth", "gum", "gingivitis",
    "periodontal", "oral infection", "toothache"
]

ALL_KEYWORDS = list(set(EYE + SKIN + LUNG + TEETH))


# Clean Snippet Text

def clean_snippet(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<.*?>", "", text)
    text = text.replace("\n", " ").replace("...", " ")
    return text.strip()


# Google Search và ghép 5 Snippet lại

def search_indication_google(drug_name: str) -> str:
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": f"{drug_name} công dụng thuốc indications uses",
            "num": 5
        }

        r = requests.get(url, params=params)
        data = r.json()

        items = data.get("items")
        if not items:
            return None

        snippets = []
        for item in items[:5]:
            snippet = item.get("snippet") or item.get("htmlSnippet")
            snippet = clean_snippet(snippet)
            if snippet:
                snippets.append(snippet)

        if not snippets:
            return None

        final_text = " ".join(snippets)
        final_text = re.sub(r"\s+", " ", final_text)

        return final_text.strip()

    except Exception:
        return None



# GOOGLE FILTER: lọc từ khóa

def filter_keywords_from_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    found = []

    for kw in ALL_KEYWORDS:
        if kw in text:
            found.append(kw)

    found = list(set(found))
    return ", ".join(found) if found else ""


# API theo Key Word

def search_indication_openai(drug_name: str) -> str:

    prompt = f"""
    Hãy liệt kê NGẮN GỌN các bệnh hoặc tình trạng mà thuốc "{drug_name}"
    được dùng để điều trị.

    Yêu cầu:
    - Chỉ trả về keyword
    - Phân tách bằng dấu phẩy
    - Không mô tả dài dòng
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
        )
        return resp.choices[0].message.content.strip()

    except Exception:
        return ""



# PIPELINE TỔNG

def search_indication(drug_name: str, raw_text: str = "") -> str:
    google_text = search_indication_google(drug_name)
    kw_google = filter_keywords_from_text(google_text)
    kw_raw = filter_keywords_from_text(raw_text)

    merged = set()

    if kw_google:
        merged.update([k.strip() for k in kw_google.split(",")])

    if kw_raw:
        merged.update([k.strip() for k in kw_raw.split(",")])

    if merged:
        return ", ".join(sorted(list(merged)))

    return search_indication_openai(drug_name)
