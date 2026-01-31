import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple, List
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import os
from .qwen_handler import QwenMedicalHandler

logger = logging.getLogger(__name__)

class HybridMedicalHandler:
    def __init__(self, model_dir: str, csv_path: str):
        """
        Initialize hybrid medical handler with PhoBERT embedding
        
        Args:
            model_dir: Directory chứa Qwen model
            csv_path: Đường dẫn đến file ViMedAQA.full.csv
        """
        self.model_dir = model_dir
        self.csv_path = csv_path
        
       
        self.phobert_path = os.path.join(model_dir, "phobert-base")
        
        
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.embeddings_cache_path = os.path.join(self.data_dir, "phobert_question_embeddings.npy")
        
        
        self.qwen_handler = QwenMedicalHandler(model_dir)
        
       
        self.qa_dataset: Optional[pd.DataFrame] = None
        self.phobert_tokenizer: Optional[AutoTokenizer] = None
        self.phobert_model: Optional[AutoModel] = None
        self.question_embeddings: Optional[np.ndarray] = None
        
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
       
        self.similarity_threshold = 0.85  
        self.confidence_threshold = 0.92  
        
        logger.info("🔧 HybridMedicalHandler initialized with PhoBERT")
        logger.info(f"📦 Model dir: {model_dir}")
        logger.info(f"🤖 PhoBERT path: {self.phobert_path}")
        logger.info(f"📊 CSV path: {csv_path}")
        logger.info(f"💾 Embeddings cache: {self.embeddings_cache_path}")
        logger.info(f"⚡ Device: {self.device}")
        logger.info(f"🎯 Conservative thresholds - Similarity: {self.similarity_threshold}, Confidence: {self.confidence_threshold}")
    
    def _convert_numpy_types(self, obj: Any) -> Any:
        """Convert numpy types to Python native types for JSON serialization"""
        if isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        return obj
    
    def load_models(self) -> Dict[str, Any]:
        """Load both Qwen model and PhoBERT"""
        results = {
            "qwen_loaded": False,
            "phobert_loaded": False,
            "rule_base_loaded": False,
            "embeddings_cached": False,
            "errors": []
        }
        
        try:
            
            logger.info("🤖 Loading Qwen model...")
            results["qwen_loaded"] = self.qwen_handler.load_model()
            logger.info(f"✅ Qwen loaded: {results['qwen_loaded']}")
            
          
            logger.info("🇻🇳 Loading PhoBERT model...")
            phobert_result = self._load_phobert_model()
            results["phobert_loaded"] = phobert_result["success"]
            if not phobert_result["success"]:
                results["errors"].append(phobert_result["error"])
            logger.info(f"✅ PhoBERT loaded: {results['phobert_loaded']}")
            
            
            logger.info("📊 Loading rule-based dataset...")
            rule_result = self._load_rule_base_dataset()
            results["rule_base_loaded"] = rule_result["success"]
            results["embeddings_cached"] = rule_result.get("cached", False)
            if not rule_result["success"]:
                results["errors"].append(rule_result["error"])
            logger.info(f"✅ Rule-base loaded: {results['rule_base_loaded']}")
            logger.info(f"💾 Embeddings cached: {results['embeddings_cached']}")
            
        except Exception as e:
            error_msg = f"Error loading models: {str(e)}"
            logger.error(f"❌ {error_msg}")
            results["errors"].append(error_msg)
        
        return results
    
    def _load_phobert_model(self) -> Dict[str, Any]:
        """Load PhoBERT model and tokenizer with detailed error handling"""
        try:
            if not os.path.exists(self.phobert_path):
                error_msg = f"PhoBERT directory not found: {self.phobert_path}"
                logger.error(f"❌ {error_msg}")
                
                if os.path.exists(self.model_dir):
                    available_dirs = [d for d in os.listdir(self.model_dir) if os.path.isdir(os.path.join(self.model_dir, d))]
                    logger.info(f"📁 Available directories in {self.model_dir}: {available_dirs}")
                
                return {"success": False, "error": error_msg}
            
            
            required_files = ["config.json", "pytorch_model.bin", "tokenizer.json", "vocab.txt"]
            missing_files = []
            
            for file in required_files:
                file_path = os.path.join(self.phobert_path, file)
                if not os.path.exists(file_path):
                    missing_files.append(file)
            
            if missing_files:
                error_msg = f"Missing PhoBERT files: {missing_files}"
                logger.error(f"❌ {error_msg}")
                
                actual_files = os.listdir(self.phobert_path)
                logger.info(f"📁 Actual files in {self.phobert_path}: {actual_files}")
                
                return {"success": False, "error": error_msg}
            
            logger.info(f"📥 Loading PhoBERT from: {self.phobert_path}")
            
            
            try:
                self.phobert_tokenizer = AutoTokenizer.from_pretrained(
                    self.phobert_path,
                    local_files_only=True
                )
                logger.info("✅ PhoBERT tokenizer loaded successfully")
            except Exception as e:
                error_msg = f"Error loading PhoBERT tokenizer: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return {"success": False, "error": error_msg}
            
            try:
                self.phobert_model = AutoModel.from_pretrained(
                    self.phobert_path,
                    local_files_only=True
                )
                logger.info("✅ PhoBERT model loaded successfully")
            except Exception as e:
                error_msg = f"Error loading PhoBERT model: {str(e)}"
                logger.error(f"❌ {error_msg}")
                self.phobert_tokenizer = None
                return {"success": False, "error": error_msg}
            
           
            try:
                self.phobert_model.to(self.device)
                self.phobert_model.eval()
                
                logger.info("✅ PhoBERT model moved to device and set to eval mode")
                logger.info(f"📝 Tokenizer vocab size: {len(self.phobert_tokenizer)}")
                logger.info(f"⚡ Model on device: {next(self.phobert_model.parameters()).device}")
                
                return {"success": True, "error": None}
                
            except Exception as e:
                error_msg = f"Error moving PhoBERT to device: {str(e)}"
                logger.error(f"❌ {error_msg}")
                self.phobert_tokenizer = None
                self.phobert_model = None
                return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error loading PhoBERT: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.phobert_tokenizer = None
            self.phobert_model = None
            return {"success": False, "error": error_msg}
    
    def _get_phobert_embedding(self, text: str) -> np.ndarray:
        """Get PhoBERT embedding for text"""
        try:
            if self.phobert_model is None or self.phobert_tokenizer is None:
                logger.warning("⚠️ PhoBERT model or tokenizer not loaded")
                return np.array([])
            
           
            inputs = self.phobert_tokenizer(
                text,
                return_tensors="pt",
                max_length=256,
                truncation=True,
                padding=True
            )
            
            
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            
           
            with torch.no_grad():
                outputs = self.phobert_model(**inputs)
                embeddings = outputs.last_hidden_state[:, 0, :]  
                
            
            embedding = embeddings.cpu().numpy().flatten()
            if np.linalg.norm(embedding) > 0:
                embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Error getting PhoBERT embedding: {str(e)}")
            return np.array([])
    
    def _load_rule_base_dataset(self) -> Dict[str, Any]:
        """Load and preprocess ViMedAQA dataset with PhoBERT embeddings caching"""
        try:
            if not os.path.exists(self.csv_path):
                error_msg = f"CSV file not found: {self.csv_path}"
                logger.error(f"❌ {error_msg}")
                return {"success": False, "error": error_msg}
            
            
            logger.info(f"📖 Reading CSV from: {self.csv_path}")
            self.qa_dataset = pd.read_csv(self.csv_path)
            
            
            required_columns = ['question', 'answer']
            missing_columns = [col for col in required_columns if col not in self.qa_dataset.columns]
            
            if missing_columns:
                error_msg = f"Missing required columns: {missing_columns}"
                logger.error(f"❌ {error_msg}")
                logger.info(f"📋 Available columns: {list(self.qa_dataset.columns)}")
                return {"success": False, "error": error_msg}
            
           
            self.qa_dataset = self.qa_dataset.dropna(subset=['question', 'answer'])
            questions = self.qa_dataset['question'].astype(str).tolist()
            
            logger.info(f"📊 Processing {len(questions)} Q&A pairs...")
            logger.info(f"📝 Sample question: {questions[0][:100]}...")
            
            
            if self.phobert_model is None or self.phobert_tokenizer is None:
                logger.warning("⚠️ PhoBERT not available, skipping embedding creation")
                logger.info("💡 System will fall back to Qwen-only responses")
                return {"success": True, "error": "PhoBERT not available, fallback mode"}
            
            
            if os.path.exists(self.embeddings_cache_path):
                logger.info(f"⚡ Loading cached PhoBERT embeddings from: {self.embeddings_cache_path}")
                try:
                    self.question_embeddings = np.load(self.embeddings_cache_path)
                    logger.info(f"✅ Loaded cached embeddings with shape: {self.question_embeddings.shape}")
                    return {"success": True, "cached": True}
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load cached embeddings: {str(e)}")
                    logger.info("🔄 Will skip embedding creation (as requested)")
            else:
                logger.warning(f"⚠️ No cached embeddings found at: {self.embeddings_cache_path}")
                logger.info("💡 Please create embeddings first or system will use Qwen-only")
            
            
            return {"success": True, "cached": False, "error": "No embeddings available, Qwen-only mode"}
            
        except Exception as e:
            error_msg = f"Error loading rule-base dataset: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def _find_similar_question(self, query: str, top_k: int = 3) -> Tuple[Optional[str], float, str]:
        """Find most similar question using PhoBERT semantic similarity with stricter matching"""
        try:
            if self.phobert_model is None or self.question_embeddings is None:
                logger.warning("⚠️ PhoBERT or embeddings not available")
                return None, 0.0, ""
            
            
            logger.info("🔍 Getting PhoBERT embedding for query...")
            query_embedding = self._get_phobert_embedding(query)
            
            if query_embedding.size == 0:
                logger.error("❌ Failed to get query embedding")
                return None, 0.0, ""
            
           
            query_embedding = query_embedding.reshape(1, -1)
            similarities = cosine_similarity(query_embedding, self.question_embeddings)[0]
            
            top_indices = np.argsort(similarities)[::-1][:top_k]
            best_idx = top_indices[0]
            best_similarity = similarities[best_idx]
            
            logger.info(f"🔍 Top {top_k} PhoBERT similarities: {similarities[top_indices]}")
            
            
            if best_similarity < self.similarity_threshold:
                logger.info(f"🔍 Best similarity {best_similarity:.3f} below strict threshold {self.similarity_threshold}")
                return None, float(best_similarity), ""
            
            
            best_row = self.qa_dataset.iloc[best_idx]
            best_answer = best_row['answer']
            best_question = best_row['question']
            
            
            query_length = len(query.split())
            matched_length = len(best_question.split())
            length_ratio = min(query_length, matched_length) / max(query_length, matched_length)
            
            if length_ratio < 0.5: 
                logger.info(f"📏 Question length mismatch: {query_length} vs {matched_length} (ratio: {length_ratio:.2f})")
                return None, float(best_similarity), best_question
            
            logger.info(f"🎯 Found highly similar question (PhoBERT similarity: {best_similarity:.3f})")
            logger.info(f"📝 Question: {best_question[:100]}...")
            logger.info(f"📏 Length ratio: {length_ratio:.2f}")
            
            return best_answer, float(best_similarity), best_question
            
        except Exception as e:
            logger.error(f"❌ Error finding similar question: {str(e)}")
            return None, 0.0, ""
    
    def _evaluate_answer_quality(self, qwen_answer: str, rule_answer: str, similarity_score: float, matched_question: str, original_query: str) -> Dict[str, Any]:
        """Rebalanced answer quality evaluation - strongly favor Qwen"""
        try:
           
            qwen_length = len(qwen_answer.strip())
            rule_length = len(rule_answer.strip()) if rule_answer else 0
            
            
            qwen_score = 0.8  
            rule_score = similarity_score * 0.9  
            
            
            if 50 <= qwen_length <= 1000:  
                qwen_score += 0.15
            if 50 <= rule_length <= 500:
                rule_score += 0.1  
            
            
            if any(marker in qwen_answer for marker in ['•', '-', '1.', '2.', '\n\n']):
                qwen_score += 0.15  
            
            medical_keywords = [
                'triệu chứng', 'nguyên nhân', 'điều trị', 'chẩn đoán', 'bác sĩ', 
                'thuốc', 'bệnh', 'liều lượng', 'tác dụng phụ', 'khám', 'xét nghiệm',
                'phòng khám', 'bệnh viện', 'sức khỏe', 'y tế', 'chữa', 'uống thuốc'
            ]
            
            qwen_medical_count = sum(1 for kw in medical_keywords if kw in qwen_answer.lower())
            rule_medical_count = sum(1 for kw in medical_keywords if kw in rule_answer.lower()) if rule_answer else 0
            
            qwen_medical_density = qwen_medical_count / len(qwen_answer.split()) if qwen_answer else 0
            rule_medical_density = rule_medical_count / len(rule_answer.split()) if rule_answer else 0
            
            qwen_score += qwen_medical_density * 10  
            rule_score += rule_medical_density * 5   
            
            
            if similarity_score < 0.9:
                rule_score *= 0.7  
            
           
            if rule_answer and matched_question:
                
                query_words = set(original_query.lower().split())
                matched_words = set(matched_question.lower().split())
                word_overlap = len(query_words & matched_words) / len(query_words | matched_words)
                
                if word_overlap < 0.3: 
                    rule_score *= 0.5  
                    logger.info(f"📝 Low word overlap: {word_overlap:.2f} - penalizing rule-based")
            
            
            decision_reason = ""
            selected_answer = qwen_answer  
            selected_source = "qwen"
            
            if rule_answer:
               
                if (similarity_score > self.confidence_threshold and 
                    rule_score > qwen_score + 0.6 and  
                    similarity_score > 0.9):  
                    
                    selected_answer = rule_answer
                    selected_source = "rule_based"
                    decision_reason = f"Exceptional PhoBERT similarity: {similarity_score:.3f} with significant quality advantage"
                    
                elif similarity_score > 0.95 and rule_score > qwen_score + 0.3: 
                    selected_answer = rule_answer
                    selected_source = "rule_based"
                    decision_reason = f"Near-identical question match: {similarity_score:.3f}"
                    
                else:
                    
                    decision_reason = f"Qwen preferred: better flexibility and context (PhoBERT sim: {similarity_score:.3f}, scores: Q={qwen_score:.3f}, R={rule_score:.3f})"
            else:
                decision_reason = f"Qwen only: no suitable PhoBERT match (similarity: {similarity_score:.3f})"
            
            
            result = {
                "selected_answer": selected_answer,
                "selected_source": selected_source,
                "decision_reason": decision_reason,
                "qwen_score": float(qwen_score),
                "rule_score": float(rule_score),
                "similarity_score": float(similarity_score),
                "qwen_length": int(qwen_length),
                "rule_length": int(rule_length),
                "matched_question": matched_question if matched_question else None
            }
            
            return self._convert_numpy_types(result)
            
        except Exception as e:
            logger.error(f"❌ Error evaluating answer quality: {str(e)}")
            return {
                "selected_answer": qwen_answer,
                "selected_source": "qwen",
                "decision_reason": f"Evaluation error, defaulting to Qwen: {str(e)}",
                "qwen_score": 0.8,
                "rule_score": 0.0,
                "similarity_score": 0.0
            }
    
    def generate_response(self, query: str) -> Dict[str, Any]:
        """Generate hybrid response with strong Qwen preference"""
        try:
            logger.info(f"🎯 Hybrid processing (Qwen-preferred): {query[:50]}...")
            
            
            logger.info("🤖 Getting Qwen response...")
            qwen_result = self.qwen_handler.generate_response(query)
            
            if not qwen_result["success"]:
                logger.error("❌ Qwen failed, fallback to PhoBERT rule-based only")
                rule_answer, similarity, matched_question = self._find_similar_question(query)
                
                
                if rule_answer and similarity > 0.9:
                    return self._convert_numpy_types({
                        "success": True,
                        "response": rule_answer,
                        "source": "rule_based_fallback",
                        "similarity_score": similarity,
                        "matched_question": matched_question,
                        "qwen_error": qwen_result.get("error"),
                        "decision_reason": "Qwen failed, using high-confidence PhoBERT match"
                    })
                else:
                    return {
                        "success": False,
                        "response": "Xin lỗi, không thể xử lý câu hỏi của bạn. Vui lòng thử lại.",
                        "error": "Qwen failed and no high-confidence rule-based match available"
                    }
            
            qwen_answer = qwen_result["response"]
            
           
            logger.info("🇻🇳 Getting PhoBERT semantic rule-based response...")
            rule_answer, similarity, matched_question = self._find_similar_question(query)
            
            
            logger.info("⚖️ Evaluating answer quality (Qwen-preferred)...")
            evaluation = self._evaluate_answer_quality(qwen_answer, rule_answer, similarity, matched_question, query)
            
            
            final_response = {
                "success": True,
                "response": evaluation["selected_answer"],
                "source": evaluation["selected_source"],
                "decision_reason": evaluation["decision_reason"],
                "qwen_answer": qwen_answer,
                "rule_answer": rule_answer,
                "matched_question": matched_question,
                "similarity_score": evaluation["similarity_score"],
                "quality_scores": {
                    "qwen": evaluation["qwen_score"],
                    "rule": evaluation["rule_score"]
                },
                "model_info": {
                    **qwen_result.get("model_info", {}),
                    "semantic_model": "PhoBERT-base" if self.phobert_model else "None",
                    "device": str(self.device),
                    "phobert_available": self.phobert_model is not None,
                    "embeddings_cached": os.path.exists(self.embeddings_cache_path),
                    "bias": "qwen_preferred"
                }
            }
            
            logger.info(f"✅ Final decision: {evaluation['selected_source']} - {evaluation['decision_reason']}")
            
            
            return self._convert_numpy_types(final_response)
            
        except Exception as e:
            logger.error(f"❌ Hybrid response error: {str(e)}")
            return {
                "success": False,
                "response": "Có lỗi xảy ra trong hệ thống. Vui lòng thử lại.",
                "error": str(e)
            }
    
    def is_ready(self) -> Dict[str, bool]:
        """Check if both systems and PhoBERT are ready"""
        return {
            "qwen_ready": self.qwen_handler.is_model_loaded(),
            "phobert_ready": (
                self.phobert_model is not None and 
                self.phobert_tokenizer is not None
            ),
            "rule_base_ready": (
                self.qa_dataset is not None and 
                self.question_embeddings is not None
            ),
            "embeddings_cached": os.path.exists(self.embeddings_cache_path)
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        qwen_info = self.qwen_handler.get_model_info()
        readiness = self.is_ready()
        
        
        cache_info = {
            "cache_path": self.embeddings_cache_path,
            "cache_exists": os.path.exists(self.embeddings_cache_path),
            "cache_size_mb": 0.0,
            "cache_modified": None
        }
        
        if cache_info["cache_exists"]:
            try:
                cache_info["cache_size_mb"] = float(os.path.getsize(self.embeddings_cache_path) / 1024 / 1024)
                import datetime
                cache_info["cache_modified"] = datetime.datetime.fromtimestamp(
                    os.path.getmtime(self.embeddings_cache_path)
                ).isoformat()
            except Exception:
                pass
        
        phobert_info = {
            "model_path": self.phobert_path,
            "model_exists": os.path.exists(self.phobert_path),
            "device": str(self.device),
            "vocab_size": len(self.phobert_tokenizer) if self.phobert_tokenizer else 0,
            "is_loaded": self.phobert_model is not None
        }
        
        rule_base_info = {}
        if self.qa_dataset is not None:
            rule_base_info = {
                "dataset_size": len(self.qa_dataset),
                "csv_path": self.csv_path,
                "embeddings_shape": list(self.question_embeddings.shape) if self.question_embeddings is not None else None,
                "similarity_threshold": float(self.similarity_threshold),
                "confidence_threshold": float(self.confidence_threshold)
            }
        
        result = {
            "qwen_info": qwen_info,
            "phobert_info": phobert_info,
            "rule_base_info": rule_base_info,
            "cache_info": cache_info,
            "readiness": readiness,
            "csv_exists": os.path.exists(self.csv_path),
            "approach": "qwen_preferred_with_conservative_phobert_backup",
            "bias_settings": {
                "similarity_threshold": float(self.similarity_threshold),
                "confidence_threshold": float(self.confidence_threshold),
                "bias": "qwen_preferred"
            }
        }
        
        
        return self._convert_numpy_types(result)
    
    def update_thresholds(self, similarity_threshold: Optional[float] = None, 
                         confidence_threshold: Optional[float] = None):
        """Update PhoBERT similarity thresholds"""
        if similarity_threshold is not None:
            self.similarity_threshold = max(0.7, min(0.98, similarity_threshold)) 
            logger.info(f"🔧 Updated PhoBERT similarity_threshold = {self.similarity_threshold}")
        
        if confidence_threshold is not None:
            self.confidence_threshold = max(0.85, min(0.98, confidence_threshold)) 
            logger.info(f"🔧 Updated confidence_threshold = {self.confidence_threshold}")