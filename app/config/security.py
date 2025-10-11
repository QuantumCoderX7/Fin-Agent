"""
Security configuration and utilities for the Financial AI Agents system.

This module provides security-related configuration, constants, and utility
functions to ensure the system follows security best practices.
"""

from typing import List, Dict, Any
from enum import Enum


class SecurityLevel(Enum):
    """Security levels for different deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SecurityConfig:
    """Security configuration constants and settings."""
    
    # API Key validation patterns
    GROQ_API_KEY_PREFIX = "gsk_"
    GROQ_API_KEY_MIN_LENGTH = 50
    
    OPENAI_API_KEY_PREFIX = "sk-"
    OPENAI_API_KEY_MIN_LENGTH = 40
    
    # Rate limiting defaults
    DEFAULT_RATE_LIMIT_PER_MINUTE = 60
    DEFAULT_RATE_LIMIT_PER_HOUR = 1000
    DEFAULT_BURST_LIMIT = 10
    
    # Request size limits
    MAX_REQUEST_SIZE_MB = 10.0
    MAX_QUERY_PARAM_LENGTH = 1000
    MAX_HEADER_VALUE_LENGTH = 8192
    
    # Timeout limits
    MAX_REQUEST_TIMEOUT_SECONDS = 600  # 10 minutes
    MAX_SOURCES_LIMIT = 20
    
    # Blocked user agents (case-insensitive)
    BLOCKED_USER_AGENTS = [
        "curl",
        "wget", 
        "python-requests",
        "bot",
        "crawler",
        "spider",
        "scraper"
    ]
    
    # Allowed content types for POST/PUT requests
    ALLOWED_CONTENT_TYPES = [
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data"
    ]
    
    # Suspicious patterns for input validation
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>',           # Script injection
        r'javascript:',             # JavaScript URLs
        r'on\w+\s*=',              # Event handlers
        r'union\s+select',          # SQL injection
        r'drop\s+table',            # SQL injection
        r'exec\s*\(',               # Command injection
        r'eval\s*\(',               # Code injection
        r'<iframe[^>]*>',           # Iframe injection
        r'<object[^>]*>',           # Object injection
        r'<embed[^>]*>',            # Embed injection
        r'vbscript:',               # VBScript injection
        r'data:text/html',          # Data URL injection
    ]
    
    # Headers that might indicate security issues
    SUSPICIOUS_HEADERS = [
        "X-Forwarded-Host",         # Host header injection
        "X-Original-URL",           # URL manipulation
        "X-Rewrite-URL",            # URL rewriting attacks
        "X-Forwarded-Proto",        # Protocol manipulation
    ]
    
    # Security headers to add to responses
    SECURITY_RESPONSE_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'",
    }


class SecurityValidator:
    """Utility class for security validation functions."""
    
    @staticmethod
    def is_valid_api_key_format(key: str, key_type: str) -> bool:
        """
        Validate API key format based on type.
        
        Args:
            key: API key to validate
            key_type: Type of key ('groq' or 'phi')
            
        Returns:
            True if key format is valid
        """
        if not key or not isinstance(key, str):
            return False
        
        if key_type.lower() == "groq":
            return (
                key.startswith(SecurityConfig.GROQ_API_KEY_PREFIX) and
                len(key) >= SecurityConfig.GROQ_API_KEY_MIN_LENGTH
            )
        elif key_type.lower() == "openai":
            return (
                key.startswith(SecurityConfig.OPENAI_API_KEY_PREFIX) and
                len(key) >= SecurityConfig.OPENAI_API_KEY_MIN_LENGTH
            )
        
        return False
    
    @staticmethod
    def is_suspicious_user_agent(user_agent: str) -> bool:
        """
        Check if user agent appears suspicious.
        
        Args:
            user_agent: User agent string to check
            
        Returns:
            True if user agent is suspicious
        """
        if not user_agent:
            return True
        
        user_agent_lower = user_agent.lower()
        return any(
            blocked_agent in user_agent_lower 
            for blocked_agent in SecurityConfig.BLOCKED_USER_AGENTS
        )
    
    @staticmethod
    def contains_suspicious_patterns(text: str) -> List[str]:
        """
        Check text for suspicious patterns that might indicate attacks.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of suspicious patterns found
        """
        import re
        
        if not text:
            return []
        
        found_patterns = []
        for pattern in SecurityConfig.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                found_patterns.append(pattern)
        
        return found_patterns
    
    @staticmethod
    def validate_cors_origins(origins: List[str], is_production: bool) -> bool:
        """
        Validate CORS origins configuration.
        
        Args:
            origins: List of allowed origins
            is_production: Whether running in production mode
            
        Returns:
            True if configuration is valid
        """
        if is_production and "*" in origins:
            return False
        
        return True
    
    @staticmethod
    def get_security_level_config(level: SecurityLevel) -> Dict[str, Any]:
        """
        Get security configuration for a specific security level.
        
        Args:
            level: Security level
            
        Returns:
            Dictionary of security settings
        """
        base_config = {
            "rate_limit_per_minute": SecurityConfig.DEFAULT_RATE_LIMIT_PER_MINUTE,
            "rate_limit_per_hour": SecurityConfig.DEFAULT_RATE_LIMIT_PER_HOUR,
            "burst_limit": SecurityConfig.DEFAULT_BURST_LIMIT,
            "max_request_size_mb": SecurityConfig.MAX_REQUEST_SIZE_MB,
            "enable_ip_blocking": True,
            "enable_input_sanitization": True,
            "blocked_user_agents": SecurityConfig.BLOCKED_USER_AGENTS.copy(),
        }
        
        if level == SecurityLevel.DEVELOPMENT:
            base_config.update({
                "enable_ip_blocking": False,
                "blocked_user_agents": [],  # Allow all user agents in dev
                "rate_limit_per_minute": 1000,  # Higher limits for dev
                "rate_limit_per_hour": 10000,
            })
        elif level == SecurityLevel.STAGING:
            base_config.update({
                "rate_limit_per_minute": 120,  # Slightly higher for testing
                "rate_limit_per_hour": 2000,
            })
        elif level == SecurityLevel.PRODUCTION:
            # Use strict defaults
            pass
        
        return base_config


class SecurityAuditLogger:
    """Logger for security-related events."""
    
    def __init__(self, logger):
        self.logger = logger
    
    def log_rate_limit_violation(self, client_ip: str, violation_type: str, count: int):
        """Log rate limit violations."""
        self.logger.warning(
            f"SECURITY: Rate limit violation from {client_ip}. "
            f"Type: {violation_type}, Count: {count}"
        )
    
    def log_suspicious_request(self, client_ip: str, reason: str, details: str):
        """Log suspicious requests."""
        self.logger.warning(
            f"SECURITY: Suspicious request from {client_ip}. "
            f"Reason: {reason}, Details: {details}"
        )
    
    def log_blocked_request(self, client_ip: str, user_agent: str, reason: str):
        """Log blocked requests."""
        self.logger.warning(
            f"SECURITY: Blocked request from {client_ip}. "
            f"User-Agent: {user_agent}, Reason: {reason}"
        )
    
    def log_api_key_validation_failure(self, key_type: str, error: str):
        """Log API key validation failures."""
        self.logger.error(
            f"SECURITY: API key validation failed for {key_type}. "
            f"Error: {error}"
        )
    
    def log_input_sanitization(self, field: str, original_length: int, sanitized_length: int):
        """Log input sanitization events."""
        self.logger.info(
            f"SECURITY: Input sanitized for field '{field}'. "
            f"Original length: {original_length}, Sanitized length: {sanitized_length}"
        )


def get_security_config_for_environment(debug: bool = False) -> Dict[str, Any]:
    """
    Get security configuration based on environment.
    
    Args:
        debug: Whether running in debug mode
        
    Returns:
        Security configuration dictionary
    """
    if debug:
        level = SecurityLevel.DEVELOPMENT
    else:
        level = SecurityLevel.PRODUCTION
    
    return SecurityValidator.get_security_level_config(level)


def validate_security_settings(settings) -> List[str]:
    """
    Validate security settings and return list of issues found.
    
    Args:
        settings: Application settings object
        
    Returns:
        List of security issues found
    """
    issues = []
    
    # Validate API keys
    if not SecurityValidator.is_valid_api_key_format(settings.groq_api_key, "groq"):
        issues.append("Invalid GROQ API key format")
    
    if not SecurityValidator.is_valid_api_key_format(settings.openai_api_key, "openai"):
        issues.append("Invalid OPENAI API key format")
    
    # Validate CORS settings
    if not SecurityValidator.validate_cors_origins(settings.cors_origins, not settings.debug):
        issues.append("CORS origins set to '*' in production mode")
    
    # Validate timeout settings
    if settings.request_timeout > SecurityConfig.MAX_REQUEST_TIMEOUT_SECONDS:
        issues.append(f"Request timeout too high: {settings.request_timeout}s")
    
    # Validate source limits
    if settings.max_sources > SecurityConfig.MAX_SOURCES_LIMIT:
        issues.append(f"Max sources too high: {settings.max_sources}")
    
    return issues