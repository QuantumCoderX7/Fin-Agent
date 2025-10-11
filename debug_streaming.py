#!/usr/bin/env python3

import os
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Set environment variables
os.environ['GROQ_API_KEY'] = 'test-key'
os.environ['PHI_API_KEY'] = 'test-key'

from app.main import create_app

def test_debug():
    app = create_app()
    client = TestClient(app)
    
    # Test basic endpoint first
    response = client.get("/health")
    print(f"Health endpoint: {response.status_code}")
    
    # Test status endpoint
    response = client.get("/status")
    print(f"Status endpoint: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"API keys configured: {data.get('api_keys_configured', {})}")
    
    # Test streaming endpoint without mocking
    request_data = {"topic": "test"}
    response = client.post("/api/v1/research/stream", json=request_data)
    print(f"Research stream endpoint: {response.status_code}")
    if response.status_code != 200:
        print(f"Error response: {response.text}")

if __name__ == "__main__":
    test_debug()