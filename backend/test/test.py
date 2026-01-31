from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ..chat_routes.chatbotrag import rag_chat

app = FastAPI()

@app.post("/chat_rag/")
async def chat_rag_api(request: Request):
    try:
        data = await request.json()
        question = data.get("question")
        if not question:
            return JSONResponse({"error": "Missing question"}, status_code=400)
        result = rag_chat(question)
        return JSONResponse(result)
    except Exception as e:
        import traceback
        print("ERROR:", e)
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)