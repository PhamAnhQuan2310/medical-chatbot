"""
Script để test Q-Learning integration
"""

import sqlite3
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rl.q_learning_manager import QLearningManager

def test_qlearning():
    # Path to database
    db_path = os.path.join(os.path.dirname(__file__), "Data.db")
    
    # Initialize Q-Learning Manager
    ql_manager = QLearningManager(db_path)
    
    print("=== Testing Q-Learning Manager ===")
    
    # Test session
    session_key = "test_session_001"
    
    # Test bandit creation
    print(f"\n1. Creating bandit for session: {session_key}")
    bandit = ql_manager.get_or_create_bandit(session_key)
    print(f"Bandit arms: {bandit.arms}")
    print(f"Initial values: {bandit.values}")
    print(f"Initial counts: {bandit.counts}")
    
    # Test action selection
    print(f"\n2. Selecting actions:")
    for i in range(5):
        action = ql_manager.choose_action_bandit(session_key, f"Test query {i+1}")
        print(f"Query {i+1}: Selected action = {action}")
        
        # Calculate fake reward based on action
        if action == 'rag':
            reward = 0.8
        elif action == 'sql':
            reward = 0.6
        elif action == 'gemini':
            reward = 0.7
        else:
            reward = 0.5
            
        # Update bandit
        ql_manager.update_bandit(session_key, action, reward, f"Test query {i+1}", reward)
        
        # Print updated values
        bandit = ql_manager.get_or_create_bandit(session_key)
        print(f"  Updated values: {bandit.values}")
        print(f"  Updated counts: {bandit.counts}")
    
    # Test statistics
    print(f"\n3. Session statistics:")
    stats = ql_manager.get_session_stats(session_key)
    print(f"Session stats: {stats}")
    
    print(f"\n4. Overall statistics:")
    overall_stats = ql_manager.get_overall_stats()
    print(f"Overall stats: {overall_stats}")
    
    print(f"\n5. Testing calculate_response_quality:")
    
    # Test different types of responses
    test_responses = [
        "Đây là câu trả lời tốt với thông tin chi tiết.",
        {"answer": "Câu trả lời dạng dict", "sources": ["source1", "source2"]},
        {"answer": "Không tìm thấy thông tin nào", "sources": []},
        "Không có dữ liệu phù hợp",
        ""
    ]
    
    for i, response in enumerate(test_responses):
        quality = ql_manager.calculate_response_quality(f"Test query {i+1}", response, 1.5)
        print(f"Response {i+1} quality: {quality:.3f}")
        print(f"  Response: {response}")

if __name__ == "__main__":
    test_qlearning()
