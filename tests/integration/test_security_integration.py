"""
Integration tests for security features in the Financial AI Agents system.

This module tests end-to-end security functionality including rate limiting,
input validation, and API key management in a real application context.
"""

import pytest
import time
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from app.main import create_app
from app.config.settings import get_settings


class TestSecurityIntegration:
    """Integration tests for security middleware and validation."""
    
    @pytest.fixture
    def client(self):
        """Create a test client with security middleware enabled."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings with valid API keys for testing."""
        with patch('app.config.settings.get_settings') as mock:
            settings = Mock()
            settings.groq_api_key = "gsk_" + "x" * 50
            settings.phi_api_key = "sk-" + "x" * 40
            settings.debug = True
            settings.cors_origins = ["*"]
            settings.request_timeout = 300
            settings.max_sources = 10
            settings.app_name = "Financial AI Agents"
            settings.api_v1_prefix = "/api/v1"
            mock.return_value = settings
            yield settings
    
    def test_health_check_with_security(self, client, mock_settings):
        """Test that health check works with security middleware."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_missing_user_agent_blocked(self, client, mock_settings):
        """Test that requests without User-Agent are blocked."""
        # Remove default User-Agent header
        response = client.get("/health", headers={})
        assert response.status_code == 422
        assert "User-Agent header is required" in response.json()["message"]
    
    def test_blocked_user_agent(self, client, mock_settings):
        """Test that blocked user agents are rejected."""
        response = client.get(
            "/health", 
            headers={"User-Agent": "curl/7.68.0"}
        )
        assert response.status_code == 422
        assert "curl" in response.json()["message"]
    
    def test_valid_user_agent_allowed(self, client, mock_settings):
        """Test that valid user agents are allowed."""
        response = client.get(
            "/health",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        assert response.status_code == 200
    
    def test_rate_limiting_headers(self, client, mock_settings):
        """Test that rate limiting headers are included in responses."""
        response = client.get("/health")
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Limit-Hour" in response.headers
        assert "X-RateLimit-Remaining-Hour" in response.headers
    
    def test_correlation_id_header(self, client, mock_settings):
        """Test that correlation ID is included in responses."""
        response = client.get("/health")
        assert "X-Correlation-ID" in response.headers
        
        # Correlation ID should be a valid UUID format
        correlation_id = response.headers["X-Correlation-ID"]
        assert len(correlation_id) == 36  # UUID length
        assert correlation_id.count("-") == 4  # UUID format
    
    def test_post_request_content_type_validation(self, client, mock_settings):
        """Test content type validation for POST requests."""
        # Missing Content-Type
        response = client.post(
            "/api/v1/research/analyze",
            json={"topic": "test"},
            headers={"Content-Type": ""}  # Override default
        )
        assert response.status_code == 422
        assert "Content-Type header is required" in response.json()["message"]
    
    def test_invalid_content_type_rejected(self, client, mock_settings):
        """Test that invalid content types are rejected."""
        response = client.post(
            "/api/v1/research/analyze",
            data="plain text data",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 422
        assert "Content-Type 'text/plain' is not allowed" in response.json()["message"]
    
    def test_large_request_rejected(self, client, mock_settings):
        """Test that oversized requests are rejected."""
        # Create a large payload (over 10MB)
        large_data = {"topic": "x" * (11 * 1024 * 1024)}  # 11MB of data
        
        response = client.post(
            "/api/v1/research/analyze",
            json=large_data
        )
        # Should be rejected due to size
        assert response.status_code in [413, 422]  # Payload too large or validation error
    
    def test_suspicious_query_parameters(self, client, mock_settings):
        """Test that suspicious query parameters are detected."""
        # SQL injection attempt
        response = client.get(
            "/health?test='; DROP TABLE users; --"
        )
        # Should be blocked or sanitized
        assert response.status_code in [200, 422]  # Either sanitized or blocked
    
    def test_xss_attempt_in_query(self, client, mock_settings):
        """Test that XSS attempts in query parameters are blocked."""
        response = client.get(
            "/health?search=<script>alert('xss')</script>"
        )
        # Should be blocked or sanitized
        assert response.status_code in [200, 422]  # Either sanitized or blocked
    
    @patch('app.api.middleware.time.time')
    def test_rate_limit_enforcement(self, mock_time, client, mock_settings):
        """Test that rate limiting is enforced correctly."""
        # Mock time to control rate limiting
        current_time = 1000000
        mock_time.return_value = current_time
        
        # Make requests up to the limit
        responses = []
        for i in range(65):  # Over the 60 per minute limit
            response = client.get("/health")
            responses.append(response)
            
            # If we hit rate limit, break
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        assert any(r.status_code == 429 for r in responses)
    
    def test_error_response_format(self, client, mock_settings):
        """Test that error responses follow the expected format."""
        # Trigger a validation error
        response = client.get("/health", headers={})  # Missing User-Agent
        
        assert response.status_code == 422
        error_data = response.json()
        
        # Check error response structure
        assert "error_code" in error_data
        assert "message" in error_data
        assert "timestamp" in error_data
        assert "correlation_id" in error_data
        
        # Check correlation ID matches header
        assert error_data["correlation_id"] == response.headers["X-Correlation-ID"]
    
    def test_security_headers_present(self, client, mock_settings):
        """Test that security headers are present in responses."""
        response = client.get("/health")
        
        # Check for security-related headers
        assert "X-Correlation-ID" in response.headers
        assert "X-RateLimit-Limit-Minute" in response.headers
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    def test_api_endpoint_security(self, client, mock_settings):
        """Test security on actual API endpoints."""
        # Test research endpoint with invalid data
        response = client.post(
            "/api/v1/research/analyze",
            json={"topic": ""},  # Empty topic should be rejected
        )
        
        # Should return validation error
        assert response.status_code in [422, 400]
    
    def test_streaming_endpoint_security(self, client, mock_settings):
        """Test security on streaming endpoints."""
        response = client.post(
            "/api/v1/research/stream",
            json={"topic": "test research"},
        )
        
        # Should have proper headers even for streaming
        assert "X-Correlation-ID" in response.headers


class TestAPIKeyValidationIntegration:
    """Integration tests for API key validation during startup."""
    
    def test_startup_with_missing_api_keys(self):
        """Test that application fails to start with missing API keys."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(Exception):  # Should raise APIKeyMissingException
                create_app()
    
    def test_startup_with_invalid_api_keys(self):
        """Test that application fails to start with invalid API keys."""
        with patch.dict('os.environ', {
            'GROQ_API_KEY': 'invalid_key',
            'PHI_API_KEY': 'invalid_key'
        }):
            with pytest.raises(Exception):  # Should raise APIKeyMissingException
                create_app()
    
    @patch.dict('os.environ', {
        'GROQ_API_KEY': 'gsk_' + 'x' * 50,
        'PHI_API_KEY': 'sk-' + 'x' * 40
    })
    def test_startup_with_valid_api_keys(self):
        """Test that application starts successfully with valid API keys."""
        app = create_app()
        assert app is not None
        
        # Test that the app can handle requests
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200


class TestSecurityConfiguration:
    """Test security configuration validation."""
    
    def test_production_cors_validation(self):
        """Test CORS validation in production mode."""
        with patch.dict('os.environ', {
            'GROQ_API_KEY': 'gsk_' + 'x' * 50,
            'PHI_API_KEY': 'sk-' + 'x' * 40,
            'DEBUG': 'false',
            'CORS_ORIGINS': '*'
        }):
            with pytest.raises(Exception):  # Should raise security exception
                create_app()
    
    def test_debug_mode_security_relaxed(self):
        """Test that security is relaxed in debug mode."""
        with patch.dict('os.environ', {
            'GROQ_API_KEY': 'gsk_' + 'x' * 50,
            'PHI_API_KEY': 'sk-' + 'x' * 40,
            'DEBUG': 'true',
            'CORS_ORIGINS': '*'
        }):
            app = create_app()
            client = TestClient(app)
            
            # Should allow curl in debug mode
            response = client.get("/health", headers={"User-Agent": "curl/7.68.0"})
            assert response.status_code == 200
    
    def test_timeout_validation(self):
        """Test request timeout validation."""
        with patch.dict('os.environ', {
            'GROQ_API_KEY': 'gsk_' + 'x' * 50,
            'PHI_API_KEY': 'sk-' + 'x' * 40,
            'REQUEST_TIMEOUT': '700'  # Over 600 second limit
        }):
            with pytest.raises(Exception):  # Should raise security exception
                create_app()
    
    def test_max_sources_validation(self):
        """Test max sources validation."""
        with patch.dict('os.environ', {
            'GROQ_API_KEY': 'gsk_' + 'x' * 50,
            'PHI_API_KEY': 'sk-' + 'x' * 40,
            'MAX_SOURCES': '25'  # Over 20 limit
        }):
            with pytest.raises(Exception):  # Should raise security exception
                create_app()


if __name__ == "__main__":
    pytest.main([__file__])