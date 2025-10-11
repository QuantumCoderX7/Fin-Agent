"""
Error handling and response formatting utilities.

This module provides utilities for handling exceptions and formatting
error responses consistently across the Financial AI Agents system.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.utils.exceptions import (
    FinancialAgentException,
    APIKeyMissingException,
    DataSourceException,
    ValidationException,
    AgentProcessingException,
    ConfigurationException,
    RateLimitException,
    TimeoutException
)
from app.models.responses import ErrorResponse


logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Centralized error handling and response formatting.
    
    This class provides methods for converting various exception types
    into standardized error responses with appropriate HTTP status codes.
    """
    
    # Mapping of exception types to HTTP status codes
    EXCEPTION_STATUS_CODES = {
        ValidationException: 400,
        APIKeyMissingException: 401,
        ConfigurationException: 500,
        DataSourceException: 502,
        AgentProcessingException: 500,
        RateLimitException: 429,
        TimeoutException: 504,
        ValidationError: 422,
        HTTPException: None,  # Use the exception's status_code
        Exception: 500,  # Generic server error
    }
    
    @staticmethod
    def create_error_response(
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """
        Create a standardized error response.
        
        Args:
            error_code: Machine-readable error code
            message: Human-readable error message
            details: Additional error details
            suggestions: Suggestions for resolving the error
            request_id: Request ID for tracking
            
        Returns:
            ErrorResponse instance
        """
        return ErrorResponse(
            error_code=error_code,
            message=message,
            details=details or {},
            suggestions=suggestions or [],
            request_id=request_id,
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def handle_financial_agent_exception(
        exc: FinancialAgentException,
        request_id: Optional[str] = None
    ) -> tuple[ErrorResponse, int]:
        """
        Handle FinancialAgentException and its subclasses.
        
        Args:
            exc: The exception to handle
            request_id: Optional request ID
            
        Returns:
            Tuple of (ErrorResponse, HTTP status code)
        """
        status_code = ErrorHandler.EXCEPTION_STATUS_CODES.get(
            type(exc), 500
        )
        
        suggestions = ErrorHandler._get_error_suggestions(exc)
        
        error_response = ErrorHandler.create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            suggestions=suggestions,
            request_id=request_id
        )
        
        return error_response, status_code 
   
    @staticmethod
    def handle_validation_error(
        exc: ValidationError,
        request_id: Optional[str] = None
    ) -> tuple[ErrorResponse, int]:
        """
        Handle Pydantic ValidationError.
        
        Args:
            exc: The validation error to handle
            request_id: Optional request ID
            
        Returns:
            Tuple of (ErrorResponse, HTTP status code)
        """
        # Extract validation error details
        error_details = {}
        for error in exc.errors():
            field_path = '.'.join(str(loc) for loc in error['loc'])
            error_details[field_path] = {
                'message': error['msg'],
                'type': error['type'],
                'input': error.get('input')
            }
        
        suggestions = [
            "Check the request format and ensure all required fields are provided",
            "Verify that field values meet the specified constraints",
            "Refer to the API documentation for correct request structure"
        ]
        
        error_response = ErrorHandler.create_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"validation_errors": error_details},
            suggestions=suggestions,
            request_id=request_id
        )
        
        return error_response, 422
    
    @staticmethod
    def handle_http_exception(
        exc: HTTPException,
        request_id: Optional[str] = None
    ) -> tuple[ErrorResponse, int]:
        """
        Handle FastAPI HTTPException.
        
        Args:
            exc: The HTTP exception to handle
            request_id: Optional request ID
            
        Returns:
            Tuple of (ErrorResponse, HTTP status code)
        """
        error_response = ErrorHandler.create_error_response(
            error_code=f"HTTP_{exc.status_code}",
            message=exc.detail,
            request_id=request_id
        )
        
        return error_response, exc.status_code
    
    @staticmethod
    def handle_generic_exception(
        exc: Exception,
        request_id: Optional[str] = None,
        include_traceback: bool = False
    ) -> tuple[ErrorResponse, int]:
        """
        Handle generic exceptions.
        
        Args:
            exc: The exception to handle
            request_id: Optional request ID
            include_traceback: Whether to include traceback in details
            
        Returns:
            Tuple of (ErrorResponse, HTTP status code)
        """
        details = {"exception_type": type(exc).__name__}
        
        if include_traceback:
            details["traceback"] = traceback.format_exc()
        
        suggestions = [
            "This appears to be an internal server error",
            "Please try again later or contact support if the issue persists",
            "Check the request format and parameters"
        ]
        
        error_response = ErrorHandler.create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details=details,
            suggestions=suggestions,
            request_id=request_id
        )
        
        return error_response, 500    

    @staticmethod
    def _get_error_suggestions(exc: FinancialAgentException) -> List[str]:
        """
        Get context-specific suggestions for resolving errors.
        
        Args:
            exc: The exception to get suggestions for
            
        Returns:
            List of suggestion strings
        """
        if isinstance(exc, APIKeyMissingException):
            return [
                f"Set the {exc.details.get('api_key_name', 'required')} environment variable",
                "Check your .env file or environment configuration",
                "Ensure API keys are properly formatted and valid"
            ]
        
        elif isinstance(exc, DataSourceException):
            source_name = exc.details.get('source_name', 'external service')
            return [
                f"Check if {source_name} is currently available",
                "Verify your internet connection",
                "Try again in a few moments as this may be a temporary issue",
                "Check if API rate limits have been exceeded"
            ]
        
        elif isinstance(exc, ValidationException):
            field_name = exc.details.get('field_name', 'input field')
            return [
                f"Check the format and constraints for {field_name}",
                "Refer to the API documentation for valid input formats",
                "Ensure all required fields are provided"
            ]
        
        elif isinstance(exc, AgentProcessingException):
            return [
                "Check if the request parameters are valid",
                "Verify that required external services are available",
                "Try simplifying the request or breaking it into smaller parts"
            ]
        
        elif isinstance(exc, RateLimitException):
            retry_after = exc.details.get('retry_after')
            suggestions = [
                "Reduce the frequency of requests",
                "Implement exponential backoff in your client"
            ]
            if retry_after:
                suggestions.append(f"Wait {retry_after} seconds before retrying")
            return suggestions
        
        elif isinstance(exc, TimeoutException):
            return [
                "Try reducing the scope of your request",
                "Check your network connection",
                "Consider breaking large requests into smaller chunks"
            ]
        
        else:
            return [
                "Check the request format and parameters",
                "Refer to the API documentation",
                "Contact support if the issue persists"
            ]
    
    @staticmethod
    def log_error(
        exc: Exception,
        request: Optional[Request] = None,
        request_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log error with context information.
        
        Args:
            exc: The exception to log
            request: Optional FastAPI request object
            request_id: Optional request ID
            additional_context: Additional context to include in logs
        """
        context = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_id": request_id
        }
        
        if request:
            context.update({
                "method": request.method,
                "url": str(request.url),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            })
        
        if additional_context:
            context.update(additional_context)
        
        # Log at appropriate level based on exception type
        if isinstance(exc, (ValidationException, HTTPException)):
            logger.warning("Request validation error", extra=context)
        elif isinstance(exc, FinancialAgentException):
            logger.error("Financial agent error", extra=context)
        else:
            logger.error("Unexpected error", extra=context, exc_info=True)


async def create_error_handler_middleware():
    """
    Create FastAPI middleware for centralized error handling.
    
    Returns:
        Middleware function for FastAPI
    """
    async def error_handler_middleware(request: Request, call_next):
        """Middleware function to handle errors consistently."""
        request_id = request.headers.get("x-request-id")
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # Log the error
            ErrorHandler.log_error(exc, request, request_id)
            
            # Handle different exception types
            if isinstance(exc, FinancialAgentException):
                error_response, status_code = ErrorHandler.handle_financial_agent_exception(
                    exc, request_id
                )
            elif isinstance(exc, ValidationError):
                error_response, status_code = ErrorHandler.handle_validation_error(
                    exc, request_id
                )
            elif isinstance(exc, HTTPException):
                error_response, status_code = ErrorHandler.handle_http_exception(
                    exc, request_id
                )
            else:
                error_response, status_code = ErrorHandler.handle_generic_exception(
                    exc, request_id
                )
            
            return JSONResponse(
                status_code=status_code,
                content=error_response.dict()
            )
    
    return error_handler_middleware


def create_exception_handlers() -> Dict[Any, callable]:
    """
    Create exception handlers for FastAPI application.
    
    Returns:
        Dictionary of exception handlers
    """
    async def financial_agent_exception_handler(request: Request, exc: FinancialAgentException):
        """Handle FinancialAgentException."""
        request_id = request.headers.get("x-request-id")
        ErrorHandler.log_error(exc, request, request_id)
        
        error_response, status_code = ErrorHandler.handle_financial_agent_exception(
            exc, request_id
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
        )
    
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic ValidationError."""
        request_id = request.headers.get("x-request-id")
        ErrorHandler.log_error(exc, request, request_id)
        
        error_response, status_code = ErrorHandler.handle_validation_error(
            exc, request_id
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
        )
    
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTPException."""
        request_id = request.headers.get("x-request-id")
        ErrorHandler.log_error(exc, request, request_id)
        
        error_response, status_code = ErrorHandler.handle_http_exception(
            exc, request_id
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
        )
    
    return {
        FinancialAgentException: financial_agent_exception_handler,
        ValidationError: validation_exception_handler,
        HTTPException: http_exception_handler,
    }