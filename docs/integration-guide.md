# Integration Guide

This guide provides comprehensive information for integrating the Financial AI Agents API into your applications and systems.

## Table of Contents

- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [SDK and Client Libraries](#sdk-and-client-libraries)
- [Webhook Integration](#webhook-integration)
- [Streaming Integration](#streaming-integration)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Best Practices](#best-practices)
- [Testing Integration](#testing-integration)

## Quick Start

### 1. Verify API Availability

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "financial-ai-agents"
}
```

### 2. Get API Information

```bash
curl http://localhost:8000/status
```

This returns detailed system information including available endpoints and configuration.

### 3. Test Basic Functionality

```bash
# Get research topics
curl http://localhost:8000/api/v1/research/topics

# Get stock information
curl http://localhost:8000/api/v1/stocks/AAPL/info

# Get evaluation metrics
curl http://localhost:8000/api/v1/evaluation/metrics
```

## Authentication

The Financial AI Agents API currently uses API key authentication for external services. No client authentication is required for the API itself, but you should implement your own authentication layer in production.

### Environment Setup

```bash
# Required environment variables
export GROQ_API_KEY="your_groq_api_key"
export PHI_API_KEY="your_phi_api_key"
```

### Production Authentication

For production deployments, consider implementing:

1. **JWT Authentication**
2. **API Key Authentication**
3. **OAuth 2.0**
4. **mTLS for service-to-service communication**

Example JWT middleware integration:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
```

## SDK and Client Libraries

### Python SDK

```python
import requests
from typing import Dict, List, Optional, Generator
import json

class FinancialAIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def research_analyze(self, topic: str, sources_limit: int = 5, 
                        include_outlook: bool = True) -> Dict:
        """Analyze a financial research topic."""
        url = f"{self.base_url}/api/v1/research/analyze"
        payload = {
            "topic": topic,
            "sources_limit": sources_limit,
            "include_outlook": include_outlook
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def stock_analyze(self, symbols: List[str], analysis_type: str = "comprehensive",
                     include_comparison: bool = False) -> Dict:
        """Analyze stock symbols."""
        url = f"{self.base_url}/api/v1/stocks/analyze"
        payload = {
            "symbols": symbols,
            "analysis_type": analysis_type,
            "include_comparison": include_comparison
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def evaluate_response(self, query: str, response: str, 
                         context: List[str]) -> Dict:
        """Evaluate RAG response quality."""
        url = f"{self.base_url}/api/v1/evaluation/assess"
        payload = {
            "query": query,
            "response": response,
            "context": context
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def stream_research(self, topic: str, sources_limit: int = 5) -> Generator[str, None, None]:
        """Stream research analysis results."""
        url = f"{self.base_url}/api/v1/research/stream"
        payload = {"topic": topic, "sources_limit": sources_limit}
        
        with self.session.post(url, json=payload, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    if line.startswith(b'data: '):
                        data = line[6:].decode('utf-8')
                        if data != '[DONE]':
                            try:
                                chunk = json.loads(data)
                                yield chunk.get('content', '')
                            except json.JSONDecodeError:
                                yield data

# Usage example
client = FinancialAIClient()

# Basic analysis
result = client.research_analyze("Federal Reserve policy 2024")
print(result['headline'])

# Streaming analysis
for chunk in client.stream_research("AI impact on finance"):
    print(chunk, end='', flush=True)
```

### JavaScript/Node.js SDK

```javascript
class FinancialAIClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl.replace(/\/$/, '');
    }

    async researchAnalyze(topic, sourcesLimit = 5, includeOutlook = true) {
        const response = await fetch(`${this.baseUrl}/api/v1/research/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic,
                sources_limit: sourcesLimit,
                include_outlook: includeOutlook
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async stockAnalyze(symbols, analysisType = 'comprehensive', includeComparison = false) {
        const response = await fetch(`${this.baseUrl}/api/v1/stocks/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbols,
                analysis_type: analysisType,
                include_comparison: includeComparison
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    streamResearch(topic, sourcesLimit = 5, onChunk, onComplete, onError) {
        const eventSource = new EventSource(`${this.baseUrl}/api/v1/research/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic,
                sources_limit: sourcesLimit
            })
        });

        eventSource.onmessage = function(event) {
            if (event.data === '[DONE]') {
                eventSource.close();
                if (onComplete) onComplete();
                return;
            }
            
            try {
                const data = JSON.parse(event.data);
                if (onChunk) onChunk(data.content || '');
            } catch (e) {
                if (onChunk) onChunk(event.data);
            }
        };

        eventSource.onerror = function(event) {
            eventSource.close();
            if (onError) onError(event);
        };

        return eventSource;
    }
}

// Usage example
const client = new FinancialAIClient();

// Basic analysis
client.researchAnalyze('Cryptocurrency trends 2024')
    .then(result => console.log(result.headline))
    .catch(error => console.error('Error:', error));

// Streaming analysis
const stream = client.streamResearch(
    'Market volatility analysis',
    5,
    chunk => process.stdout.write(chunk),
    () => console.log('\nStream completed'),
    error => console.error('Stream error:', error)
);
```

## Webhook Integration

### Setting Up Webhooks

While the current API doesn't include built-in webhook functionality, you can implement webhooks for event notifications:

```python
# Example webhook implementation
from fastapi import BackgroundTasks
import httpx

async def send_webhook(url: str, data: dict):
    """Send webhook notification."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, timeout=10.0)
            response.raise_for_status()
        except Exception as e:
            print(f"Webhook failed: {e}")

# Usage in endpoint
@app.post("/api/v1/research/analyze")
async def analyze_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    result = await research_service.analyze(request)
    
    # Send webhook notification
    if webhook_url:
        webhook_data = {
            "event": "research_completed",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        background_tasks.add_task(send_webhook, webhook_url, webhook_data)
    
    return result
```

### Webhook Security

```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature."""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

## Streaming Integration

### Server-Sent Events (SSE)

```python
# Client-side SSE handling
import asyncio
import aiohttp

async def stream_analysis(topic: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8000/api/v1/research/stream',
            json={'topic': topic}
        ) as response:
            async for line in response.content:
                if line.startswith(b'data: '):
                    data = line[6:].decode('utf-8').strip()
                    if data != '[DONE]':
                        try:
                            chunk = json.loads(data)
                            print(chunk.get('content', ''), end='', flush=True)
                        except json.JSONDecodeError:
                            print(data, end='', flush=True)

# Usage
asyncio.run(stream_analysis("Market analysis"))
```

### WebSocket Alternative

```python
# WebSocket implementation (if needed)
from fastapi import WebSocket
import json

@app.websocket("/ws/research")
async def websocket_research(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            
            # Process request and stream results
            async for chunk in research_service.stream_analyze(request):
                await websocket.send_text(json.dumps(chunk))
                
    except Exception as e:
        await websocket.close(code=1000)
```

## Error Handling

### Error Response Format

All API errors follow this consistent format:

```json
{
    "error_code": "VALIDATION_ERROR",
    "message": "Topic cannot be empty",
    "details": {
        "field": "topic",
        "constraint": "min_length"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
}
```

### Client Error Handling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class FinancialAIClientWithRetry:
    def __init__(self, base_url: str, max_retries: int = 3):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def make_request(self, method: str, endpoint: str, **kwargs):
        """Make request with error handling."""
        try:
            response = self.session.request(method, f"{self.base_url}{endpoint}", **kwargs)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_data = response.json() if response.content else {}
            raise APIError(
                status_code=response.status_code,
                error_code=error_data.get('error_code', 'UNKNOWN_ERROR'),
                message=error_data.get('message', str(e)),
                details=error_data.get('details')
            )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to API: {e}")

class APIError(Exception):
    def __init__(self, status_code, error_code, message, details=None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(self.message)
```

## Rate Limiting

### Understanding Rate Limits

The API implements rate limiting with the following default limits:

- **Development**: 100 requests/minute, 1000 requests/hour
- **Production**: 60 requests/minute, 500 requests/hour

### Handling Rate Limits

```python
import time
from datetime import datetime, timedelta

class RateLimitedClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.last_request_time = None
        self.min_interval = 1.0  # Minimum seconds between requests
    
    def make_request(self, method: str, endpoint: str, **kwargs):
        # Implement client-side rate limiting
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        
        try:
            response = self.session.request(method, f"{self.base_url}{endpoint}", **kwargs)
            self.last_request_time = time.time()
            
            # Check rate limit headers
            if 'X-RateLimit-Remaining' in response.headers:
                remaining = int(response.headers['X-RateLimit-Remaining'])
                if remaining < 10:  # Adjust threshold as needed
                    print(f"Warning: Only {remaining} requests remaining")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                return self.make_request(method, endpoint, **kwargs)
            raise
```

## Best Practices

### 1. Connection Management

```python
# Use connection pooling
import requests
from requests.adapters import HTTPAdapter

session = requests.Session()
adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=3
)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

### 2. Timeout Configuration

```python
# Always set timeouts
response = requests.post(
    url,
    json=payload,
    timeout=(5, 30)  # (connect_timeout, read_timeout)
)
```

### 3. Async Operations

```python
import asyncio
import aiohttp

async def batch_analyze_stocks(symbols: list):
    """Analyze multiple stocks concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for symbol in symbols:
            task = analyze_single_stock(session, symbol)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def analyze_single_stock(session, symbol):
    async with session.post(
        'http://localhost:8000/api/v1/stocks/analyze',
        json={'symbols': [symbol]}
    ) as response:
        return await response.json()
```

### 4. Caching Strategies

```python
import redis
import json
from datetime import timedelta

class CachedClient:
    def __init__(self, base_url: str, redis_url: str = "redis://localhost:6379"):
        self.base_url = base_url
        self.redis_client = redis.from_url(redis_url)
        self.cache_ttl = timedelta(minutes=15)
    
    def get_cached_or_fetch(self, cache_key: str, fetch_func, *args, **kwargs):
        # Try cache first
        cached_result = self.redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        # Fetch from API
        result = fetch_func(*args, **kwargs)
        
        # Cache result
        self.redis_client.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(result)
        )
        
        return result
```

## Testing Integration

### Unit Tests

```python
import unittest
from unittest.mock import patch, Mock
import requests

class TestFinancialAIIntegration(unittest.TestCase):
    def setUp(self):
        self.client = FinancialAIClient("http://localhost:8000")
    
    @patch('requests.Session.post')
    def test_research_analyze_success(self, mock_post):
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "headline": "Test Analysis",
            "analysis": "Test content"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.client.research_analyze("test topic")
        
        self.assertEqual(result["headline"], "Test Analysis")
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_research_analyze_error(self, mock_post):
        # Mock error response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_post.return_value = mock_response
        
        with self.assertRaises(requests.exceptions.HTTPError):
            self.client.research_analyze("test topic")
```

### Integration Tests

```python
import pytest
import requests

class TestLiveIntegration:
    @pytest.fixture
    def api_base_url(self):
        return "http://localhost:8000"
    
    def test_health_check(self, api_base_url):
        response = requests.get(f"{api_base_url}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_research_topics(self, api_base_url):
        response = requests.get(f"{api_base_url}/api/v1/research/topics")
        assert response.status_code == 200
        topics = response.json()
        assert isinstance(topics, dict)
        assert len(topics) > 0
    
    @pytest.mark.slow
    def test_full_research_workflow(self, api_base_url):
        # Test complete research workflow
        payload = {
            "topic": "Test market analysis",
            "sources_limit": 3,
            "include_outlook": True
        }
        
        response = requests.post(
            f"{api_base_url}/api/v1/research/analyze",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "headline" in result
        assert "analysis" in result
```

### Load Testing

```python
import asyncio
import aiohttp
import time

async def load_test_endpoint(session, url, payload, num_requests=100):
    """Load test an endpoint with concurrent requests."""
    start_time = time.time()
    
    async def make_request():
        async with session.post(url, json=payload) as response:
            return await response.json()
    
    tasks = [make_request() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    duration = end_time - start_time
    
    successful_requests = sum(1 for r in results if not isinstance(r, Exception))
    
    print(f"Load test results:")
    print(f"  Total requests: {num_requests}")
    print(f"  Successful: {successful_requests}")
    print(f"  Failed: {num_requests - successful_requests}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Requests/second: {num_requests / duration:.2f}")

# Usage
async def run_load_test():
    async with aiohttp.ClientSession() as session:
        await load_test_endpoint(
            session,
            "http://localhost:8000/api/v1/research/topics",
            {},
            num_requests=50
        )

asyncio.run(run_load_test())
```

This integration guide provides comprehensive information for successfully integrating the Financial AI Agents API into various applications and systems, with practical examples and best practices for production use.