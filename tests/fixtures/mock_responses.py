"""
Mock responses for external API calls in tests.

This module provides consistent mock responses for all external services
used by the Financial AI Agents system.
"""

from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
import json
import pandas as pd
from typing import Dict, List, Any, Optional

class MockGroqClient:
    """Mock Groq client for testing AI interactions."""
    
    def __init__(self, response_content: Optional[str] = None):
        self.response_content = response_content or self._default_response()
        self.chat = Mock()
        self.chat.completions = Mock()
        self.chat.completions.create = AsyncMock(return_value=self._create_mock_response())
    
    def _default_response(self) -> str:
        return """
        # Analysis Complete
        
        ## Summary
        This is a mock analysis response for testing purposes.
        
        ## Details
        The analysis has been completed successfully with mock data.
        """
    
    def _create_mock_response(self) -> Mock:
        """Create a mock response object."""
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = self.response_content
        response.usage = Mock()
        response.usage.total_tokens = 150
        response.usage.prompt_tokens = 50
        response.usage.completion_tokens = 100
        return response
    
    def set_response(self, content: str):
        """Set custom response content."""
        self.response_content = content
        self.chat.completions.create.return_value = self._create_mock_response()

class MockDuckDuckGoSearch:
    """Mock DuckDuckGo search for testing research functionality."""
    
    def __init__(self, search_results: Optional[List[Dict]] = None):
        self.search_results = search_results or self._default_search_results()
    
    def _default_search_results(self) -> List[Dict]:
        return [
            {
                "title": "Federal Reserve Policy Update",
                "href": "https://example.com/fed-policy-1",
                "body": "The Federal Reserve announced new policy measures affecting interest rates and monetary policy."
            },
            {
                "title": "Market Analysis: Economic Indicators",
                "href": "https://example.com/market-analysis-1",
                "body": "Recent economic indicators show mixed signals with employment data remaining strong."
            },
            {
                "title": "Investment Strategy Outlook",
                "href": "https://example.com/investment-outlook-1",
                "body": "Investment managers are adjusting strategies based on current market conditions and policy changes."
            }
        ]
    
    def text(self, keywords: str, max_results: int = 10, **kwargs) -> List[Dict]:
        """Mock text search method."""
        return self.search_results[:max_results]
    
    def set_results(self, results: List[Dict]):
        """Set custom search results."""
        self.search_results = results

class MockNewspaperArticle:
    """Mock newspaper article for testing content extraction."""
    
    def __init__(self, article_data: Optional[Dict] = None):
        self.article_data = article_data or self._default_article_data()
        self._setup_attributes()
    
    def _default_article_data(self) -> Dict:
        return {
            "title": "Federal Reserve Policy Analysis",
            "text": "The Federal Reserve's recent policy decisions reflect careful consideration of economic indicators and market conditions. Key factors include employment data, inflation metrics, and global economic uncertainties.",
            "authors": ["John Smith", "Jane Doe"],
            "publish_date": datetime(2024, 1, 15),
            "url": "https://example.com/fed-policy-analysis"
        }
    
    def _setup_attributes(self):
        """Set up article attributes."""
        for key, value in self.article_data.items():
            setattr(self, key, value)
    
    def download(self):
        """Mock download method."""
        pass
    
    def parse(self):
        """Mock parse method."""
        pass
    
    def nlp(self):
        """Mock NLP processing method."""
        pass

class MockYFinanceTicker:
    """Mock yfinance ticker for testing stock data retrieval."""
    
    def __init__(self, symbol: str = "AAPL", stock_data: Optional[Dict] = None):
        self.symbol = symbol
        self.stock_data = stock_data or self._default_stock_data()
        self._setup_properties()
    
    def _default_stock_data(self) -> Dict:
        # Create sample historical data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        hist_data = pd.DataFrame({
            'Open': [150.0 + i * 0.1 for i in range(len(dates))],
            'High': [152.0 + i * 0.1 for i in range(len(dates))],
            'Low': [148.0 + i * 0.1 for i in range(len(dates))],
            'Close': [150.0 + i * 0.1 for i in range(len(dates))],
            'Volume': [1000000 + i * 1000 for i in range(len(dates))]
        }, index=dates)
        
        return {
            "info": {
                "longName": f"{self.symbol} Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "marketCap": 2800000000000,
                "trailingPE": 28.5,
                "forwardPE": 26.8,
                "dividendYield": 0.0052,
                "beta": 1.2,
                "52WeekHigh": 195.0,
                "52WeekLow": 140.0,
                "averageVolume": 50000000,
                "regularMarketPrice": 180.50,
                "regularMarketChange": 1.5,
                "regularMarketChangePercent": 0.0085
            },
            "history": hist_data
        }
    
    def _setup_properties(self):
        """Set up ticker properties."""
        self.info = self.stock_data["info"]
    
    def history(self, period: str = "1y", **kwargs) -> pd.DataFrame:
        """Mock history method."""
        return self.stock_data["history"]

class MockHTTPXClient:
    """Mock HTTPX client for testing HTTP requests."""
    
    def __init__(self, responses: Optional[Dict[str, Any]] = None):
        self.responses = responses or {}
        self.request_history = []
    
    async def get(self, url: str, **kwargs) -> Mock:
        """Mock GET request."""
        self.request_history.append(("GET", url, kwargs))
        
        response = Mock()
        response.status_code = 200
        response.json.return_value = self.responses.get(url, {"status": "success"})
        response.text = json.dumps(response.json.return_value)
        return response
    
    async def post(self, url: str, **kwargs) -> Mock:
        """Mock POST request."""
        self.request_history.append(("POST", url, kwargs))
        
        response = Mock()
        response.status_code = 200
        response.json.return_value = self.responses.get(url, {"status": "success"})
        response.text = json.dumps(response.json.return_value)
        return response
    
    def set_response(self, url: str, response_data: Any):
        """Set custom response for specific URL."""
        self.responses[url] = response_data

class MockStreamingResponse:
    """Mock streaming response for testing SSE functionality."""
    
    def __init__(self, chunks: List[str]):
        self.chunks = chunks
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.chunks):
            raise StopAsyncIteration
        
        chunk = self.chunks[self.index]
        self.index += 1
        return chunk

def create_mock_groq_response(content: str, tokens: int = 150) -> Mock:
    """Create a mock Groq API response."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = content
    response.usage = Mock()
    response.usage.total_tokens = tokens
    response.usage.prompt_tokens = tokens // 3
    response.usage.completion_tokens = tokens * 2 // 3
    return response

def create_mock_research_response() -> str:
    """Create a mock research analysis response."""
    return """
    # Federal Reserve Policy Analysis
    
    ## Executive Summary
    The Federal Reserve maintains a cautious approach to monetary policy amid economic uncertainty.
    
    ## Analysis
    Current economic indicators show mixed signals with employment remaining strong while inflation concerns persist.
    
    ## Future Outlook
    Policy adjustments are likely to be gradual and data-dependent in the coming months.
    """

def create_mock_stock_response() -> str:
    """Create a mock stock analysis response."""
    return json.dumps({
        "summary": "Strong fundamentals with growth potential",
        "recommendation": "BUY",
        "risk_level": "MEDIUM",
        "strengths": ["Market leadership", "Strong financials"],
        "weaknesses": ["High valuation", "Market competition"],
        "catalysts": ["Product innovation", "Market expansion"]
    })

def create_mock_evaluation_response() -> str:
    """Create a mock RAG evaluation response."""
    return json.dumps({
        "score": 4,
        "justification": "Good response with minor areas for improvement",
        "examples": ["Accurate information", "Relevant content"],
        "suggestions": ["Add more details", "Improve source attribution"]
    })

# Pre-configured mock objects for common use cases
MOCK_GROQ_CLIENT = MockGroqClient()
MOCK_DDGS = MockDuckDuckGoSearch()
MOCK_NEWSPAPER = MockNewspaperArticle()
MOCK_YFINANCE = MockYFinanceTicker()
MOCK_HTTPX = MockHTTPXClient()

# Response templates for different scenarios
RESPONSE_TEMPLATES = {
    "research_success": create_mock_research_response(),
    "stock_success": create_mock_stock_response(),
    "evaluation_success": create_mock_evaluation_response(),
    "api_error": json.dumps({"error": "API request failed", "code": 500}),
    "timeout_error": json.dumps({"error": "Request timeout", "code": 408}),
    "validation_error": json.dumps({"error": "Invalid request data", "code": 400})
}

def setup_mock_environment():
    """Set up a complete mock environment for testing."""
    return {
        "groq_client": MOCK_GROQ_CLIENT,
        "ddgs": MOCK_DDGS,
        "newspaper": MOCK_NEWSPAPER,
        "yfinance": MOCK_YFINANCE,
        "httpx": MOCK_HTTPX,
        "templates": RESPONSE_TEMPLATES
    }