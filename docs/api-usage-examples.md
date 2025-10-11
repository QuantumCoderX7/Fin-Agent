# API Usage Examples

This document provides comprehensive examples of how to use the Financial AI Agents API.

## Table of Contents

- [Authentication](#authentication)
- [Research Agent Examples](#research-agent-examples)
- [Stock Analysis Examples](#stock-analysis-examples)
- [RAG Evaluation Examples](#rag-evaluation-examples)
- [Streaming Examples](#streaming-examples)
- [Error Handling](#error-handling)

## Authentication

The API requires API keys for external data sources. Configure these via environment variables:

```bash
export GROQ_API_KEY="your_groq_api_key"
export PHI_API_KEY="your_phi_api_key"
```

## Research Agent Examples

### Basic Research Analysis

```python
import requests
import json

# Basic research request
url = "http://localhost:8000/api/v1/research/analyze"
payload = {
    "topic": "Federal Reserve interest rate policy 2024",
    "sources_limit": 5,
    "include_outlook": True
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Headline: {result['headline']}")
print(f"Executive Summary: {result['executive_summary']}")
print(f"Analysis: {result['analysis']}")
print(f"Future Outlook: {result['future_outlook']}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

async function analyzeMarketTrend() {
    try {
        const response = await axios.post('http://localhost:8000/api/v1/research/analyze', {
            topic: "Cryptocurrency market trends Q4 2024",
            sources_limit: 7,
            include_outlook: true
        });
        
        console.log('Research Results:', response.data);
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

analyzeMarketTrend();
```

### Get Research Topics

```python
# Get suggested research topics
response = requests.get("http://localhost:8000/api/v1/research/topics")
topics = response.json()

print("Suggested Topics:")
for category, topic_list in topics.items():
    print(f"\n{category}:")
    for topic in topic_list:
        print(f"  - {topic}")
```

## Stock Analysis Examples

### Individual Stock Analysis

```python
# Analyze a single stock
url = "http://localhost:8000/api/v1/stocks/analyze"
payload = {
    "symbols": ["AAPL"],
    "analysis_type": "comprehensive",
    "include_comparison": False
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Stock Analysis for {result['symbols'][0]}:")
print(f"Analysis: {result['analysis']}")
print(f"Recommendation: {result['recommendations']}")
print(f"Market Sentiment: {result['market_sentiment']}")
```

### Multi-Stock Comparison

```python
# Compare multiple stocks
payload = {
    "symbols": ["AAPL", "GOOGL", "MSFT", "AMZN"],
    "analysis_type": "comparative",
    "include_comparison": True
}

response = requests.post(url, json=payload)
result = response.json()

print("Stock Comparison Results:")
for symbol in result['symbols']:
    analysis = result['analysis'][symbol]
    recommendation = result['recommendations'][symbol]
    print(f"\n{symbol}:")
    print(f"  Recommendation: {recommendation}")
    print(f"  Key Metrics: {analysis.get('key_metrics', 'N/A')}")
```

### Get Stock Information

```python
# Get basic stock information
symbol = "TSLA"
response = requests.get(f"http://localhost:8000/api/v1/stocks/{symbol}/info")
info = response.json()

print(f"Stock Info for {symbol}:")
print(json.dumps(info, indent=2))
```

### cURL Examples

```bash
# Basic stock analysis
curl -X POST "http://localhost:8000/api/v1/stocks/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "symbols": ["NVDA"],
       "analysis_type": "comprehensive",
       "include_comparison": false
     }'

# Stock comparison
curl -X POST "http://localhost:8000/api/v1/stocks/compare" \
     -H "Content-Type: application/json" \
     -d '{
       "symbols": ["AAPL", "MSFT"],
       "analysis_type": "comparative",
       "include_comparison": true
     }'
```

## RAG Evaluation Examples

### Evaluate Response Quality

```python
# Evaluate a RAG response
url = "http://localhost:8000/api/v1/evaluation/assess"
payload = {
    "query": "What is the current state of the US housing market?",
    "response": "The US housing market is experiencing high prices due to low inventory and high demand. Interest rates have been rising, which may cool the market.",
    "context": [
        "Housing inventory is at historic lows",
        "Mortgage rates have increased to 7%",
        "Home prices increased 8% year-over-year"
    ],
    "evaluation_criteria": ["faithfulness", "relevance", "completeness"]
}

response = requests.post(url, json=payload)
result = response.json()

print("Evaluation Results:")
print(f"Overall Score: {result['overall_score']}/5")
print(f"Scores: {result['scores']}")
print(f"Recommendations: {result['recommendations']}")
print(f"Summary: {result['summary']}")
```

### Batch Evaluation

```python
# Batch evaluate multiple responses
url = "http://localhost:8000/api/v1/evaluation/batch"
payload = {
    "evaluations": [
        {
            "query": "Market outlook for tech stocks",
            "response": "Tech stocks are expected to perform well...",
            "context": ["Tech earnings strong", "AI adoption growing"]
        },
        {
            "query": "Bond market analysis",
            "response": "Bond yields are rising due to inflation...",
            "context": ["Inflation at 3.2%", "Fed policy tightening"]
        }
    ]
}

response = requests.post(url, json=payload)
results = response.json()

for i, result in enumerate(results['evaluations']):
    print(f"\nEvaluation {i+1}:")
    print(f"  Overall Score: {result['overall_score']}")
    print(f"  Key Issues: {result['recommendations'][:2]}")
```

## Streaming Examples

### Python Streaming with SSE

```python
import requests
import json

def stream_research_analysis(topic):
    url = "http://localhost:8000/api/v1/research/stream"
    payload = {"topic": topic, "sources_limit": 5}
    
    with requests.post(url, json=payload, stream=True) as response:
        for line in response.iter_lines():
            if line:
                # Parse Server-Sent Events
                if line.startswith(b'data: '):
                    data = line[6:].decode('utf-8')
                    if data != '[DONE]':
                        try:
                            chunk = json.loads(data)
                            print(chunk.get('content', ''), end='', flush=True)
                        except json.JSONDecodeError:
                            print(data, end='', flush=True)

# Usage
stream_research_analysis("AI impact on financial services")
```

### JavaScript Streaming with EventSource

```javascript
function streamStockAnalysis(symbols) {
    const eventSource = new EventSource('/api/v1/stocks/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            symbols: symbols,
            analysis_type: 'comprehensive'
        })
    });

    eventSource.onmessage = function(event) {
        if (event.data === '[DONE]') {
            eventSource.close();
            console.log('Stream completed');
            return;
        }
        
        try {
            const data = JSON.parse(event.data);
            document.getElementById('output').innerHTML += data.content;
        } catch (e) {
            document.getElementById('output').innerHTML += event.data;
        }
    };

    eventSource.onerror = function(event) {
        console.error('Stream error:', event);
        eventSource.close();
    };
}

// Usage
streamStockAnalysis(['AAPL', 'GOOGL']);
```

## Error Handling

### Common Error Responses

```python
import requests

try:
    response = requests.post("http://localhost:8000/api/v1/research/analyze", 
                           json={"topic": ""})  # Invalid empty topic
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    error_data = response.json()
    print(f"Error {response.status_code}: {error_data['message']}")
    print(f"Details: {error_data.get('details', 'N/A')}")
```

### Error Response Format

All errors follow this structure:

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

### Common Error Codes

- `VALIDATION_ERROR`: Invalid input parameters
- `API_KEY_MISSING`: Required API keys not configured
- `DATA_SOURCE_ERROR`: External API failure
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `PROCESSING_ERROR`: Internal processing failure

### Retry Logic Example

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Usage
session = create_session_with_retries()
response = session.post("http://localhost:8000/api/v1/research/analyze", 
                       json={"topic": "Market analysis"})
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Development**: 100 requests/minute, 1000 requests/hour
- **Production**: 60 requests/minute, 500 requests/hour

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1642234567
```

## Best Practices

1. **Always handle errors gracefully**
2. **Implement retry logic for transient failures**
3. **Use streaming for long-running operations**
4. **Cache results when appropriate**
5. **Monitor rate limits**
6. **Validate inputs before sending requests**
7. **Use appropriate timeouts**

## Integration Testing

```python
import unittest
import requests

class TestFinancialAIAPI(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:8000"
    
    def test_health_check(self):
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
    
    def test_research_analysis(self):
        payload = {
            "topic": "Test market analysis",
            "sources_limit": 3
        }
        response = requests.post(f"{self.base_url}/api/v1/research/analyze", 
                               json=payload)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("headline", result)
        self.assertIn("analysis", result)

if __name__ == "__main__":
    unittest.main()
```