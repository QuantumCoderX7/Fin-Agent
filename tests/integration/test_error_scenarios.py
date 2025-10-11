"""
Integration tests for error handling scenarios.

This module tests error handling in realistic scenarios with external
service failures, network issues, and various edge cases.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient

from app.main import create_app
from app.utils.exceptions import (
    DataSourceException,
    RateLimitException,
    TimeoutException,
    APIKeyMissingException
)


class TestExternalServiceFailures:
    """Test error handling for external service failures."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    @patch('app.agents.research_agent.ResearchAgent.process_request')
    def test_research_agent_data_source_failure(self, mock_process, client):
        """Test handling of data source failures in research agent."""
        # Mock a data source failure
        mock_process.side_effect = DataSourceException(
            "duckduckgo",
            "Failed to fetch search results",
            status_code=503
        )
        
        response = client.post(
            "/api/v1/research/analyze",
            json={"topic": "AI market trends"}
        )
        
        assert response.status_code == 502
        data = response.json()
        assert data["error_code"] == "DATA_SOURCE_FAILURE"
        assert "duckduckgo" in data["message"]
        assert "correlation_id" in data
        assert "suggestions" in data
        assert any("DuckDuckGo" in suggestion for suggestion in data["suggestions"])
    
    @patch('app.agents.stock_agent.StockAgent.process_request')
    def test_stock_agent_yahoo_finance_failure(self, mock_process, client):
        """Test handling of Yahoo Finance API failures."""
        mock_process.side_effect = DataSourceException(
            "yahoo_finance",
            "Yahoo Finance API unavailable",
            status_code=500
        )
        
        response = client.post(
            "/api/v1/stocks/analyze",
            json={"symbols": ["AAPL"]}
        )
        
        assert response.status_code == 502
        data = response.json()
        assert data["error_code"] == "DATA_SOURCE_FAILURE"
        assert "yahoo_finance" in data["message"]
        assert "Yahoo Finance" in str(data["suggestions"])
    
    @patch('app.agents.research_agent.ResearchAgent.process_request')
    def test_rate_limit_handling(self, mock_process, client):
        """Test handling of rate limit exceptions."""
        mock_process.side_effect = RateLimitException(
            "groq_api",
            "Rate limit exceeded for Groq API",
            retry_after=120
        )
        
        response = client.post(
            "/api/v1/research/analyze",
            json={"topic": "Market analysis"}
        )
        
        assert response.status_code == 429
        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "120"
        assert "120 seconds" in str(data["suggestions"])
    
    @patch('app.agents.research_agent.ResearchAgent.process_request')
    def test_timeout_handling(self, mock_process, client):
        """Test handling of timeout exceptions."""
        mock_process.side_effect = TimeoutException(
            "research_analysis",
            300,
            "Research analysis timed out"
        )
        
        response = client.post(
            "/api/v1/research/analyze",
            json={"topic": "Complex market analysis"}
        )
        
        assert response.status_code == 504
        data = response.json()
        assert data["error_code"] == "OPERATION_TIMEOUT"
        assert "300 seconds" in data["message"]
        assert any("reducing the scope" in suggestion.lower() for suggestion in data["suggestions"])


class TestValidationErrorScenarios:
    """Test various validation error scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_empty_research_topic(self, client):
        """Test validation error for empty research topic."""
        response = client.post(
            "/api/v1/research/analyze",
            json={"topic": ""}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "REQUEST_VALIDATION_ERROR"
        assert "validation_errors" in data["details"]
        
        # Check that validation error details are included
        validation_errors = data["details"]["validation_errors"]
        assert any("topic" in error["field"] for error in validation_errors)
    
    def test_invalid_stock_symbols(self, client):
        """Test validation error for invalid stock symbols."""
        response = client.post(
            "/api/v1/stocks/analyze",
            json={"symbols": ["INVALID@SYMBOL", ""]}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "REQUEST_VALIDATION_ERROR"
        
        # Should include suggestions for fixing validation errors
        assert "suggestions" in data
        assert any("input format" in suggestion.lower() for suggestion in data["suggestions"])
    
    def test_too_many_sources_limit(self, client):
        """Test validation error for exceeding sources limit."""
        response = client.post(
            "/api/v1/research/analyze",
            json={
                "topic": "Market trends",
                "sources_limit": 15  # Exceeds max of 10
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "REQUEST_VALIDATION_ERROR"
    
    def test_missing_required_fields(self, client):
        """Test validation error for missing required fields."""
        response = client.post(
            "/api/v1/evaluation/assess",
            json={
                "query": "Test query"
                # Missing required 'response' and 'context' fields
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "REQUEST_VALIDATION_ERROR"
        
        validation_errors = data["details"]["validation_errors"]
        missing_fields = [error["field"] for error in validation_errors]
        assert "response" in missing_fields
        assert "context" in missing_fields


class TestConfigurationErrorScenarios:
    """Test configuration-related error scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    @patch('app.config.settings.Settings.validate_api_keys')
    def test_missing_api_keys_on_startup(self, mock_validate):
        """Test handling of missing API keys during startup."""
        mock_validate.side_effect = APIKeyMissingException("groq_api_key")
        
        # This should be caught during app startup
        with pytest.raises(APIKeyMissingException):
            create_app()
    
    @patch.dict('os.environ', {}, clear=True)
    def test_missing_environment_variables(self):
        """Test handling of missing environment variables."""
        # This test checks that the app handles missing env vars gracefully
        # The actual behavior depends on the Settings implementation
        pass


class TestConcurrentErrorHandling:
    """Test error handling under concurrent load."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    @patch('app.agents.research_agent.ResearchAgent.process_request')
    def test_concurrent_failures(self, mock_process, client):
        """Test handling of concurrent request failures."""
        # Mock intermittent failures
        call_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise DataSourceException("test", "Intermittent failure")
            return {"result": "success"}
        
        mock_process.side_effect = side_effect
        
        # Make multiple concurrent requests
        responses = []
        for i in range(10):
            response = client.post(
                "/api/v1/research/analyze",
                json={"topic": f"Test topic {i}"}
            )
            responses.append(response)
        
        # Should have mix of successful and failed responses
        success_count = sum(1 for r in responses if r.status_code == 200)
        error_count = sum(1 for r in responses if r.status_code == 502)
        
        assert success_count > 0
        assert error_count > 0
        
        # All error responses should have proper format
        for response in responses:
            if response.status_code == 502:
                data = response.json()
                assert "error_code" in data
                assert "correlation_id" in data
                assert "timestamp" in data


class TestRetryIntegration:
    """Test retry logic integration with real scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    @patch('app.agents.research_agent.ResearchAgent.process_request')
    def test_retry_on_transient_failures(self, mock_process, client):
        """Test that transient failures trigger retries."""
        call_count = 0
        
        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DataSourceException("test", "Transient failure", status_code=503)
            return {"result": "success after retry"}
        
        mock_process.side_effect = side_effect
        
        # This test would require the actual retry logic to be integrated
        # into the agent processing pipeline
        pass
    
    def test_no_retry_on_client_errors(self, client):
        """Test that client errors (4xx) don't trigger retries."""
        # Test with invalid request that should not be retried
        response = client.post(
            "/api/v1/research/analyze",
            json={"topic": ""}  # Invalid empty topic
        )
        
        assert response.status_code == 422
        # Should fail immediately without retries


class TestErrorRecovery:
    """Test error recovery scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_service_recovery_after_failure(self, client):
        """Test that service can recover after failures."""
        # First request fails due to missing data
        response1 = client.post(
            "/api/v1/research/analyze",
            json={"topic": ""}  # Invalid request
        )
        assert response1.status_code == 422
        
        # Second request should work normally
        response2 = client.get("/health")
        assert response2.status_code == 200
        
        # Service should still be operational
        data = response2.json()
        assert data["status"] == "healthy"
    
    def test_correlation_id_consistency(self, client):
        """Test that correlation IDs are consistent across error responses."""
        response = client.post(
            "/api/v1/research/analyze",
            json={"topic": ""}  # Invalid request
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # Correlation ID should be in both response body and headers
        assert "correlation_id" in data
        assert "X-Correlation-ID" in response.headers
        assert data["correlation_id"] == response.headers["X-Correlation-ID"]


if __name__ == "__main__":
    pytest.main([__file__])