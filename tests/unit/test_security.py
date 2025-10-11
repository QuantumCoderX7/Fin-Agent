"""
Unit tests for security features in the Financial AI Agents system.

This module tests API key validation, rate limiting, input sanitization,
and other security-related functionality.
"""

import pytest
import time
from unittest.mock import Mock, patch
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.api.middleware import RateLimitMiddleware, SecurityMiddleware
from app.utils.exceptions import (
    APIKeyMissingException, 
    ValidationException,
    RateLimitException
)
from app.utils.validators import InputValidator


class TestAPIKeyValidation:
    """Test API key validation functionality."""
    
    def test_valid_groq_key(self):
        """Test validation of valid GROQ API key."""
        settings = Settings(
            groq_api_key="gsk_" + "x" * 50,
            phi_api_key="sk-" + "x" * 40
        )
        # Should not raise exception
        settings.validate_api_keys()
    
    def test_valid_phi_key(self):
        """Test validation of valid PHI API key."""
        settings = Settings(
            groq_api_key="gsk_" + "x" * 50,
            phi_api_key="sk-" + "x" * 40
        )
        # Should not raise exception
        settings.validate_api_keys()
    
    def test_missing_groq_key(self):
        """Test validation fails with missing GROQ API key."""
        settings = Settings(
            groq_api_key="",
            phi_api_key="sk-" + "x" * 40
        )
        with pytest.raises(APIKeyMissingException) as exc_info:
            settings.validate_api_keys()
        assert "GROQ_API_KEY" in str(exc_info.value)
    
    def test_missing_phi_key(self):
        """Test validation fails with missing PHI API key."""
        settings = Settings(
            groq_api_key="gsk_" + "x" * 50,
            phi_api_key=""
        )
        with pytest.raises(APIKeyMissingException) as exc_info:
            settings.validate_api_keys()
        assert "PHI_API_KEY" in str(exc_info.value)
    
    def test_invalid_groq_key_format(self):
        """Test validation fails with invalid GROQ key format."""
        settings = Settings(
            groq_api_key="invalid_key",
            phi_api_key="sk-" + "x" * 40
        )
        with pytest.raises(APIKeyMissingException) as exc_info:
            settings.validate_api_keys()
        assert "Invalid API key format" in str(exc_info.value)
    
    def test_invalid_phi_key_format(self):
        """Test validation fails with invalid PHI key format."""
        settings = Settings(
            groq_api_key="gsk_" + "x" * 50,
            phi_api_key="invalid_key"
        )
        with pytest.raises(APIKeyMissingException) as exc_info:
            settings.validate_api_keys()
        assert "Invalid API key format" in str(exc_info.value)
    
    def test_short_groq_key(self):
        """Test validation fails with short GROQ key."""
        settings = Settings(
            groq_api_key="gsk_short",
            phi_api_key="sk-" + "x" * 40
        )
        with pytest.raises(APIKeyMissingException) as exc_info:
            settings.validate_api_keys()
        assert "Invalid API key format" in str(exc_info.value)
    
    def test_short_phi_key(self):
        """Test validation fails with short PHI key."""
        settings = Settings(
            groq_api_key="gsk_" + "x" * 50,
            phi_api_key="sk-short"
        )
        with pytest.raises(APIKeyMissingException) as exc_info:
            settings.validate_api_keys()
        assert "Invalid API key format" in str(exc_info.value)


class TestSecuritySettings:
    """Test security settings validation."""
    
    def test_cors_wildcard_in_production(self):
        """Test CORS wildcard validation in production mode."""
        settings = Settings(
            groq_api_key="gsk_" + "x" * 50,
            phi_api_key="sk-" + "x" * 40,
            debug=False,
            cors_origins=["*"]
        )
        with pytest.raises(APIKeyMissingException) as exc_info:
            settings.validate_security_settings()
        assert "CORS origins set to '*' in production mode" in str(exc_info.value)
    
    def test_cors_wildcard_in_debug(self):
        """Test CORS wildcard allowed in debug mode."""
        settings = Settings(
            groq_api_key="gsk_" + "x" * 50,
            phi_api_key="sk-" + "x" * 40,
            debug=True,
            cors_origins=["*"]
        )
        # Should not raise exception
        settings.validate_security_settings()
    
    def test_excessive_timeout(self):
        """Test validation fails with excessive timeout."""
        settings = Settings(
            groq_api_key="gsk_" + "x" * 50,
            phi_api_key="sk-" + "x" * 40,
            request_timeout=700  # Over 600 seconds limit
        )
        with pytest.raises(APIKeyMissingException) as exc_info:
            settings.validate_security_settings()
        assert "Request timeout" in str(exc_info.value)
    
    def test_excessive_max_sources(self):
        """Test validation fails with excessive max sources."""
        settings = Settings(
            groq_api_key="gsk_" + "x" * 50,
            phi_api_key="sk-" + "x" * 40,
            max_sources=25  # Over 20 limit
        )
        with pytest.raises(APIKeyMissingException) as exc_info:
            settings.validate_security_settings()
        assert "Max sources" in str(exc_info.value)


class TestRateLimitMiddleware:
    """Test rate limiting middleware functionality."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        return request
    
    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter instance for testing."""
        return RateLimitMiddleware(
            app=None,
            calls_per_minute=5,
            calls_per_hour=50,
            burst_limit=3,
            enable_ip_blocking=True
        )
    
    def test_normal_request_flow(self, rate_limiter, mock_request):
        """Test normal request flow within limits."""
        client_ip = "127.0.0.1"
        current_time = time.time()
        
        # Clean state
        rate_limiter._clean_old_requests(client_ip, current_time)
        
        # Should not raise exception for first request
        rate_limiter.minute_requests[client_ip] = []
        rate_limiter.hour_requests[client_ip] = []
        rate_limiter.burst_requests[client_ip] = []
        
        # Simulate adding requests within limits
        for i in range(3):  # Within burst limit
            rate_limiter.minute_requests[client_ip].append(current_time)
            rate_limiter.hour_requests[client_ip].append(current_time)
            rate_limiter.burst_requests[client_ip].append(current_time)
    
    def test_burst_limit_exceeded(self, rate_limiter, mock_request):
        """Test burst limit enforcement."""
        client_ip = "127.0.0.1"
        current_time = time.time()
        
        # Fill burst limit
        rate_limiter.burst_requests[client_ip] = [current_time] * 3
        
        # Check burst limit
        assert rate_limiter._check_burst_limit(client_ip, current_time) == True
    
    def test_minute_limit_exceeded(self, rate_limiter, mock_request):
        """Test minute limit enforcement."""
        client_ip = "127.0.0.1"
        current_time = time.time()
        
        # Fill minute limit
        rate_limiter.minute_requests[client_ip] = [current_time] * 5
        
        # Should be at limit
        assert len(rate_limiter.minute_requests[client_ip]) >= rate_limiter.calls_per_minute
    
    def test_ip_blocking_after_violations(self, rate_limiter, mock_request):
        """Test IP blocking after rate limit violations."""
        client_ip = "127.0.0.1"
        current_time = time.time()
        
        # Simulate multiple violations
        rate_limiter._handle_rate_limit_violation(client_ip, current_time, "minute")
        rate_limiter._handle_rate_limit_violation(client_ip, current_time, "minute")
        
        # IP should be blocked
        assert rate_limiter._is_ip_blocked(client_ip, current_time) == True
    
    def test_old_requests_cleanup(self, rate_limiter, mock_request):
        """Test cleanup of old request records."""
        client_ip = "127.0.0.1"
        current_time = time.time()
        old_time = current_time - 3700  # Over 1 hour ago
        
        # Add old requests
        rate_limiter.minute_requests[client_ip] = [old_time]
        rate_limiter.hour_requests[client_ip] = [old_time]
        rate_limiter.burst_requests[client_ip] = [old_time]
        
        # Clean old requests
        rate_limiter._clean_old_requests(client_ip, current_time)
        
        # Old requests should be removed
        assert len(rate_limiter.minute_requests[client_ip]) == 0
        assert len(rate_limiter.hour_requests[client_ip]) == 0
        assert len(rate_limiter.burst_requests[client_ip]) == 0


class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"User-Agent": "Mozilla/5.0"}
        request.method = "GET"
        request.query_params = {}
        return request
    
    @pytest.fixture
    def security_middleware(self):
        """Create a security middleware instance for testing."""
        return SecurityMiddleware(
            app=None,
            max_request_size_mb=1.0,
            enable_input_sanitization=True,
            blocked_user_agents=["curl", "wget"]
        )
    
    def test_valid_user_agent(self, security_middleware, mock_request):
        """Test validation passes with valid user agent."""
        mock_request.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        # Should not raise exception
        security_middleware._validate_user_agent(mock_request)
    
    def test_empty_user_agent(self, security_middleware, mock_request):
        """Test validation fails with empty user agent."""
        mock_request.headers = {}
        with pytest.raises(ValidationException) as exc_info:
            security_middleware._validate_user_agent(mock_request)
        assert "User-Agent header is required" in str(exc_info.value)
    
    def test_blocked_user_agent(self, security_middleware, mock_request):
        """Test validation fails with blocked user agent."""
        mock_request.headers = {"User-Agent": "curl/7.68.0"}
        with pytest.raises(ValidationException) as exc_info:
            security_middleware._validate_user_agent(mock_request)
        assert "curl" in str(exc_info.value)
    
    def test_content_type_validation_post(self, security_middleware, mock_request):
        """Test content type validation for POST requests."""
        mock_request.method = "POST"
        mock_request.headers = {"User-Agent": "Mozilla/5.0"}
        
        with pytest.raises(ValidationException) as exc_info:
            security_middleware._validate_headers(mock_request)
        assert "Content-Type header is required" in str(exc_info.value)
    
    def test_valid_content_type(self, security_middleware, mock_request):
        """Test validation passes with valid content type."""
        mock_request.method = "POST"
        mock_request.headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }
        # Should not raise exception
        security_middleware._validate_headers(mock_request)
    
    def test_invalid_content_type(self, security_middleware, mock_request):
        """Test validation fails with invalid content type."""
        mock_request.method = "POST"
        mock_request.headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "text/plain"
        }
        with pytest.raises(ValidationException) as exc_info:
            security_middleware._validate_headers(mock_request)
        assert "Content-Type 'text/plain' is not allowed" in str(exc_info.value)
    
    def test_request_size_validation(self, security_middleware, mock_request):
        """Test request size validation."""
        # 2MB content (over 1MB limit)
        mock_request.headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Length": str(2 * 1024 * 1024)
        }
        
        with pytest.raises(ValidationException) as exc_info:
            import asyncio
            asyncio.run(security_middleware._validate_request_size(mock_request))
        assert "Request size" in str(exc_info.value)


class TestInputValidation:
    """Test input validation utilities."""
    
    def test_valid_stock_symbol(self):
        """Test validation of valid stock symbols."""
        valid_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        for symbol in valid_symbols:
            result = InputValidator.validate_stock_symbol(symbol)
            assert result == symbol
    
    def test_invalid_stock_symbol(self):
        """Test validation fails with invalid stock symbols."""
        invalid_symbols = ["", "123", "TOOLONG123", "aa@pl"]
        for symbol in invalid_symbols:
            with pytest.raises(ValidationException):
                InputValidator.validate_stock_symbol(symbol)
    
    def test_text_input_validation(self):
        """Test text input validation with length constraints."""
        # Valid text
        result = InputValidator.validate_text_input("Valid text", "test_field")
        assert result == "Valid text"
        
        # Empty text (not allowed)
        with pytest.raises(ValidationException):
            InputValidator.validate_text_input("", "test_field")
        
        # Text too long
        with pytest.raises(ValidationException):
            InputValidator.validate_text_input("x" * 10001, "test_field", max_length=10000)
    
    def test_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://localhost:8000",
            "https://api.example.com/v1/data"
        ]
        for url in valid_urls:
            result = InputValidator.validate_url(url)
            assert result == url
        
        # Invalid URLs
        invalid_urls = ["", "not-a-url", "ftp://example.com"]
        for url in invalid_urls:
            with pytest.raises(ValidationException):
                InputValidator.validate_url(url)
    
    def test_input_sanitization(self):
        """Test input sanitization against injection attacks."""
        # Test script tag removal
        malicious_input = "<script>alert('xss')</script>Hello"
        sanitized = InputValidator.sanitize_input(malicious_input)
        assert "<script>" not in sanitized
        assert "Hello" in sanitized
        
        # Test JavaScript URL removal
        malicious_input = "javascript:alert('xss')"
        sanitized = InputValidator.sanitize_input(malicious_input)
        assert "javascript:" not in sanitized
    
    def test_numeric_range_validation(self):
        """Test numeric range validation."""
        # Valid number within range
        result = InputValidator.validate_numeric_range(5, "test_field", 1, 10)
        assert result == 5
        
        # Number below minimum
        with pytest.raises(ValidationException):
            InputValidator.validate_numeric_range(0, "test_field", 1, 10)
        
        # Number above maximum
        with pytest.raises(ValidationException):
            InputValidator.validate_numeric_range(15, "test_field", 1, 10)
    
    def test_list_validation(self):
        """Test list input validation."""
        # Valid list
        result = InputValidator.validate_list_input([1, 2, 3], "test_field", 1, 5)
        assert result == [1, 2, 3]
        
        # Empty list (below minimum)
        with pytest.raises(ValidationException):
            InputValidator.validate_list_input([], "test_field", 1, 5)
        
        # List too long
        with pytest.raises(ValidationException):
            InputValidator.validate_list_input([1] * 10, "test_field", 1, 5)


if __name__ == "__main__":
    pytest.main([__file__])