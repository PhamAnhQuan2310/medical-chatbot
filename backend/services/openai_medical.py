from __future__ import annotations

import os
from typing import Optional, Dict, Any
from openai import OpenAI

OPENAI_API_KEY = ""

client = OpenAI(api_key=OPENAI_API_KEY)


def describe_diagnosis(
    diagnosis: Dict[str, Any],
    user_message: str = "",
    model: str = "gpt-4o-mini",
) -> str:
    """
    CHỈ mô tả bệnh dựa trên output model nhận diện.
    - Không khuyến cáo
    - Không hướng dẫn
    - Không nhắc "đi khám"
    - Không thêm lưu ý/cảnh báo gì
    """

    domain = str(diagnosis.get("domain", "")).strip()
    diag = str(diagnosis.get("diagnosis", "")).strip()
    conf = diagnosis.get("router_confidence", None)

    # Prompt
    prompt = f"""
Bạn là hệ thống mô tả bệnh dựa trên kết quả dự đoán từ mô hình AI.
Nhiệm vụ: CHỈ mô tả ngắn gọn bệnh/nhóm bệnh được gợi ý bởi kết quả dưới đây.
Không đưa lời khuyên, không hướng dẫn xử trí, không cảnh báo, không nhắc đi khám, không đề xuất xét nghiệm.
Viết bằng tiếng Việt, 6-10 câu, dễ hiểu.

Dữ liệu:
- domain: {domain}
- router_confidence: {conf}
- model_output: {diag}
- user_question: {user_message if user_message.strip() else "(trống)"}
""".strip()

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
            temperature=0.4,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"Lỗi OpenAI: {e}"
