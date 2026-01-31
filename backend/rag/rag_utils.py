import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def rag_retrieve(user_message, kb_path):
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
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
        print(f"RAG error: {str(e)}")
        return "", False