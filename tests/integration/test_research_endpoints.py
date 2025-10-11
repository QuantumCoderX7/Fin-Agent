"""
Simplified integration tests for research analysis endpoints.

These tests verify the basic functionality of research endpoints with mocked services.
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
from app.models.responses import ResearchResponse, SourceInfo
from app.api.deps import get_research_service


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_research_service():
    """Mock research service for testing."""
    service = MagicMock()
    service.execute_research_analysis = AsyncMock()
    service.stream_research_analysis = AsyncMock()
    service.get_research_suggestions = AsyncMock()
    return service


@pytest.fixture
def sample_research_response():
    """Sample research response for testing."""
    return ResearchResponse(
        headline="Federal Reserve Policy Analysis",
        executive_summary="The Federal Reserve is expected to maintain current interest rates...",
        analysis="Detailed analysis of current monetary policy trends and implications...",
        future_outlook="Looking ahead, the Fed is likely to adopt a cautious approach...",
        key_insights=[
            "Interest rates likely to remain stable",
            "Inflation showing signs of moderation",
            "Labor market remains resilient"
        ],
        sources=[
            SourceInfo(
                url="https://example.com/fed-policy",
                title="Fed Policy Update",
                relevance_score=0.95
            )
        ],
        topic="Federal Reserve interest rate policy",
        confidence_score=0.85,
        processing_time=12.5
    )


@pytest.fixture
def valid_research_request():
    """Valid research request for testing."""
    return {
        "topic": "Federal Reserve interest rate policy impact",
        "sources_limit": 5,
        "include_outlook": True,
        "focus_areas": ["monetary policy", "inflation"],
        "time_horizon": "6 months"
    }


class TestResearchEndpoints:
    """Test cases for research endpoints."""
    
    def test_research_status(self, app, client, mock_research_service):
        """Test research status endpoint."""
        # Override dependency
        app.dependency_overrides[get_research_service] = lambda: mock_research_service
        
        try:
            response = client.get("/api/v1/research/")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "ready"
            assert data["agent"] == "research"
            assert "available_endpoints" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_analyze_success(self, app, client, mock_research_service, sample_research_response, valid_research_request):
        """Test successful research analysis."""
        # Override dependency
        app.dependency_overrides[get_research_service] = lambda: mock_research_service
        
        # Setup mock
        mock_research_service.execute_research_analysis.return_value = sample_research_response
        
        try:
            response = client.post("/api/v1/research/analyze", json=valid_research_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["headline"] == "Federal Reserve Policy Analysis"
            assert data["topic"] == "Federal Reserve interest rate policy"
            assert data["confidence_score"] == 0.85
            assert len(data["key_insights"]) == 3
            assert len(data["sources"]) == 1
            
            # Verify service was called
            mock_research_service.execute_research_analysis.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    def test_analyze_invalid_request(self, app, client, mock_research_service):
        """Test analysis with invalid request."""
        # Override dependency
        app.dependency_overrides[get_research_service] = lambda: mock_research_service
        
        try:
            # Request with missing required field
            invalid_request = {"sources_limit": 5}
            response = client.post("/api/v1/research/analyze", json=invalid_request)
            assert response.status_code == 422
            
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_get_topics_success(self, app, client, mock_research_service):
        """Test successful topic retrieval."""
        # Override dependency
        app.dependency_overrides[get_research_service] = lambda: mock_research_service
        
        # Setup mock
        mock_research_service.get_research_suggestions.return_value = {
            "domain": "finance",
            "suggested_topics": [
                "Federal Reserve interest rate policy impact",
                "Cryptocurrency market trends and regulation",
                "ESG investing and sustainable finance"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        try:
            response = client.get("/api/v1/research/topics")
            assert response.status_code == 200
            
            data = response.json()
            assert data["domain"] == "finance"
            assert len(data["suggested_topics"]) == 3
            assert "generated_at" in data
            
            # Verify service was called
            mock_research_service.get_research_suggestions.assert_called_once_with("finance")
        finally:
            app.dependency_overrides.clear()
    
    def test_get_topics_with_domain(self, app, client, mock_research_service):
        """Test topic retrieval with specific domain."""
        # Override dependency
        app.dependency_overrides[get_research_service] = lambda: mock_research_service
        
        # Setup mock
        mock_research_service.get_research_suggestions.return_value = {
            "domain": "markets",
            "suggested_topics": [
                "Emerging markets investment opportunities",
                "Bond market dynamics and yield curves"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        try:
            response = client.get("/api/v1/research/topics?domain=markets")
            assert response.status_code == 200
            
            data = response.json()
            assert data["domain"] == "markets"
            assert len(data["suggested_topics"]) == 2
            
            # Verify service was called with correct domain
            mock_research_service.get_research_suggestions.assert_called_once_with("markets")
        finally:
            app.dependency_overrides.clear()
    
    def test_stream_analysis(self, app, client, mock_research_service, valid_research_request):
        """Test streaming analysis endpoint."""
        # Override dependency
        app.dependency_overrides[get_research_service] = lambda: mock_research_service
        
        # Mock streaming response
        async def mock_stream():
            yield "Starting analysis..."
            yield "Searching sources..."
            yield "Analysis complete!"
        
        mock_research_service.stream_research_analysis.return_value = mock_stream()
        
        try:
            response = client.post("/api/v1/research/stream", json=valid_research_request)
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # Verify service was called
            mock_research_service.stream_research_analysis.assert_called_once()
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])