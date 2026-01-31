import os
import google.generativeai as genai
from rag.vector_ingest import collection, model
import numpy as np
import re

GENAI_API_KEY = ""
genai.configure(api_key=GENAI_API_KEY)


def get_all_docs_and_meta():
    results = collection.get(limit=10000)
    docs = results["documents"]
    metas = results["metadatas"]
    return docs, metas


def keyword_filter(question, docs, metas, top_n=20):
    q_keywords = set(re.findall(r'\w+', question.lower()))
    scored = []
    for doc, meta in zip(docs, metas):
        doc_text = doc.lower()
        score = len(q_keywords & set(re.findall(r'\w+', doc_text)))
        scored.append((score, doc, meta))
    scored.sort(reverse=True, key=lambda x: x[0])
    filtered = [(doc, meta) for score, doc, meta in scored[:top_n] if score > 0]
    if not filtered:
        filtered = [(doc, meta) for doc, meta in zip(docs[:top_n], metas[:top_n])]
    return filtered


def query_vector_db_hybrid(question, top_k=5, keyword_top_n=20):
    docs, metas = get_all_docs_and_meta()
    filtered = keyword_filter(question, docs, metas, top_n=keyword_top_n)
    if not filtered:
        return [], []
    filtered_docs, filtered_metas = zip(*filtered)
    doc_embeddings = model.encode(list(filtered_docs))
    q_emb = model.encode([question])[0]
    sims = np.dot(doc_embeddings, q_emb) / (np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(q_emb) + 1e-8)
    top_idx = np.argsort(sims)[::-1][:top_k]
    top_docs = [filtered_docs[i] for i in top_idx]
    top_metas = [filtered_metas[i] for i in top_idx]
    return top_docs, top_metas


def build_rag_prompt(question, documents):
    context = "\n".join(documents)
    prompt = f"""Dữ liệu tham chiếu:
{context}

Câu hỏi: {question}
Trả lời dựa trên dữ liệu tham chiếu trên:"""
    return prompt


def call_gemini_api(prompt, model_name="models/gemini-2.5-flash"):
    model = genai.GenerativeModel(model_name)
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi khi gọi Gemini API: {e}"


def rag_chat(question, top_k=5, model_name="models/gemini-2.5-flash"):
    documents, metadatas = query_vector_db_hybrid(question, top_k=top_k)
    prompt = build_rag_prompt(question, documents)
    answer = call_gemini_api(prompt, model_name)
    return {
        "answer": answer,
        "sources": metadatas
    }
