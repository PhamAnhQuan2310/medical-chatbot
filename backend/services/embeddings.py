import numpy as np
import re
from sentence_transformers import SentenceTransformer

_model = None


# Clean text trước embedding

def clean_text(text: str) -> str:
    if not text:
        return ""

    t = text.strip()

    t = t.replace("**", " ").replace("*", " ")

    t = re.sub(r"[^\w\s,.:/()-]", " ", t)

    t = re.sub(r"\s+", " ", t)

    return t.strip()


# Load medical embedding model (SapBERT)

def get_model():
    """
    Model mạnh nhất cho Embedding y tế:
    - 'cambridgeltl/SapBERT-from-PubMedBERT-fulltext'  ← Recommended
    """
    global _model
    if _model is None:
        print("🔥 Loading medical embedding model: SapBERT ...")
        _model = SentenceTransformer(
            "cambridgeltl/SapBERT-from-PubMedBERT-fulltext",
            device="cpu"   # nếu có GPU → đổi thành "cuda"
        )
    return _model


# Embedding

def embed(text: str) -> np.ndarray:
    """
    Trả về vector embedding đã L2-normalized.
    Cực kỳ quan trọng cho cosine accuracy.
    """
    if not text:
        # SapBERT dimension = 768
        return np.zeros(768, dtype=np.float32)

    text = clean_text(text)
    model = get_model()

    # Encode 
    emb = model.encode(text)

    # L2 normalize 
    norm = np.linalg.norm(emb) + 1e-12
    emb = emb / norm

    return emb.astype(np.float32)
