"""
FastAPI exception handlers for comprehensive error handling.

This module provides centralized exception handling for all custom
exception types, ensuring consistent error responses across the API.
"""

import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException

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
from app.config.logging import get_logger

logger = get_logger(__name__)


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: dict = None,
    correlation_id: str = None,
    suggestions: list = None
) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        correlation_id: Request correlation ID
        suggestions: Suggestions for resolving the error
        
    Returns:
        JSONResponse with standardized error format
    """
    content = {
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "timestamp": time.time(),
        "correlation_id": correlation_id
    }
    
    if suggestions:
        content["suggestions"] = suggestions
    
    headers = {}
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Set up all exception handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(APIKeyMissingException)
    async def api_key_missing_handler(request: Request, exc: APIKeyMissingException):
        """Handle missing API key exceptions."""
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        suggestions = [
            "Check that all required API keys are set in environment variables",
            "Verify API key format and validity",
            "Ensure .env file is properly loaded",
            "Contact administrator if API keys should be configured"
        ]
        
        logger.error(
            f"API key missing: {exc.message} - Correlation ID: {correlation_id}",
            extra={"correlation_id": correlation_id, "details": exc.details}
        )
        
        return create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=exc.details,
            correlation_id=correlation_id,
            suggestions=suggestions
        )
    
    @app.exception_handler(DataSourceException)
    async def data_source_handler(request: Request, exc: DataSourceException):
        """Handle data source exceptions."""
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        suggestions = [
            "Check internet connectivity",
            "Verify that external services are operational",
            "Try again in a few moments",
            "Contact support if the issue persists"
        ]
        
        # Add specific suggestions based on the data source
        if 'source_name' in exc.details:
            source = exc.details['source_name']
            if 'yahoo' in source.lower():
                suggestions.append("Check Yahoo Finance service status")
            elif 'duckduckgo' in source.lower():
                suggestions.append("Check DuckDuckGo search service availability")
        
        logger.error(
            f"Data source error: {exc.message} - Correlation ID: {correlation_id}",
            extra={"correlation_id": correlation_id, "details": exc.details}
        )
        
        return create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=exc.details,
            correlation_id=correlation_id,
            suggestions=suggestions
        )
    
    @app.exception_handler(ValidationException)
    async def validation_handler(request: Request, exc: ValidationException):
        """Handle validation exceptions."""
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        suggestions = [
            "Check input format and requirements",
            "Ensure all required fields are provided",
            "Verify data types match expected formats",
            "Review API documentation for correct input structure"
        ]
        
        logger.warning(
            f"Validation error: {exc.message} - Correlation ID: {correlation_id}",
            extra={"correlation_id": correlation_id, "details": exc.details}
        )
        
        return create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=exc.details,
            correlation_id=correlation_id,
            suggestions=suggestions
        )
    
    @app.exception_handler(AgentProcessingException)
    async def agent_processing_handler(request: Request, exc: AgentProcessingException):
        """Handle agent processing exceptions."""
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        suggestions = [
            "Try simplifying your request",
            "Check if the requested analysis type is supported",
            "Retry the request after a short delay",
            "Contact support if the issue persists"
        ]
        
        logger.error(
            f"Agent processing error: {exc.message} - Correlation ID: {correlation_id}",
            extra={"correlation_id": correlation_id, "details": exc.details}
        )
        
        return create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=exc.details,
            correlation_id=correlation_id,
            suggestions=suggestions
        )
    
    @app.exception_handler(RateLimitException)
    async def rate_limit_handler(request: Request, exc: RateLimitException):
        """Handle rate limit exceptions."""
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        retry_after = exc.details.get('retry_after', 60)
        suggestions = [
            f"Wait {retry_after} seconds before making another request",
            "Reduce the frequency of API calls",
            "Consider upgrading to a higher rate limit tier",
            "Implement client-side rate limiting"
        ]
        
        logger.warning(
            f"Rate limit exceeded: {exc.message} - Correlation ID: {correlation_id}",
            extra={"correlation_id": correlation_id, "details": exc.details}
        )
        
        headers = {"Retry-After": str(retry_after)}
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": time.time(),
                "correlation_id": correlation_id,
                "suggestions": suggestions
            },
            headers=headers
        )
    
    @app.exception_handler(TimeoutException)
    async def timeout_handler(request: Request, exc: TimeoutException):
        """Handle timeout exceptions."""
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        suggestions = [
            "Try reducing the scope of your request",
            "Retry the request after a short delay",
            "Consider breaking large requests into smaller parts",
            "Check if the service is experiencing high load"
        ]
        
        logger.error(
            f"Timeout error: {exc.message} - Correlation ID: {correlation_id}",
            extra={"correlation_id": correlation_id, "details": exc.details}
        )
        
        return create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            details=exc.details,
            correlation_id=correlation_id,
            suggestions=suggestions
        )
    
    @app.exception_handler(ConfigurationException)
    async def configuration_handler(request: Request, exc: ConfigurationException):
        """Handle configuration exceptions."""
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        suggestions = [
            "Check system configuration settings",
            "Verify environment variables are properly set",
            "Contact administrator to review configuration",
            "Restart the service after configuration changes"
        ]
        
        logger.error(
            f"Configuration error: {exc.message} - Correlation ID: {correlation_id}",
            extra={"correlation_id": correlation_id, "details": exc.details}
        )
        
        return create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=exc.details,
            correlation_id=correlation_id,
            suggestions=suggestions
        )
    
    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic request validation errors."""
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        # Extract detailed validation errors
        validation_details = []
        for error in exc.errors():
            validation_details.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input")
            })
        
        suggestions = [
            "Check the request format against API documentation",
            "Ensure all required fields are provided",
            "Verify data types match expected formats",
            "Review field validation requirements"
        ]
        
        logger.warning(
            f"Request validation error - Correlation ID: {correlation_id}",
            extra={"correlation_id": correlation_id, "validation_errors": validation_details}
        )
        
        return create_error_response(
            error_code="REQUEST_VALIDATION_ERROR",
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": validation_details},
            correlation_id=correlation_id,
            suggestions=suggestions
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle standard HTTP exceptions."""
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail} - Correlation ID: {correlation_id}",
            extra={"correlation_id": correlation_id, "status_code": exc.status_code}
        )
        
        return create_error_response(
            error_code="HTTP_ERROR",
            message=exc.detail,
            status_code=exc.status_code,
            correlation_id=correlation_id
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle all other unhandled exceptions."""
        correlation_id = getattr(request.state, 'correlation_id', None)
        
        suggestions = [
            "Try the request again",
            "Check if the service is operational",
            "Contact support with the correlation ID if the issue persists"
        ]
        
        logger.error(
            f"Unhandled exception: {type(exc).__name__} - {str(exc)} - Correlation ID: {correlation_id}",
            exc_info=True,
            extra={"correlation_id": correlation_id}
        )
        
        return create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            correlation_id=correlation_id,
            suggestions=suggestions
        )