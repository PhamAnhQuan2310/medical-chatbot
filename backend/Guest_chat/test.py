import asyncio
import sys
import os
import requests
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

BASE_URL = "http://localhost:8000/api/guest-chat"

async def test_rag_integration():
    """Test RAG integration với guest chat API"""
    
    print("🧪 Testing RAG Integration với Guest Chat API")
    print("=" * 60)
    
    # Test 1: Check model status
    print("\n1️⃣ Testing model status...")
    try:
        response = requests.get(f"{BASE_URL}/model/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Initialize model
    print("\n2️⃣ Testing model initialization...")
    try:
        response = requests.get(f"{BASE_URL}/initialize")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Check debug paths
    print("\n3️⃣ Testing debug check path...")
    try:
        response = requests.get(f"{BASE_URL}/debug/check-path")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Test retrieval only
    print("\n4️⃣ Testing document retrieval...")
    test_query = "Triệu chứng của bệnh tiểu đường type 2?"
    try:
        response = requests.post(f"{BASE_URL}/retrieve", json={
            "message": test_query
        })
        print(f"Status: {response.status_code}")
        result = response.json()
        if result.get("success"):
            print(f"Query: {result['query']}")
            print(f"Retrieved {result['num_docs']} documents")
            for i, (doc, score) in enumerate(zip(result['retrieved_documents'], result['scores'])):
                print(f"  {i+1}. [Score: {score:.3f}] {doc[:100]}...")
        else:
            print(f"❌ Retrieval failed: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Test full RAG chat
    print("\n5️⃣ Testing full RAG chat...")
    test_queries = [
        "Triệu chứng của bệnh tiểu đường là gì?",
        "Cách điều trị cao huyết áp?",
        "Aspirin có tác dụng phụ gì không?"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        
        # Test với RAG enabled
        try:
            response = requests.post(f"{BASE_URL}/chat", json={
                "message": query,
                "use_rag": True
            })
            print(f"   RAG Mode - Status: {response.status_code}")
            result = response.json()
            if result.get("success"):
                print(f"   RAG Response: {result['response'][:200]}...")
                print(f"   Mode: {result.get('mode', 'unknown')}")
                print(f"   RAG Enabled: {result.get('rag_enabled', False)}")
            else:
                print(f"   ❌ RAG failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ RAG Error: {e}")
        
        # Test với T5-only mode
        try:
            response = requests.post(f"{BASE_URL}/chat", json={
                "message": query,
                "use_rag": False
            })
            print(f"   T5-Only Mode - Status: {response.status_code}")
            result = response.json()
            if result.get("success"):
                print(f"   T5-Only Response: {result['response'][:200]}...")
                print(f"   Mode: {result.get('mode', 'unknown')}")
            else:
                print(f"   ❌ T5-Only failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ T5-Only Error: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test_rag_integration())