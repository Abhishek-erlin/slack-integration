#!/usr/bin/env python3
"""
Simple test script for article API endpoints
"""

import requests
import json

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/v1/articles/health")
        print(f"Health Status: {response.status_code}")
        print(f"Health Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health Error: {e}")
        return False

def test_research_brief():
    """Test research brief generation"""
    url = "http://localhost:8000/api/v1/articles/research-brief"
    
    payload = {
        "keyword": "test",
        "location": "test", 
        "goal": "test"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Research Brief Status Code: {response.status_code}")
        print(f"Research Brief Response: {response.text}")
        
        if response.status_code != 200:
            print("❌ Research brief generation failed")
            return False, None
        
        data = response.json()
        return True, data.get("data", {}).get("id")
    except Exception as e:
        print(f"Research Brief Error: {e}")
        return False, None

if __name__ == "__main__":
    print("🧪 Simple Article API Test")
    print("=" * 40)
    
    # Test health first
    health_ok = test_health()
    print()
    
    if health_ok:
        # Test research brief
        success, article_id = test_research_brief()
        print(f"Result: {'✅ Success' if success else '❌ Failed'}")
        if article_id:
            print(f"Article ID: {article_id}")
    else:
        print("❌ Health check failed - cannot proceed")
