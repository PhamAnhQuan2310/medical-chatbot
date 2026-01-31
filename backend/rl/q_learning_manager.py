"""
Q-Learning Manager for CareBot - tích hợp reinforcement learning vào hệ thống chat
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple
from .Q_Learning import Bandit, QLearningAgent

class QLearningManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.agents = {}  # Lưu trữ agents cho các session
        self.bandits = {}  # Lưu trữ bandits cho các session
        
        # Định nghĩa actions và states
        self.actions = ['rag', 'gemini', 'sql', 'web_search', 'mcp']
        self.initialize_db()
    
    def initialize_db(self):
        """Khởi tạo bảng q_learning_logs nếu chưa có"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS q_learning_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                action TEXT,
                state TEXT,
                q_value REAL,
                reward REAL,
                user_query TEXT,
                response_quality REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_or_create_bandit(self, session_key: str, epsilon: float = 0.1) -> Bandit:
        """Lấy hoặc tạo bandit cho session"""
        if session_key not in self.bandits:
            self.bandits[session_key] = Bandit(
                arms=self.actions, 
                session_key=session_key, 
                epsilon=epsilon
            )
            # Load state từ database nếu có
            self._load_bandit_state(session_key)
        
        return self.bandits[session_key]
    
    def get_or_create_qagent(self, session_key: str, alpha: float = 0.1, gamma: float = 0.9, epsilon: float = 0.1) -> QLearningAgent:
        """Lấy hoặc tạo Q-Learning agent cho session"""
        if session_key not in self.agents:
            self.agents[session_key] = QLearningAgent(
                actions=self.actions,
                alpha=alpha,
                gamma=gamma,
                epsilon=epsilon
            )
            # Load Q-table từ database nếu có
            self._load_qtable_state(session_key)
        
        return self.agents[session_key]
    
    def _load_bandit_state(self, session_key: str):
        """Load trạng thái bandit từ database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Lấy thống kê cho mỗi action
        cursor.execute("""
            SELECT action, COUNT(*) as count, AVG(reward) as avg_reward
            FROM q_learning_logs 
            WHERE session_id = ? 
            GROUP BY action
        """, (session_key,))
        
        stats = cursor.fetchall()
        bandit = self.bandits[session_key]
        
        for action, count, avg_reward in stats:
            if action in bandit.arms:
                bandit.counts[action] = count
                bandit.values[action] = avg_reward or 0.0
        
        conn.close()
    
    def _load_qtable_state(self, session_key: str):
        """Load Q-table từ database (simplified version)"""
        # Implement if needed - for now, start fresh each session
        pass
    
    def choose_action_bandit(self, session_key: str, user_query: str, context: Dict = None) -> str:
        """Chọn action bằng bandit algorithm"""
        bandit = self.get_or_create_bandit(session_key)
        
        # Có thể customize logic chọn action dựa trên context
        action = bandit.select_action()
        
        # Log action được chọn
        self._log_action_choice(session_key, action, user_query, context)
        
        return action
    
    def choose_action_qlearning(self, session_key: str, state: str, user_query: str) -> str:
        """Chọn action bằng Q-Learning"""
        agent = self.get_or_create_qagent(session_key)
        action = agent.choose_action(state)
        
        # Log action được chọn
        self._log_action_choice(session_key, action, user_query, {"state": state, "method": "qlearning"})
        
        return action
    
    def update_bandit(self, session_key: str, action: str, reward: float, user_query: str = "", response_quality: float = 0.0):
        """Cập nhật bandit với reward"""
        if session_key not in self.bandits:
            return
        
        bandit = self.bandits[session_key]
        bandit.update(action, reward)
        
        # Log vào database
        self._log_qlearning_update(session_key, action, "", reward, user_query, response_quality)
    
    def update_qlearning(self, session_key: str, state: str, action: str, reward: float, next_state: str, user_query: str = "", response_quality: float = 0.0):
        """Cập nhật Q-Learning agent"""
        if session_key not in self.agents:
            return
        
        agent = self.agents[session_key]
        agent.update(state, action, reward, next_state)
        
        # Lấy Q-value sau khi update
        q_value = agent.get_q(state, action)
        
        # Log vào database
        self._log_qlearning_update(session_key, action, state, reward, user_query, response_quality, q_value)
    
    def _log_action_choice(self, session_key: str, action: str, user_query: str, context: Dict = None):
        """Log việc chọn action"""
        # Có thể implement logging chi tiết hơn nếu cần
        pass
    
    def _log_qlearning_update(self, session_id: str, action: str, state: str, reward: float, user_query: str = "", response_quality: float = 0.0, q_value: float = None):
        """Log cập nhật Q-Learning vào database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO q_learning_logs 
            (session_id, action, state, q_value, reward, user_query, response_quality)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, action, state, q_value, reward, user_query, response_quality))
        
        conn.commit()
        conn.close()
    
    def calculate_response_quality(self, user_query: str, bot_response: Any, response_time: float = 0.0) -> float:
        """Tính toán chất lượng response để làm reward"""
        quality_score = 0.5  # Base score
        
        # Kiểm tra bot_response
        if isinstance(bot_response, dict):
            answer = bot_response.get("answer", "")
            sources = bot_response.get("sources", [])
            from_web = bot_response.get("from_web", False)
            
            # Có answer
            if answer and len(answer.strip()) > 10:
                quality_score += 0.2
            
            # Có sources
            if sources and len(sources) > 0:
                quality_score += 0.2
            
            # Từ web search (có thể tốt hoặc xấu tùy context)
            if from_web:
                quality_score += 0.1
                
            # Kiểm tra negative patterns
            negative_patterns = [
                "không tìm thấy", "không có thông tin", "không cung cấp",
                "không chứa", "không liên quan", "không có dữ liệu"
            ]
            
            if any(pattern in answer.lower() for pattern in negative_patterns):
                quality_score -= 0.3
                
        elif isinstance(bot_response, str):
            if len(bot_response.strip()) > 10:
                quality_score += 0.2
            
            negative_patterns = [
                "không tìm thấy", "không có thông tin", "không cung cấp",
                "không chứa", "không liên quan", "không có dữ liệu"
            ]
            
            if any(pattern in bot_response.lower() for pattern in negative_patterns):
                quality_score -= 0.3
        
        # Response time factor (nếu có)
        if response_time > 0:
            if response_time < 2.0:  # < 2 seconds is good
                quality_score += 0.1
            elif response_time > 10.0:  # > 10 seconds is bad
                quality_score -= 0.1
        
        # Normalize between 0 and 1
        return max(0.0, min(1.0, quality_score))
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Lấy thống kê Q-Learning cho session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT action, COUNT(*) as count, AVG(reward) as avg_reward, AVG(q_value) as avg_q_value
            FROM q_learning_logs 
            WHERE session_id = ? 
            GROUP BY action
        """, (session_id,))
        
        stats = {}
        for action, count, avg_reward, avg_q_value in cursor.fetchall():
            stats[action] = {
                "count": count,
                "avg_reward": avg_reward or 0.0,
                "avg_q_value": avg_q_value or 0.0
            }
        
        conn.close()
        return stats
    
    def get_overall_stats(self) -> Dict:
        """Lấy thống kê tổng quan"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_actions,
                AVG(reward) as avg_reward,
                AVG(q_value) as avg_q_value,
                AVG(response_quality) as avg_quality
            FROM q_learning_logs
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "total_actions": row[0] or 0,
            "avg_reward": row[1] or 0.0,
            "avg_q_value": row[2] or 0.0,
            "avg_response_quality": row[3] or 0.0
        }
