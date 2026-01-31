import os
import json
import sqlite3
import random
import logging
from typing import List
import requests
import numpy as np
from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from chat_routes.chat_routes import router as chat_router
from rag.rag_files import router as rag_files_router
from utils.data_import import router as data_import_router
from rag.vector_ingest import router as vector_ingest_router
from chat_routes.chat_routes_rag import router as chat_rag_router
from workflow.api import router as workflow_router
from workflow.settings_routes import router as settings_router
from chat_routes.chat_workflow import router as chat_workflow_router
from Dashboard.dashboard_routes import router as dashboard_router
from accounts.auths import router as auth_router
from accounts.managerole import router as managerole_router
from accounts.history import router as history_router
from Guest_chat.guest_chat_routes import router as guest_chat_router
from Guest_chat.guest_history import router as guest_history_router
from rag.rag_files_thuoc import router as thuoc_ocr_router 
from chat_routes.chat_multimodal import router as chat_multimodal_router

# CHỨC NĂNG CHẨN ĐOÁN ẢNH BỆNH 
from detect.disease_router import (
    load_image_from_bytes,
    run_router,
    diagnose_chest,
    diagnose_eye,
    diagnose_skin,
    diagnose_teeth,
)

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Cấu hình FastAPI ---
app = FastAPI(
    title="Hishiro Chat API",
    description="API server for Hishiro Chat application with T5-medical model",
    version="1.0.0"
)

# THÊM HEALTH ENDPOINTS TRƯỚC KHI INCLUDE ROUTERS
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hishiro Chat API is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "database": "connected",
            "guest_chat": "available"
        },
        "timestamp": "2025-01-22T10:00:00Z"
    }

# API CHẨN ĐOÁN BỆNH TỪ ẢNH 

@app.post("/api/disease-image")
async def analyze_disease_image(file: UploadFile = File(...)):
    """
    API nhận ảnh → router → chọn model tương ứng → trả kết quả.
    """
    # 1 Kiểm tra loại file
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Vui lòng upload file hình ảnh.")

    # 2 Đọc dữ liệu bytes
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File rỗng hoặc lỗi.")

    # 3 Bytes → PIL Image
    try:
        image = load_image_from_bytes(data)
    except Exception:
        raise HTTPException(status_code=400, detail="Không đọc được file ảnh.")

    # 4 Router dự đoán domain (phổi / mắt / da / răng)
    try:
        domain, conf = run_router(image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi router: {e}")

    # 5 Gọi model tương ứng
    if domain == "chest_xray":
        diagnosis = diagnose_chest(image)
    elif domain == "retina_oct":
        diagnosis = diagnose_eye(image)
    elif domain == "skin_derm":
        diagnosis = diagnose_skin(image)
    elif domain == "teeth_cavity":
        diagnosis = diagnose_teeth(image)
    else:
        diagnosis = "Không xác định được bệnh."

    # 6 Trả JSON cho frontend
    return {
        "domain": domain,
        "router_confidence": conf,
        "diagnosis": diagnosis,
    }

# Include all routers
app.include_router(rag_files_router)
app.include_router(thuoc_ocr_router)
app.include_router(chat_router)
app.include_router(data_import_router)
app.include_router(vector_ingest_router)
app.include_router(chat_rag_router)
app.include_router(workflow_router)
app.include_router(settings_router)
app.include_router(chat_workflow_router)
app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(managerole_router)
app.include_router(history_router, prefix="/api", tags=["Chat History"])
app.include_router(
    guest_chat_router, 
    prefix="/guest-chat",
    tags=["Guest Chat"]
)

app.include_router(chat_multimodal_router)

app.include_router(
    guest_history_router,
    prefix="/api", 
    tags=["Guest History"]
)


# Cấu hình thư mục upload
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("🚀 Hishiro Chat API server is starting up...")
    logger.info("✅ All routers loaded successfully")
    logger.info("📝 Guest chat will initialize T5-medical model on first access")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks when shutting down"""
    logger.info("🛑 Hishiro Chat API server is shutting down...")

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"message": "Endpoint not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "error": str(exc)}
    )

# Run the server
if __name__ == "__main__":
    import uvicorn
    logger.info("🔥 Starting Hishiro Chat API server...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        # reload=True,
        log_level="info"
    )