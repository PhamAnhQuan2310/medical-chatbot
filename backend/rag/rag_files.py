import os
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse

UPLOAD_DIR = os.path.join(os.path.dirname(__file__),"..", "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

@router.post("/upload_rag_files/")
async def upload_rag_files(files: List[UploadFile] = File(...)):
    saved_files = []
    print(f"Received {len(files)} files")
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        print(f"Saving file to: {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
    print(f"Saved files: {saved_files}")
    return JSONResponse({"status": "success", "files": saved_files})

@router.get("/list_rag_files/")
async def list_rag_files():
    allowed_exts = (".json", ".pdf", ".docx", ".txt", ".xlsx", ".csv")
    files = [
        f for f in os.listdir(UPLOAD_DIR)
        if f.lower().endswith(allowed_exts) and f!= "file_context.json"
    ]
    return JSONResponse({"files": files})

@router.get("/get_rag_file/")
async def get_rag_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(file_path):
        return PlainTextResponse("File not found", status_code=404)
    # Trả về text cho file text, còn lại trả về file để download
    if filename.endswith((".json", ".txt", ".csv")):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return PlainTextResponse(content)
    return FileResponse(file_path, filename=filename)