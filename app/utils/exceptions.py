"""
Custom exception classes for the Financial AI Agents system.

This module defines all custom exceptions used throughout the system,
providing specific error types for different failure scenarios.
"""

from typing import Optional, Dict, Any


class FinancialAgentException(Exception):
    """
    Base exception for all financial agent system errors.
    
    This is the root exception class that all other custom exceptions
    inherit from, providing a common interface for error handling.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


class APIKeyMissingException(FinancialAgentException):
    """
    Raised when required API keys are missing or invalid.
    
    This exception is thrown during system startup or when attempting
    to use external services without proper authentication.
    """
    
    def __init__(self, api_key_name: str, message: Optional[str] = None):
        """
        Initialize the API key missing exception.
        
        Args:
            api_key_name: Name of the missing API key
            message: Optional custom message
        """
        default_message = f"Required API key '{api_key_name}' is missing or invalid"
        super().__init__(
            message or default_message,
            error_code="API_KEY_MISSING",
            details={"api_key_name": api_key_name}
        )


class DataSourceException(FinancialAgentException):
    """
    Raised when external data sources fail or return invalid data.
    
    This exception covers failures from external APIs like Yahoo Finance,
    DuckDuckGo, or other financial data providers.
    """
    
    def __init__(
        self, 
        source_name: str, 
        message: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        """
        Initialize the data source exception.
        
        Args:
            source_name: Name of the failing data source
            message: Optional custom message
            status_code: HTTP status code if applicable
        """
        default_message = f"Data source '{source_name}' failed to provide data"
        details = {"source_name": source_name}
        if status_code:
            details["status_code"] = status_code
            
        super().__init__(
            message or default_message,
            error_code="DATA_SOURCE_FAILURE",
            details=details
        )


class ValidationException(FinancialAgentException):
    """
    Raised when input validation fails.
    
    This exception is thrown when user input doesn't meet the required
    format, constraints, or business rules.
    """
    
    def __init__(
        self, 
        field_name: str, 
        message: Optional[str] = None,
        validation_errors: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the validation exception.
        
        Args:
            field_name: Name of the field that failed validation
            message: Optional custom message
            validation_errors: Detailed validation error information
        """
        default_message = f"Validation failed for field '{field_name}'"
        details = {"field_name": field_name}
        if validation_errors:
            details["validation_errors"] = validation_errors
            
        super().__init__(
            message or default_message,
            error_code="VALIDATION_FAILED",
            details=details
        )


class AgentProcessingException(FinancialAgentException):
    """
    Raised when agent processing fails.
    
    This exception covers failures during the core agent processing,
    such as LLM API failures, tool execution errors, or analysis failures.
    """
    
    def __init__(
        self, 
        agent_name: str, 
        message: Optional[str] = None,
        processing_stage: Optional[str] = None
    ):
        """
        Initialize the agent processing exception.
        
        Args:
            agent_name: Name of the agent that failed
            message: Optional custom message
            processing_stage: Stage where processing failed
        """
        default_message = f"Agent '{agent_name}' failed during processing"
        details = {"agent_name": agent_name}
        if processing_stage:
            details["processing_stage"] = processing_stage
            
        super().__init__(
            message or default_message,
            error_code="AGENT_PROCESSING_FAILED",
            details=details
        )


class ConfigurationException(FinancialAgentException):
    """
    Raised when system configuration is invalid or incomplete.
    
    This exception is thrown when required configuration parameters
    are missing or have invalid values.
    """
    
    def __init__(
        self, 
        config_key: str, 
        message: Optional[str] = None,
        expected_type: Optional[str] = None
    ):
        """
        Initialize the configuration exception.
        
        Args:
            config_key: Configuration key that is invalid
            message: Optional custom message
            expected_type: Expected type for the configuration value
        """
        default_message = f"Invalid configuration for '{config_key}'"
        details = {"config_key": config_key}
        if expected_type:
            details["expected_type"] = expected_type
            
        super().__init__(
            message or default_message,
            error_code="CONFIGURATION_INVALID",
            details=details
        )


class RateLimitException(FinancialAgentException):
    """
    Raised when API rate limits are exceeded.
    
    This exception is thrown when external APIs return rate limit
    errors or when internal rate limiting is triggered.
    """
    
    def __init__(
        self, 
        service_name: str, 
        message: Optional[str] = None,
        retry_after: Optional[int] = None
    ):
        """
        Initialize the rate limit exception.
        
        Args:
            service_name: Name of the service that hit rate limits
            message: Optional custom message
            retry_after: Seconds to wait before retrying
        """
        default_message = f"Rate limit exceeded for service '{service_name}'"
        details = {"service_name": service_name}
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(
            message or default_message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )


class TimeoutException(FinancialAgentException):
    """
    Raised when operations timeout.
    
    This exception is thrown when agent processing or external API
    calls exceed the configured timeout limits.
    """
    
    def __init__(
        self, 
        operation_name: str, 
        timeout_seconds: int,
        message: Optional[str] = None
    ):
        """
        Initialize the timeout exception.
        
        Args:
            operation_name: Name of the operation that timed out
            timeout_seconds: Timeout limit that was exceeded
            message: Optional custom message
        """
        default_message = f"Operation '{operation_name}' timed out after {timeout_seconds} seconds"
        super().__init__(
            message or default_message,
            error_code="OPERATION_TIMEOUT",
            details={
                "operation_name": operation_name,
                "timeout_seconds": timeout_seconds
            }
        )