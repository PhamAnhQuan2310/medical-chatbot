import random
from datetime import datetime
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import numpy as np
import re

class EnhancedMLScriptHandler:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.pipeline = None
        self.confidence_threshold = 0.85  
        

        self.training_data = {
            'greeting': [
                'xin chào', 'chào bạn', 'hello', 'hi', 'hey', 
                'chào buổi sáng', 'chào buổi chiều', 'good morning', 
                'good afternoon', 'hí', 'hế lô', 'chào', 'hello there', 'hi there'
            ],
            'goodbye': [
                'tạm biệt', 'bye', 'goodbye', 'see you later', 'hẹn gặp lại',
                'chúc ngủ ngon', 'good night', 'bai bai', 'chào tạm biệt',
                'bye bye', 'see you', 'good bye'
            ],
            'thanks': [
                'cảm ơn', 'thank you', 'thanks', 'cám ơn', 'cam on',
                'cảm ơn nhiều', 'thank you so much', 'cảm ơn bạn',
                'thanks a lot', 'tks', 'thks', 'thank u'
            ],
            'help': [
                'giúp đỡ', 'help', 'hỗ trợ', 'support', 'trợ giúp',
                'làm được gì', 'có thể làm gì', 'hỗ trợ gì', 'giúp tôi',
                'hướng dẫn', 'guide', 'help me', 'cần hỗ trợ'
            ],
            'introduction': [
                'bạn là ai', 'who are you', 'tên bạn', 'your name',
                'giới thiệu', 'introduce', 'about you', 'bạn là gì',
                'what are you', 'tên gì', 'ai vậy'
            ],
            'datetime': [
                'mấy giờ', 'what time', 'bây giờ là mấy giờ', 'ngày mấy',
                'what day', 'hôm nay', 'today', 'thời gian', 'current time',
                'bây giờ', 'now', 'ngày hôm nay', 'thứ mấy', 'what date'
            ]
        }
        
   
        self.exclusion_patterns = [
          
            r'\b(bệnh|thuốc|khám|điều trị|triệu chứng|đau|sốt|ho|mệt)\b',
            r'\b(bác sĩ|bệnh viện|phòng khám|xét nghiệm|chẩn đoán)\b',
            r'\b(patient|medical|doctor|hospital|medicine|treatment)\b',
            
      
            r'\b(danh sách|thống kê|số lượng|dữ liệu|database|table)\b',
            r'\b(tìm kiếm|tra cứu|lookup|search|query|find)\b',
            r'\b(hiển thị|show|display|list|count|sum)\b',
            
         
            r'\b(tại sao|why|làm thế nào|how|như thế nào|cách nào)\b',
            r'\b(khi nào|when|ở đâu|where|ai|who|cái gì|what)\b',
            
        
            r'\b(thông tin về|information about|chi tiết|details|explain)\b',
            r'\b(id|mã|code|số)\s*\d+\b',  # IDs or codes
            r'\b\d+\b.*\b(năm|tuổi|age|year|month|ngày)\b',  # Ages/dates
        ]
        
      
        self.never_script_phrases = [
            'thông tin bệnh nhân', 'patient information', 'danh sách bệnh nhân',
            'số lượng', 'thống kê', 'báo cáo', 'report', 'analysis',
            'dữ liệu', 'database', 'truy vấn', 'query', 'tìm kiếm',
            'tra cứu', 'lookup', 'search', 'chi tiết về', 'details about',
            'giải thích về', 'explain about', 'so sánh', 'compare'
        ]
        
        self.scripts = {
            "greeting": [
                "Xin chào! Tôi là CareBot - trợ lý AI y tế thông minh. Tôi có thể giúp bạn tra cứu thông tin y tế, tìm kiếm dữ liệu bệnh nhân và trả lời các câu hỏi chuyên môn. Bạn cần hỗ trợ gì hôm nay?",
                "Chào bạn! Tôi là CareBot, có thể hỗ trợ bạn về thông tin y tế và dữ liệu bệnh nhân. Bạn muốn tìm hiểu điều gì?",
                "Xin chào! Tôi có thể giúp bạn tra cứu thông tin y tế, tìm kiếm dữ liệu và trả lời câu hỏi. Hãy cho tôi biết bạn cần gì nhé!"
            ],
            "goodbye": [
                "Tạm biệt! Chúc bạn có một ngày tốt lành và sức khỏe dồi dào!",
                "Hẹn gặp lại bạn! Đừng ngần ngại quay lại khi cần hỗ trợ về thông tin y tế.",
                "Tạm biệt và cảm ơn đã sử dụng CareBot. Chúc bạn luôn khỏe mạnh!"
            ],
            "thanks": [
                "Rất vui khi được giúp bạn! Bạn có cần hỗ trợ thêm về thông tin y tế không?",
                "Không có gì! Tôi luôn sẵn sàng hỗ trợ bạn về các vấn đề y tế.",
                "Hân hạnh được phục vụ! Bạn cần tra cứu thông tin gì khác không?"
            ],
            "help": [
                "Tôi có thể hỗ trợ bạn:\n• 🔍 Tra cứu thông tin y tế qua hệ thống RAG\n• 📊 Tìm kiếm dữ liệu bệnh nhân bằng SQL\n• 🏥 Truy xuất hồ sơ bệnh nhân qua FHIR\n• 💊 Tư vấn về thuốc và điều trị\n\nHãy hỏi tôi bất cứ điều gì liên quan đến y tế!",
                "CareBot có thể giúp bạn tìm hiểu thông tin y tế, tra cứu dữ liệu bệnh nhân và trả lời các câu hỏi chuyên môn. Bạn cần hỗ trợ về vấn đề gì?"
            ],
            "introduction": [
                "Tôi là CareBot - trợ lý AI chuyên về y tế được phát triển để hỗ trợ tra cứu thông tin, phân tích dữ liệu và tư vấn y tế. Tôi có thể tìm kiếm thông tin qua RAG, truy vấn dữ liệu SQL và kết nối với hệ thống FHIR.",
                "Tôi là CareBot, được tạo ra để hỗ trợ trong lĩnh vực y tế. Tôi có thể giúp bạn tra cứu thông tin bệnh nhân, tìm hiểu về thuốc và điều trị, cũng như phân tích dữ liệu y tế."
            ],
            "datetime": [
                f"Hôm nay là {datetime.now().strftime('%A, ngày %d/%m/%Y')}",
                f"Bây giờ là {datetime.now().strftime('%H:%M')} ngày {datetime.now().strftime('%d/%m/%Y')}"
            ],
            "default": [
                "Tôi chưa hiểu rõ yêu cầu của bạn. Bạn có thể hỏi về thông tin y tế, dữ liệu bệnh nhân hoặc tra cứu thuốc không?",
                "Có vẻ câu hỏi của bạn cần xử lý chuyên sâu hơn. Hãy thử hỏi về thông tin y tế cụ thể để tôi có thể hỗ trợ tốt hơn.",
                "Tôi có thể giúp bạn tốt hơn nếu bạn hỏi về thông tin y tế, dữ liệu bệnh nhân hoặc các vấn đề sức khỏe cụ thể."
            ]
        }
        
        self.model_path = "script_classifier.pkl"
        self._train_or_load_model()
    
    def _has_exclusion_patterns(self, message):
        """Kiểm tra xem message có chứa pattern loại trừ không"""
        message_lower = message.lower()
        
        # Kiểm tra never script phrases
        for phrase in self.never_script_phrases:
            if phrase in message_lower:
                return True
        
        # Kiểm tra exclusion patterns
        for pattern in self.exclusion_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _is_simple_script_only(self, message):

        message_clean = message.strip().lower()
        

        if len(message_clean.split()) > 5:  
            return False
        

        simple_greetings = [
            'xin chào', 'chào', 'hello', 'hi', 'hey', 'hí', 'hế lô',
            'chào bạn', 'hello there', 'hi there'
        ]
        
        simple_goodbyes = [
            'tạm biệt', 'bye', 'goodbye', 'good bye', 'bai bai',
            'see you', 'hẹn gặp lại'
        ]
        
        simple_thanks = [
            'cảm ơn', 'thank you', 'thanks', 'cám ơn', 'tks', 'thks'
        ]
        
        simple_help = [
            'help', 'giúp đỡ', 'hỗ trợ', 'giúp tôi', 'help me'
        ]
        
        all_simple = simple_greetings + simple_goodbyes + simple_thanks + simple_help
        

        return any(simple in message_clean for simple in all_simple)
    
    def _prepare_training_data(self):
        """Chuẩn bị dữ liệu training với balance"""
        X, y = [], []
        for intent, examples in self.training_data.items():
            for example in examples:
                X.append(example.lower())
                y.append(intent)
        return X, y
    
    def _train_or_load_model(self):
        """Train model với parameters nghiêm ngặt hơn"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.pipeline = pickle.load(f)
                print("Loaded existing script classifier model")
                return
            except:
                print("Could not load existing model, training new one...")
        
        X, y = self._prepare_training_data()
        
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 1),  
                max_features=500,   
                lowercase=True,
                strip_accents='unicode',
                min_df=2,          
                max_df=0.8          
            )),
            ('classifier', MultinomialNB(alpha=1.0)) 
        ])
        
        self.pipeline.fit(X, y)
        
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.pipeline, f)
            print("Trained and saved new script classifier model")
        except:
            print("Could not save model, but training successful")
    
    def classify_script(self, message):
        """Phân loại script với logic nghiêm ngặt"""
        if not self.pipeline:
            return "default"
        
  
        if self._has_exclusion_patterns(message):
            return "default"  
      
        if not self._is_simple_script_only(message):
            return "default"
    
        try:
            prediction = self.pipeline.predict([message.lower()])[0]
            probabilities = self.pipeline.predict_proba([message.lower()])[0]
            confidence = max(probabilities)
            
            
            if confidence >= self.confidence_threshold:
                return prediction
            else:
                return "default"
            
        except Exception as e:
            print(f"Classification error: {e}")
            return "default"
    
    def get_response(self, message):
        """Trả về response với validation bổ sung"""
        script_type = self.classify_script(message)
        
     
        if self._has_exclusion_patterns(message):
            script_type = "default"
        
 
        if script_type == "datetime":
            current_time = datetime.now()
            weekday_names = {
                'Monday': 'Thứ Hai', 'Tuesday': 'Thứ Ba', 'Wednesday': 'Thứ Tư',
                'Thursday': 'Thứ Năm', 'Friday': 'Thứ Sáu', 'Saturday': 'Thứ Bảy',
                'Sunday': 'Chủ Nhật'
            }
            weekday_vi = weekday_names.get(current_time.strftime('%A'), current_time.strftime('%A'))
            return f"Hôm nay là {weekday_vi}, ngày {current_time.strftime('%d/%m/%Y')}, bây giờ là {current_time.strftime('%H:%M')}"
        
        responses = self.scripts.get(script_type, self.scripts["default"])
        return random.choice(responses)
    
    def should_use_script(self, message):
        """Method mới để kiểm tra có nên dùng script không"""
     
        if len(message.split()) > 5:
            return False
        
       
        if self._has_exclusion_patterns(message):
            return False
        
        
        if not self._is_simple_script_only(message):
            return False
        
        
        script_type = self.classify_script(message)
        return script_type != "default"

try:
    ml_script_handler = EnhancedMLScriptHandler()
    script_handler = ml_script_handler
    print("Successfully initialized Enhanced ML Script Handler with strict filtering")
except Exception as e:
    print(f"Could not initialize enhanced script handler: {e}")
    class SimpleScriptHandler:
        def classify_script(self, message):
            return "default"
        def get_response(self, message):
            return "Xin lỗi, tôi đang gặp sự cố. Vui lòng thử lại sau."
        def should_use_script(self, message):
            return False
    
    ml_script_handler = SimpleScriptHandler()
    script_handler = ml_script_handler

def handle_script_message(message):
    """Hàm xử lý tin nhắn script - chỉ dùng khi chắc chắn là script"""
    return ml_script_handler.get_response(message)

def is_script_message(message):
    """Kiểm tra nghiêm ngặt xem có phải script không"""
    try:
        return ml_script_handler.should_use_script(message)
    except:
        return False

def get_script_confidence(message):
    """Trả về confidence score cho script classification"""
    try:
        if not ml_script_handler.pipeline:
            return 0.0
        
        if ml_script_handler._has_exclusion_patterns(message):
            return 0.0
        
        if not ml_script_handler._is_simple_script_only(message):
            return 0.0
        
        probabilities = ml_script_handler.pipeline.predict_proba([message.lower()])[0]
        return max(probabilities)
    except:
        return 0.0