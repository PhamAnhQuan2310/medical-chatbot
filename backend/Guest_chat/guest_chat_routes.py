from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import traceback
import os
from typing import Dict, Any, Optional

from .hybrid_medical_handler import HybridMedicalHandler

logger = logging.getLogger(__name__)


router = APIRouter()


hybrid_handler: Optional[HybridMedicalHandler] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    response: str
    source: Optional[str] = None  
    model_info: Optional[Dict[str, Any]] = None
    decision_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def get_or_initialize_hybrid_handler() -> HybridMedicalHandler:
    global hybrid_handler
    
    logger.info("🔄 get_or_initialize_hybrid_handler called")
    
    if hybrid_handler is None:
        logger.info("🚀 Initializing new HybridMedicalHandler...")
        
        # Đường dẫn model và CSV
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, "model")
        csv_path = os.path.join(current_dir, "data", "ViMedAQA_full.csv")
        
        logger.info(f"📦 Model directory: {model_dir}")
        logger.info(f"📊 CSV path: {csv_path}")
        
        # Kiểm tra file paths exist
        logger.info(f"🔍 Model directory exists: {os.path.exists(model_dir)}")
        logger.info(f"🔍 CSV file exists: {os.path.exists(csv_path)}")
        
        try:
            hybrid_handler = HybridMedicalHandler(model_dir, csv_path)
            
            logger.info("🔄 Attempting to load models...")
            load_results = hybrid_handler.load_models()
            logger.info(f"📊 Load results: {load_results}")
            
            readiness = hybrid_handler.is_ready()
            logger.info(f"🎯 System readiness: {readiness}")
            
        except Exception as e:
            logger.error(f"❌ Error initializing HybridMedicalHandler: {str(e)}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            hybrid_handler = HybridMedicalHandler(model_dir, csv_path)
    
    return hybrid_handler

@router.get("/initialize")
async def initialize_hybrid_system():
    try:
        logger.info("🎯 /initialize endpoint called")
        
        handler = get_or_initialize_hybrid_handler()
        
        # Kiểm tra system status
        readiness = handler.is_ready()
        system_info = handler.get_system_info()
        
        all_ready = all(readiness.values())
        
        response_data = {
            "success": all_ready,
            "message": "Hybrid Medical system đã sẵn sàng" if all_ready else "System chưa sẵn sàng hoàn toàn",
            "status": "ready" if all_ready else "partial",
            "readiness": readiness,
            "system_info": system_info
        }
        
        logger.info(f"✅ Hybrid system response: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Initialize endpoint error: {str(e)}")
        return {
            "success": False,
            "message": f"Lỗi khởi tạo system: {str(e)}",
            "status": "error",
            "error": str(e)
        }

@router.post("/chat", response_model=ChatResponse)
async def chat_with_hybrid(request: ChatRequest):
    try:
        logger.info(f"💬 Hybrid chat request: {request.message[:50]}...")
        
        handler = get_or_initialize_hybrid_handler()
        
        
        readiness = handler.is_ready()
        if not readiness["qwen_ready"] and not readiness["rule_base_ready"]:
            return ChatResponse(
                success=False,
                response="System chưa sẵn sàng. Vui lòng thử lại sau.",
                error="No subsystem ready"
            )
        
        
        logger.info("🎯 Generating hybrid response...")
        result = handler.generate_response(request.message)
        
        if result["success"]:
            logger.info(f"✅ Hybrid response success - source: {result.get('source')}")
            return ChatResponse(
                success=True,
                response=result["response"],
                source=result.get("source"),
                model_info=result.get("model_info"),
                decision_info={
                    "decision_reason": result.get("decision_reason"),
                    "similarity_score": result.get("similarity_score"),
                    "quality_scores": result.get("quality_scores")
                }
            )
        else:
            logger.error(f"❌ Hybrid response failed: {result.get('error')}")
            return ChatResponse(
                success=False,
                response=result["response"],
                error=result.get("error")
            )
            
    except Exception as e:
        logger.error(f"❌ Hybrid chat error: {str(e)}")
        return ChatResponse(
            success=False,
            response="Có lỗi xảy ra. Vui lòng thử lại sau.",
            error=str(e)
        )

@router.get("/status")
async def get_hybrid_status():
    """Get hybrid system status"""
    try:
        global hybrid_handler
        
        if hybrid_handler is None:
            return {
                "status": "not_initialized",
                "readiness": {"qwen_ready": False, "rule_base_ready": False}
            }
        
        readiness = hybrid_handler.is_ready()
        system_info = hybrid_handler.get_system_info()
        
        return {
            "status": "ready" if all(readiness.values()) else "partial",
            "readiness": readiness,
            "system_info": system_info
        }
        
    except Exception as e:
        logger.error(f"❌ Status error: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/update-thresholds")
async def update_thresholds(thresholds: Dict[str, float]):
    """Update decision thresholds"""
    try:
        handler = get_or_initialize_hybrid_handler()
        handler.update_thresholds(
            similarity_threshold=thresholds.get("similarity_threshold"),
            confidence_threshold=thresholds.get("confidence_threshold")
        )
        
        return {
            "success": True,
            "message": "Thresholds updated",
            "updated_thresholds": thresholds
        }
        
    except Exception as e:
        logger.error(f"❌ Update thresholds error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export router
guest_chat_router = router
logger.info("📋 Hybrid guest chat routes defined")