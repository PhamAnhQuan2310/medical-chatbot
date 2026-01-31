"""
Test dashboard endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_dashboard_overview():
    print("\n=== Testing Dashboard Overview ===")
    response = requests.get(f"{BASE_URL}/dashboard/overview")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

def test_recent_sessions():
    print("\n=== Testing Recent Sessions ===")
    response = requests.get(f"{BASE_URL}/dashboard/sessions/recent?limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

def test_session_history(session_id):
    print(f"\n=== Testing Session History for {session_id} ===")
    response = requests.get(f"{BASE_URL}/dashboard/sessions/{session_id}/history")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

def test_user_stats():
    print("\n=== Testing User Stats ===")
    response = requests.get(f"{BASE_URL}/dashboard/users/stats")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

def test_performance_analytics():
    print("\n=== Testing Performance Analytics ===")
    response = requests.get(f"{BASE_URL}/dashboard/analytics/performance")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("Testing Dashboard API...")
    
    # Test overview
    test_dashboard_overview()
    
    # Test recent sessions
    test_recent_sessions()
    
    # Test user stats
    test_user_stats()
    
    # Test performance analytics
    test_performance_analytics()
    
    print("\n=== All tests completed ===")
