import torch
import logging
import os
import traceback
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from typing import Dict, Any
import re

logger = logging.getLogger(__name__)

class QwenMedicalHandler:
    def __init__(self, model_dir: str):
        """
        Initialize Qwen2.5 medical chatbot handler
        
        Args:
            model_dir: Directory chứa base model và LoRA adapter
        """
        self.model_dir = model_dir
        self.base_model_path = os.path.join(model_dir, "qwen2.5-0.5B-Instruct")
        self.lora_model_path = os.path.join(model_dir, "qwen-medical-lora")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
       
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        
        
        self.max_length = 256
        self.max_new_tokens = 120
        self.temperature = 0.3
        self.top_p = 0.85
        self.top_k = 40
        self.do_sample = True

        """
        # Độ dài tối đa của đầu vào (bao gồm prompt và context)
        self.max_length = 256

        # Giới hạn số lượng token mới mà mô hình được phép sinh ra
        # => tránh sinh quá dài hoặc lặp vô hạn
        self.max_new_tokens = 120

        # Nhiệt độ điều khiển độ ngẫu nhiên của mô hình (0.0–1.0)
        # - Thấp (≈0.2–0.3): câu trả lời ổn định, ít ngẫu nhiên
        # - Cao (>0.8): câu trả lời đa dạng, có thể lạc chủ đề
        self.temperature = 0.3

        # Top-p sampling (nucleus sampling): chỉ lấy nhóm token có tổng xác suất <= top_p
        # => giúp giảm rủi ro chọn từ quá hiếm, nhưng vẫn giữ tính tự nhiên
        self.top_p = 0.85

        # Top-k sampling: chỉ xét k token có xác suất cao nhất để chọn tiếp theo
        # => giới hạn không gian tìm kiếm, giảm nhiễu
        self.top_k = 40

        # Bật chế độ sampling (ngẫu nhiên)
        # - Nếu False: mô hình luôn chọn token xác suất cao nhất (greedy decoding)
        # - Nếu True: chọn token theo xác suất có trọng số (đa dạng hơn)
        self.do_sample = True

        """
        
        logger.info(f"🔧 QwenMedicalHandler initialized with device: {self.device}")
        logger.info(f"📦 Base model: {self.base_model_path}")
        logger.info(f"🔧 LoRA adapter: {self.lora_model_path}")
    
    def load_model(self) -> bool:
        """Load base model và LoRA adapter"""
        try:
            logger.info("🚀 Starting Qwen2.5 + LoRA model loading...")
            
            
            if not os.path.exists(self.base_model_path):
                logger.error(f"❌ Base model path không tồn tại: {self.base_model_path}")
                return False
            
            if not os.path.exists(self.lora_model_path):
                logger.warning(f"⚠️ LoRA adapter path không tồn tại: {self.lora_model_path}")
                logger.info("📝 Will use base model only")
            
           
            logger.info("📝 Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_path,
                trust_remote_code=True,
                local_files_only=True
            )
            
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                logger.info("🔧 Set pad_token = eos_token")
            
            
            logger.info("🤖 Loading base model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True,
                local_files_only=True
            )
            
           
            if os.path.exists(self.lora_model_path):
                logger.info("🔧 Loading LoRA adapter...")
                self.model = PeftModel.from_pretrained(
                    self.model,
                    self.lora_model_path,
                    local_files_only=True
                )
                
               
                logger.info("🔄 Merging LoRA weights...")
                self.model = self.model.merge_and_unload()
                logger.info("✅ LoRA weights merged successfully")
            
            self.model.eval()
            
            if not torch.cuda.is_available():
                self.model.to(self.device)
            
            self.is_loaded = True
            
            logger.info("✅ Qwen2.5 model loaded successfully!")
            logger.info(f"📊 Model info: {self.get_model_info()}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Model loading error: {str(e)}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self.is_loaded = False
            return False
    
    def _format_medical_prompt(self, query: str) -> str:
        """Format prompt tối ưu cho medical QA"""
        return (
            f"Câu hỏi y tế: {query}\n"
            "Trả lời ngắn gọn, chính xác về:\n"
            "- Nguyên nhân có thể\n"
            "- Triệu chứng chính\n"
            "- Cách xử lý cơ bản\n"
            "- Khi nào cần gặp bác sĩ\n"
            "Trả lời:"
        )
    
    def generate_response(self, query: str) -> Dict[str, Any]:
        """Generate response với optimized parameters cho medical domain"""
        try:
            if not self.is_model_loaded():
                return {
                    "success": False,
                    "response": "Model chưa được load.",
                    "error": "Model not loaded",
                    "model_type": "qwen_medical"
                }

            logger.info(f"🤖 Generating response for: {query[:50]}...")

            
            prompt = self._format_medical_prompt(query)
            logger.info(f"📝 Using prompt length: {len(prompt)}")

          
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=self.max_length,
                truncation=True,
                padding=False
            ).to(self.device)

            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    min_new_tokens=20,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    top_k=self.top_k,
                    do_sample=self.do_sample,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.15,
                    length_penalty=0.8,
                    early_stopping=True,
                    no_repeat_ngram_size=3
                )

            
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
           
            if full_response.startswith(prompt):
                response = full_response[len(prompt):].strip()
            else:
                response = full_response.strip()

            response = self._post_process_medical_response(response)

            logger.info(f"✅ Generated clean response: {response[:80]}...")

            return {
                "success": True,
                "response": response,
                "model_type": "qwen_medical",
                "input_length": inputs['input_ids'].shape[1],
                "output_length": outputs[0].shape[0]
            }

        except Exception as e:
            logger.error(f"❌ Generation error: {str(e)}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "response": "Có lỗi xảy ra khi tạo phản hồi. Vui lòng thử lại.",
                "error": str(e),
                "model_type": "qwen_medical"
            }
    
    def _post_process_medical_response(self, response: str) -> str:
        """Clean và format medical response với formatting đẹp"""
        if not response or len(response.strip()) < 10:
            return "Vui lòng đặt câu hỏi y tế cụ thể để được tư vấn tốt hơn."
        
       
        noise_patterns = [
            r'🧠.*?$',  
            r'Hỏi tôi thêm.*?$',
            r'trao đổi ý kiến.*?$',
            r'bài viết.*?$',
            r'Để biết thêm.*?$',
            r'xem thêm.*?$',
            r'Đừng quên.*?$',
            r'chính xác và hữu ích.*?$',
            r'X\s*$',  
            r'\s*\?\s*$' 
        ]
        
        for pattern in noise_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE | re.MULTILINE)
        
       
        response = ' '.join(response.split())
        
        
        formatted_response = self._structure_medical_response(response)
        
        return formatted_response

    def _structure_medical_response(self, text: str) -> str:
        """Structure medical response với format đẹp"""
        
        sentences = re.split(r'[.!?]+', text)
        clean_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10: 
                continue
                
            # Skip noise keywords
            noise_keywords = ['hỏi tôi', 'bài viết', 'trao đổi', 'xem thêm', 'để biết thêm']
            if any(keyword in sentence.lower() for keyword in noise_keywords):
                continue
            
            clean_sentences.append(sentence)
            
            if len(clean_sentences) >= 6:  
                break
        
        if not clean_sentences:
            return "Tình trạng này cần được đánh giá bởi bác sĩ để có chẩn đoán và điều trị phù hợp."
        
       
        result_parts = []
        bullet_items = []
        current_paragraph = []
        
        for sentence in clean_sentences:
            sentence = sentence.strip()
            
            
            if self._is_list_item(sentence):
                bullet_items.append(f"• {sentence}")
            else:
                
                if bullet_items:
                    result_parts.extend(bullet_items)
                    bullet_items = []
                
                
                current_paragraph.append(sentence)
        
        
        if current_paragraph:
            paragraph_text = '. '.join(current_paragraph) + '.'
            result_parts.insert(0, paragraph_text)  
        
        if bullet_items:
            result_parts.extend(bullet_items)
        
        
        if not result_parts:
            return "Tình trạng này cần được đánh giá bởi bác sĩ để có chẩn đoán và điều trị phù hợp."
        
        formatted_result = []
        for i, part in enumerate(result_parts):
            if part.startswith('•'):
                formatted_result.append(part)
            else:
                if i > 0:  
                    formatted_result.append('\n' + part)
                else:
                    formatted_result.append(part)
        
        final_result = '\n'.join(formatted_result)
        
       
        final_result = re.sub(r'\n\s*\n\s*\n', '\n\n', final_result)  
        final_result = final_result.strip()
        
        return final_result

    def _is_list_item(self, sentence: str) -> bool:
        """Check if sentence có thể là list item"""
        sentence_lower = sentence.lower()
        
        
        list_indicators = [
            'nguyên nhân', 'triệu chứng', 'dấu hiệu', 'biện pháp', 'cách xử lý',
            'khi nào', 'nên', 'không nên', 'tránh', 'thực hiện', 'sử dụng',
            'viêm', 'nhiễm', 'bệnh', 'thuốc', 'điều trị'
        ]
        
        
        if (sentence_lower.startswith(('nếu', 'khi', 'với', 'trong trường hợp', 'có thể')) or
            any(indicator in sentence_lower for indicator in list_indicators)):
            return True
        
        
        if len(sentence) < 80 and any(indicator in sentence_lower for indicator in list_indicators):
            return True
        
        return False
    
    def _format_bullet_points(self, text: str) -> str:
        """Format bullet points với xuống dòng đúng cách"""
       
        bullet_patterns = [
            (r'(\d+)\.\s*([^\.]+)', r'\n• \2'), 
            (r'[\-\*]\s*([^\.]+)', r'\n• \1'), 
            (r'([A-Za-z][^\.]{10,})\.\s*([A-Z][^\.]{10,})', r'\1.\n• \2'), 
        ]
        
        for pattern, replacement in bullet_patterns:
            text = re.sub(pattern, replacement, text)
        
        return text

    def _format_numbered_lists(self, text: str) -> str:
        """Format numbered lists với xuống dòng"""
       
        ordinal_pattern = r'(Thứ\s+(nhất|hai|ba|tư|năm|sáu)[,\.]?\s*)'
        text = re.sub(ordinal_pattern, r'\n• ', text, flags=re.IGNORECASE)
        
       
        sequence_pattern = r'(Đầu tiên|Tiếp theo|Cuối cùng|Ngoài ra)[,\.]?\s*'
        text = re.sub(sequence_pattern, r'\n• ', text, flags=re.IGNORECASE)
        
        return text

    def _extract_clean_sentences(self, text: str) -> list:
        """Extract và clean sentences, loại bỏ noise"""
        
        parts = text.split('\n')
        clean_parts = []
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            
            if part.startswith('•'):
                clean_parts.append(part)
            else:
               
                sentences = re.split(r'[.!?]+', part)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) < 15:
                        continue
                        
                  
                    noise_keywords = ['hỏi tôi', 'bài viết', 'trao đổi', 'xem thêm', 'để biết thêm']
                    if any(keyword in sentence.lower() for keyword in noise_keywords):
                        continue
                    
                    clean_parts.append(sentence)
        
        return clean_parts[:6] 

    def _join_sentences_with_formatting(self, parts: list) -> str:
        """Join sentences với proper formatting và xuống dòng"""
        result_parts = []
        current_paragraph = []
        
        for part in parts:
            if part.startswith('•'):
                
                if current_paragraph:
                    result_parts.append('. '.join(current_paragraph) + '.')
                    current_paragraph = []
                
                result_parts.append(part)
            else:
                
                current_paragraph.append(part)
        
     
        if current_paragraph:
            result_parts.append('. '.join(current_paragraph) + '.')
        
     
        formatted_result = []
        for i, part in enumerate(result_parts):
            if part.startswith('•'):
                formatted_result.append(part)
            else:
              
                if i > 0 and not result_parts[i-1].startswith('•'):
                    formatted_result.append('\n' + part)
                else:
                    formatted_result.append(part)
        
        result = '\n'.join(formatted_result)
        
        
        result = re.sub(r'\n\s*\n', '\n\n', result)  
        result = re.sub(r'^\n+', '', result) 
        result = result.strip()
        
        return result if result else "Tình trạng này cần được đánh giá bởi bác sĩ để có chẩn đoán và điều trị phù hợp."
    
    def _clean_response(self, response: str) -> str:
        """Legacy clean method - kept for compatibility"""
        response = response.strip()
        
        if response.startswith("assistant\n"):
            response = response[10:].strip()
        
        if response.endswith("<|im_end|>"):
            response = response[:-10].strip()
        
        if response and not response.endswith(('.', '!', '?', '。')):
            response += "."
        
        return response
    
    def is_model_loaded(self) -> bool:
        """Kiểm tra model đã load chưa"""
        return (
            self.is_loaded and
            self.model is not None and
            self.tokenizer is not None
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information"""
        base_info = {
            "base_model_path": self.base_model_path,
            "lora_model_path": self.lora_model_path,
            "device": str(self.device),
            "is_loaded": self.is_loaded,
            "base_path_exists": os.path.exists(self.base_model_path),
            "lora_path_exists": os.path.exists(self.lora_model_path),
        }
        
        if not self.is_model_loaded():
            return {
                **base_info,
                "error": "Model not loaded"
            }
        
        return {
            **base_info,
            "model_type": "QwenForCausalLM + LoRA" if os.path.exists(self.lora_model_path) else "QwenForCausalLM",
            "tokenizer_type": type(self.tokenizer).__name__,
            "vocab_size": self.tokenizer.vocab_size,
            "max_length": self.max_length,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k
        }
    
    def update_generation_config(self, **kwargs):
        """Update generation parameters"""
        valid_params = {
            'max_new_tokens', 'temperature', 'top_p', 'top_k', 
            'do_sample', 'max_length'
        }
        
        updated = []
        for key, value in kwargs.items():
            if key in valid_params and hasattr(self, key):
                old_value = getattr(self, key)
                setattr(self, key, value)
                updated.append(f"{key}: {old_value} -> {value}")
                logger.info(f"🔧 Updated {key} = {value}")
            else:
                logger.warning(f"⚠️ Unknown/invalid parameter: {key}")
        
        return updated