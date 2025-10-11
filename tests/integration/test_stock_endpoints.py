"""
Integration tests for stock analysis endpoints.

These tests verify the functionality of stock analysis endpoints with mocked services,
covering individual stock analysis, comparison, streaming, and basic stock information.
"""

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Set up test environment BEFORE importing app modules
os.environ["GROQ_API_KEY"] = "test-groq-key"
os.environ["PHI_API_KEY"] = "test-phi-key"

from app.main import create_app
from app.models.responses import (
    StockAnalysisResponse, 
    StockAnalysis, 
    StockMetrics,
    ResponseStatus,
    HealthResponse,
    AgentInfoResponse
)
from app.api.deps import get_stock_service


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_stock_service():
    """Mock stock service for testing."""
    service = MagicMock()
    service.execute_stock_analysis = AsyncMock()
    service.stream_stock_analysis = AsyncMock()
    service.get_stock_info = AsyncMock()
    service.compare_stocks = AsyncMock()
    service.get_market_overview = AsyncMock()
    service.get_service_info = MagicMock()
    return service


@pytest.fixture
def sample_stock_metrics():
    """Sample stock metrics for testing."""
    return StockMetrics(
        symbol="AAPL",
        current_price=175.50,
        market_cap=2800000000000,
        pe_ratio=28.5,
        eps=6.15,
        dividend_yield=0.52,
        beta=1.25,
        volume=45000000,
        day_change=2.3,
        year_high=198.23,
        year_low=124.17
    )


@pytest.fixture
def sample_stock_analysis(sample_stock_metrics):
    """Sample stock analysis for testing."""
    return StockAnalysis(
        symbol="AAPL",
        company_name="Apple Inc.",
        metrics=sample_stock_metrics,
        analysis_summary="Apple demonstrates strong fundamentals with consistent revenue growth...",
        recommendation="BUY",
        target_price=190.0,
        risk_level="MEDIUM",
        strengths=[
            "Strong brand loyalty and ecosystem",
            "Consistent revenue growth",
            "Robust cash position"
        ],
        weaknesses=[
            "High valuation multiples",
            "Dependence on iPhone sales"
        ],
        catalysts=[
            "New product launches",
            "Services growth",
            "Market expansion"
        ]
    )


@pytest.fixture
def sample_stock_response(sample_stock_analysis):
    """Sample stock analysis response for testing."""
    return StockAnalysisResponse(
        status=ResponseStatus.SUCCESS,
        symbols=["AAPL"],
        analyses=[sample_stock_analysis],
        market_sentiment="Positive outlook for technology sector",
        comparison_summary=None,
        processing_time=8.5,
        data_freshness=datetime.utcnow()
    )


@pytest.fixture
def valid_stock_request():
    """Valid stock analysis request for testing."""
    return {
        "symbols": ["AAPL"],
        "analysis_type": "comprehensive",
        "include_comparison": False,
        "time_period": "1y",
        "include_recommendations": True
    }


@pytest.fixture
def valid_comparison_request():
    """Valid stock comparison request for testing."""
    return {
        "symbols": ["AAPL", "GOOGL", "MSFT"],
        "analysis_type": "comprehensive",
        "include_comparison": True,
        "time_period": "1y",
        "include_recommendations": True
    }


class TestStockEndpoints:
    """Test cases for stock analysis endpoints."""
    
    def test_stock_status(self, app, client, mock_stock_service):
        """Test stock status endpoint."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        # Setup mock
        mock_stock_service.get_service_info.return_value = {
            "version": "1.0.0",
            "agent_info": {}
        }
        
        try:
            response = client.get("/api/v1/stocks/")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "ready"
            assert data["service"] == "Stock Market Analyst"
            assert "dependencies" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_analyze_single_stock_success(self, app, client, mock_stock_service, sample_stock_response, valid_stock_request):
        """Test successful single stock analysis."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        # Setup mock
        mock_stock_service.execute_stock_analysis.return_value = sample_stock_response
        
        try:
            response = client.post("/api/v1/stocks/analyze", json=valid_stock_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["symbols"] == ["AAPL"]
            assert len(data["analyses"]) == 1
            
            analysis = data["analyses"][0]
            assert analysis["symbol"] == "AAPL"
            assert analysis["company_name"] == "Apple Inc."
            assert analysis["recommendation"] == "BUY"
            assert analysis["risk_level"] == "MEDIUM"
            assert len(analysis["strengths"]) == 3
            assert len(analysis["weaknesses"]) == 2
            
            # Verify service was called
            mock_stock_service.execute_stock_analysis.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    def test_analyze_multiple_stocks_success(self, app, client, mock_stock_service, valid_comparison_request):
        """Test successful multiple stock analysis."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        # Create multi-stock response
        multi_stock_response = StockAnalysisResponse(
            status=ResponseStatus.SUCCESS,
            symbols=["AAPL", "GOOGL", "MSFT"],
            analyses=[],  # Simplified for test
            market_sentiment="Mixed sentiment across tech stocks",
            comparison_summary="AAPL shows strongest fundamentals, GOOGL has growth potential...",
            processing_time=15.2,
            data_freshness=datetime.utcnow()
        )
        
        mock_stock_service.execute_stock_analysis.return_value = multi_stock_response
        
        try:
            response = client.post("/api/v1/stocks/analyze", json=valid_comparison_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert len(data["symbols"]) == 3
            assert data["comparison_summary"] is not None
            assert "AAPL shows strongest fundamentals" in data["comparison_summary"]
            
            # Verify service was called
            mock_stock_service.execute_stock_analysis.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    def test_analyze_invalid_request(self, app, client, mock_stock_service):
        """Test analysis with invalid request."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        try:
            # Request with missing required field
            invalid_request = {"analysis_type": "comprehensive"}
            response = client.post("/api/v1/stocks/analyze", json=invalid_request)
            assert response.status_code == 422
            
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_compare_stocks_success(self, app, client, mock_stock_service, valid_comparison_request):
        """Test successful stock comparison."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        # Setup mock comparison response
        comparison_result = {
            "symbols": ["AAPL", "GOOGL", "MSFT"],
            "comparison_summary": "Comparative analysis shows AAPL with strongest fundamentals...",
            "individual_analyses": [
                {
                    "symbol": "AAPL",
                    "recommendation": "BUY",
                    "risk_level": "MEDIUM",
                    "current_price": 175.50,
                    "market_cap": 2800000000000,
                    "pe_ratio": 28.5
                },
                {
                    "symbol": "GOOGL",
                    "recommendation": "HOLD",
                    "risk_level": "MEDIUM",
                    "current_price": 142.30,
                    "market_cap": 1800000000000,
                    "pe_ratio": 25.2
                }
            ],
            "market_sentiment": "Positive for tech sector",
            "generated_at": datetime.utcnow().isoformat()
        }
        
        mock_stock_service.compare_stocks.return_value = comparison_result
        
        try:
            response = client.post("/api/v1/stocks/compare", json=valid_comparison_request)
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["symbols"]) == 3
            assert "comparison_summary" in data
            assert len(data["individual_analyses"]) == 2
            assert data["market_sentiment"] == "Positive for tech sector"
            
            # Verify service was called
            mock_stock_service.compare_stocks.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    def test_compare_stocks_insufficient_symbols(self, app, client, mock_stock_service):
        """Test comparison with insufficient symbols."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        try:
            # Request with only one symbol
            single_stock_request = {
                "symbols": ["AAPL"],
                "analysis_type": "comprehensive",
                "include_comparison": True
            }
            response = client.post("/api/v1/stocks/compare", json=single_stock_request)
            assert response.status_code == 422
            
            data = response.json()
            assert "at least 2 stocks" in data["detail"].lower()
        finally:
            app.dependency_overrides.clear()
    
    def test_get_stock_info_success(self, app, client, mock_stock_service):
        """Test successful stock info retrieval."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        # Setup mock stock info
        stock_info = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "current_price": 175.50,
            "market_cap": 2800000000000,
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "day_change": 2.3,
            "volume": 45000000,
            "pe_ratio": 28.5,
            "dividend_yield": 0.52,
            "year_high": 198.23,
            "year_low": 124.17,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
        mock_stock_service.get_stock_info.return_value = stock_info
        
        try:
            response = client.get("/api/v1/stocks/AAPL/info")
            assert response.status_code == 200
            
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["company_name"] == "Apple Inc."
            assert data["current_price"] == 175.50
            assert data["sector"] == "Technology"
            assert "retrieved_at" in data
            
            # Verify service was called with correct symbol
            mock_stock_service.get_stock_info.assert_called_once_with("AAPL")
        finally:
            app.dependency_overrides.clear()
    
    def test_get_stock_info_invalid_symbol(self, app, client, mock_stock_service):
        """Test stock info with invalid symbol."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        try:
            # Request with invalid symbol format (too long)
            response = client.get("/api/v1/stocks/INVALID@SYMBOL/info")
            assert response.status_code == 422
            
            data = response.json()
            # FastAPI returns validation errors as a list
            detail = data["detail"]
            assert isinstance(detail, list)
            assert len(detail) > 0
            # Check that it's a validation error for the symbol parameter
            assert detail[0]["loc"] == ["path", "symbol"]
            assert "should have at most 10 characters" in detail[0]["msg"]
        finally:
            app.dependency_overrides.clear()
    
    def test_stream_analysis_success(self, app, client, mock_stock_service, valid_stock_request):
        """Test streaming analysis endpoint."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        # Mock streaming response
        async def mock_stream():
            yield "🔍 **Stock Market Analysis Starting**\n\n"
            yield "**Symbols to analyze:** AAPL\n"
            yield "## 📊 Analyzing AAPL\n\n"
            yield "⏳ Fetching market data for AAPL...\n"
            yield "✅ Data retrieved for Apple Inc.\n"
            yield "**Current Price:** $175.50\n"
            yield "🤖 Generating AI analysis...\n"
            yield "**Recommendation:** BUY\n"
            yield "✅ **Analysis Complete**\n"
        
        mock_stock_service.stream_stock_analysis.return_value = mock_stream()
        
        try:
            response = client.post("/api/v1/stocks/stream", json=valid_stock_request)
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            
            # Check streaming headers
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"
            
            # Verify service was called
            mock_stock_service.stream_stock_analysis.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    def test_get_agent_info_success(self, app, client, mock_stock_service):
        """Test agent info endpoint."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        # Setup mock service info
        service_info = {
            "service_name": "StockService",
            "version": "1.0.0",
            "configuration": {
                "timeout_seconds": 300,
                "max_retries": 3,
                "model_name": "qwen/qwen3-32b"
            },
            "agent_info": {
                "agent_name": "Stock Market Analyst",
                "agent_type": "stock_analysis",
                "capabilities": [
                    "Individual stock analysis",
                    "Multi-stock comparison",
                    "Real-time streaming analysis"
                ],
                "supported_models": ["qwen/qwen3-32b", "mixtral-8x7b-32768"],
                "version": "1.0.0",
                "description": "Professional stock market analyst",
                "tools": ["Yahoo Finance API", "Groq LLM"]
            }
        }
        
        mock_stock_service.get_service_info.return_value = service_info
        
        try:
            response = client.get("/api/v1/stocks/info")
            assert response.status_code == 200
            
            data = response.json()
            assert data["agent_name"] == "Stock Market Analyst"
            assert data["agent_type"] == "stock_analysis"
            assert len(data["capabilities"]) == 3
            assert len(data["supported_models"]) == 2
            assert data["version"] == "1.0.0"
            
            # Verify service was called
            mock_stock_service.get_service_info.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    def test_get_market_overview_success(self, app, client, mock_stock_service):
        """Test market overview endpoint."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        # Setup mock market overview
        market_overview = {
            "sector": "general_market",
            "symbols_analyzed": 8,
            "market_data": [
                {
                    "symbol": "SPY",
                    "company_name": "SPDR S&P 500 ETF Trust",
                    "current_price": 445.20,
                    "day_change": 0.8
                },
                {
                    "symbol": "QQQ",
                    "company_name": "Invesco QQQ Trust",
                    "current_price": 378.50,
                    "day_change": 1.2
                }
            ],
            "summary": "Market overview for 8 symbols",
            "generated_at": datetime.utcnow().isoformat()
        }
        
        mock_stock_service.get_market_overview.return_value = market_overview
        
        try:
            response = client.get("/api/v1/stocks/market/overview")
            assert response.status_code == 200
            
            data = response.json()
            assert data["sector"] == "general_market"
            assert data["symbols_analyzed"] == 8
            assert len(data["market_data"]) == 2
            assert "generated_at" in data
            
            # Verify service was called with None (no sector)
            mock_stock_service.get_market_overview.assert_called_once_with(None)
        finally:
            app.dependency_overrides.clear()
    
    def test_get_market_overview_with_sector(self, app, client, mock_stock_service):
        """Test market overview with specific sector."""
        # Override dependency
        app.dependency_overrides[get_stock_service] = lambda: mock_stock_service
        
        # Setup mock sector overview
        sector_overview = {
            "sector": "technology",
            "symbols_analyzed": 4,
            "market_data": [
                {
                    "symbol": "AAPL",
                    "company_name": "Apple Inc.",
                    "current_price": 175.50,
                    "day_change": 2.3
                }
            ],
            "summary": "Technology sector overview",
            "generated_at": datetime.utcnow().isoformat()
        }
        
        mock_stock_service.get_market_overview.return_value = sector_overview
        
        try:
            response = client.get("/api/v1/stocks/market/overview?sector=technology")
            assert response.status_code == 200
            
            data = response.json()
            assert data["sector"] == "technology"
            assert data["symbols_analyzed"] == 4
            
            # Verify service was called with correct sector
            mock_stock_service.get_market_overview.assert_called_once_with("technology")
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])