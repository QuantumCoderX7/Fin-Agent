"""
FastAPI middleware for error handling and request processing.
"""

import uuid
import time
import re
from typing import Callable, Dict, List
from collections import defaultdict
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

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
from app.utils.validators import InputValidator

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with multiple tiers and security features."""
    
    def __init__(
        self, 
        app, 
        calls_per_minute: int = 60,
        calls_per_hour: int = 1000,
        burst_limit: int = 10,
        enable_ip_blocking: bool = True
    ):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
        self.burst_limit = burst_limit
        self.enable_ip_blocking = enable_ip_blocking
        
        # Track requests per IP
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
        self.burst_requests: Dict[str, list] = defaultdict(list)
        
        # Track blocked IPs
        self.blocked_ips: Dict[str, float] = {}  # IP -> block_until_timestamp
        self.violation_counts: Dict[str, int] = defaultdict(int)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply multi-tier rate limiting with security features."""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Check if IP is currently blocked
        if self._is_ip_blocked(client_ip, current_time):
            block_until = self.blocked_ips[client_ip]
            remaining_time = int(block_until - current_time)
            raise RateLimitException(
                f"IP {client_ip} is temporarily blocked due to rate limit violations. "
                f"Try again in {remaining_time} seconds.",
                details={
                    "blocked_until": block_until,
                    "remaining_seconds": remaining_time,
                    "violation_count": self.violation_counts[client_ip]
                }
            )
        
        # Clean old requests
        self._clean_old_requests(client_ip, current_time)
        
        # Check burst limit (last 10 seconds)
        if self._check_burst_limit(client_ip, current_time):
            self._handle_rate_limit_violation(client_ip, current_time, "burst")
            raise RateLimitException(
                f"Burst rate limit exceeded. Maximum {self.burst_limit} requests per 10 seconds.",
                details={
                    "limit_type": "burst",
                    "limit": self.burst_limit,
                    "window": "10 seconds"
                }
            )
        
        # Check minute limit
        if len(self.minute_requests[client_ip]) >= self.calls_per_minute:
            self._handle_rate_limit_violation(client_ip, current_time, "minute")
            raise RateLimitException(
                f"Rate limit exceeded. Maximum {self.calls_per_minute} requests per minute.",
                details={
                    "limit_type": "minute", 
                    "limit": self.calls_per_minute,
                    "window": "1 minute"
                }
            )
        
        # Check hour limit
        if len(self.hour_requests[client_ip]) >= self.calls_per_hour:
            self._handle_rate_limit_violation(client_ip, current_time, "hour")
            raise RateLimitException(
                f"Hourly rate limit exceeded. Maximum {self.calls_per_hour} requests per hour.",
                details={
                    "limit_type": "hour",
                    "limit": self.calls_per_hour, 
                    "window": "1 hour"
                }
            )
        
        # Record the request
        self.minute_requests[client_ip].append(current_time)
        self.hour_requests[client_ip].append(current_time)
        self.burst_requests[client_ip].append(current_time)
        
        # Add rate limit headers to response
        response = await call_next(request)
        self._add_rate_limit_headers(response, client_ip)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP with support for proxy headers."""
        # Check for forwarded headers (common in production deployments)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _is_ip_blocked(self, client_ip: str, current_time: float) -> bool:
        """Check if IP is currently blocked."""
        if client_ip in self.blocked_ips:
            if current_time < self.blocked_ips[client_ip]:
                return True
            else:
                # Block expired, remove it
                del self.blocked_ips[client_ip]
        return False
    
    def _clean_old_requests(self, client_ip: str, current_time: float) -> None:
        """Clean old request records."""
        # Clean minute requests (older than 1 minute)
        self.minute_requests[client_ip] = [
            req_time for req_time in self.minute_requests[client_ip]
            if current_time - req_time < 60
        ]
        
        # Clean hour requests (older than 1 hour)
        self.hour_requests[client_ip] = [
            req_time for req_time in self.hour_requests[client_ip]
            if current_time - req_time < 3600
        ]
        
        # Clean burst requests (older than 10 seconds)
        self.burst_requests[client_ip] = [
            req_time for req_time in self.burst_requests[client_ip]
            if current_time - req_time < 10
        ]
    
    def _check_burst_limit(self, client_ip: str, current_time: float) -> bool:
        """Check if burst limit is exceeded."""
        return len(self.burst_requests[client_ip]) >= self.burst_limit
    
    def _handle_rate_limit_violation(self, client_ip: str, current_time: float, limit_type: str) -> None:
        """Handle rate limit violations with progressive blocking."""
        if not self.enable_ip_blocking:
            return
        
        self.violation_counts[client_ip] += 1
        violation_count = self.violation_counts[client_ip]
        
        # Progressive blocking: longer blocks for repeat offenders
        if violation_count >= 5:
            # Block for 1 hour after 5 violations
            block_duration = 3600
        elif violation_count >= 3:
            # Block for 10 minutes after 3 violations
            block_duration = 600
        elif violation_count >= 2:
            # Block for 2 minutes after 2 violations
            block_duration = 120
        else:
            # Block for 30 seconds on first violation
            block_duration = 30
        
        self.blocked_ips[client_ip] = current_time + block_duration
        
        logger.warning(
            f"Rate limit violation from IP {client_ip}. "
            f"Limit type: {limit_type}, Violation count: {violation_count}, "
            f"Blocked for {block_duration} seconds."
        )
    
    def _add_rate_limit_headers(self, response: Response, client_ip: str) -> None:
        """Add rate limit information to response headers."""
        minute_remaining = max(0, self.calls_per_minute - len(self.minute_requests[client_ip]))
        hour_remaining = max(0, self.calls_per_hour - len(self.hour_requests[client_ip]))
        
        response.headers["X-RateLimit-Limit-Minute"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(minute_remaining)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.calls_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(hour_remaining)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions and errors."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle exceptions."""
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Add correlation ID to response headers
        start_time = time.time()
        
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            
            # Log request completion
            process_time = time.time() - start_time
            logger.info(
                f"Request completed - {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Time: {process_time:.3f}s - "
                f"Correlation ID: {correlation_id}"
            )
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            
            # Log the exception
            logger.error(
                f"Request failed - {request.method} {request.url.path} - "
                f"Error: {str(exc)} - Time: {process_time:.3f}s - "
                f"Correlation ID: {correlation_id}",
                exc_info=True
            )
            
            # Handle specific exception types
            if isinstance(exc, APIKeyMissingException):
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "error_code": "API_KEY_MISSING",
                        "message": str(exc),
                        "details": exc.details,
                        "timestamp": time.time(),
                        "correlation_id": correlation_id
                    },
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            elif isinstance(exc, ValidationException):
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "error_code": "VALIDATION_ERROR",
                        "message": str(exc),
                        "details": exc.details,
                        "timestamp": time.time(),
                        "correlation_id": correlation_id
                    },
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            elif isinstance(exc, DataSourceException):
                return JSONResponse(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    content={
                        "error_code": "DATA_SOURCE_ERROR",
                        "message": str(exc),
                        "details": exc.details,
                        "timestamp": time.time(),
                        "correlation_id": correlation_id
                    },
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            elif isinstance(exc, AgentProcessingException):
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error_code": "AGENT_PROCESSING_ERROR",
                        "message": str(exc),
                        "details": exc.details,
                        "timestamp": time.time(),
                        "correlation_id": correlation_id
                    },
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            elif isinstance(exc, RateLimitException):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": str(exc),
                        "details": exc.details,
                        "timestamp": time.time(),
                        "correlation_id": correlation_id
                    },
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            elif isinstance(exc, ConfigurationException):
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error_code": "CONFIGURATION_ERROR",
                        "message": str(exc),
                        "details": exc.details,
                        "timestamp": time.time(),
                        "correlation_id": correlation_id
                    },
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            elif isinstance(exc, TimeoutException):
                return JSONResponse(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    content={
                        "error_code": "TIMEOUT_ERROR",
                        "message": str(exc),
                        "details": exc.details,
                        "timestamp": time.time(),
                        "correlation_id": correlation_id
                    },
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            elif isinstance(exc, HTTPException):
                return JSONResponse(
                    status_code=exc.status_code,
                    content={
                        "error_code": "HTTP_ERROR",
                        "message": exc.detail,
                        "details": {},
                        "timestamp": time.time(),
                        "correlation_id": correlation_id
                    },
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            else:
                # Generic error handling
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {},
                        "timestamp": time.time(),
                        "correlation_id": correlation_id
                    },
                    headers={"X-Correlation-ID": correlation_id}
                )


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation and sanitization."""
    
    def __init__(
        self,
        app,
        max_request_size_mb: float = 10.0,
        enable_input_sanitization: bool = True,
        blocked_user_agents: List[str] = None
    ):
        super().__init__(app)
        self.max_request_size_mb = max_request_size_mb
        self.enable_input_sanitization = enable_input_sanitization
        self.blocked_user_agents = blocked_user_agents or [
            "curl",  # Block basic curl requests in production
            "wget", 
            "python-requests",  # Block basic Python requests
            "bot",
            "crawler",
            "spider"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply security validations to incoming requests."""
        
        # Check user agent for suspicious patterns
        self._validate_user_agent(request)
        
        # Validate request headers
        self._validate_headers(request)
        
        # Check request size before processing
        await self._validate_request_size(request)
        
        # Sanitize query parameters
        if self.enable_input_sanitization:
            self._sanitize_query_params(request)
        
        return await call_next(request)
    
    def _validate_user_agent(self, request: Request) -> None:
        """Validate user agent to block suspicious requests."""
        user_agent = request.headers.get("User-Agent", "").lower()
        
        # Block empty user agents
        if not user_agent:
            raise ValidationException(
                "user_agent",
                "User-Agent header is required for security purposes."
            )
        
        # Check against blocked user agents
        for blocked_agent in self.blocked_user_agents:
            if blocked_agent.lower() in user_agent:
                raise ValidationException(
                    "user_agent", 
                    f"User agent '{blocked_agent}' is not allowed. "
                    f"Please use a standard web browser or API client."
                )
    
    def _validate_headers(self, request: Request) -> None:
        """Validate request headers for security issues."""
        
        # Check for suspicious headers that might indicate attacks
        suspicious_headers = [
            "X-Forwarded-Host",  # Potential host header injection
            "X-Original-URL",    # Potential URL manipulation
            "X-Rewrite-URL"      # Potential URL rewriting attacks
        ]
        
        for header in suspicious_headers:
            if header in request.headers:
                logger.warning(
                    f"Suspicious header detected: {header} = {request.headers[header]} "
                    f"from IP {request.client.host if request.client else 'unknown'}"
                )
        
        # Validate Content-Type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("Content-Type", "")
            if not content_type:
                raise ValidationException(
                    "content_type",
                    "Content-Type header is required for data submission."
                )
            
            # Only allow specific content types
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data"
            ]
            
            if not any(allowed_type in content_type for allowed_type in allowed_types):
                raise ValidationException(
                    "content_type",
                    f"Content-Type '{content_type}' is not allowed. "
                    f"Allowed types: {', '.join(allowed_types)}"
                )
    
    async def _validate_request_size(self, request: Request) -> None:
        """Validate request size to prevent DoS attacks."""
        content_length = request.headers.get("Content-Length")
        
        if content_length:
            try:
                size_bytes = int(content_length)
                size_mb = size_bytes / (1024 * 1024)
                
                if size_mb > self.max_request_size_mb:
                    raise ValidationException(
                        "request_size",
                        f"Request size ({size_mb:.2f} MB) exceeds maximum allowed "
                        f"size ({self.max_request_size_mb} MB)"
                    )
            except ValueError:
                raise ValidationException(
                    "content_length",
                    "Invalid Content-Length header value"
                )
    
    def _sanitize_query_params(self, request: Request) -> None:
        """Sanitize query parameters to prevent injection attacks."""
        if not request.query_params:
            return
        
        # Check for suspicious patterns in query parameters
        suspicious_patterns = [
            r'<script[^>]*>',  # Script injection
            r'javascript:',     # JavaScript URLs
            r'on\w+\s*=',      # Event handlers
            r'union\s+select',  # SQL injection
            r'drop\s+table',    # SQL injection
            r'exec\s*\(',       # Command injection
            r'eval\s*\(',       # Code injection
        ]
        
        for key, value in request.query_params.items():
            # Sanitize the value
            sanitized_value = InputValidator.sanitize_input(str(value))
            
            # Check for suspicious patterns
            for pattern in suspicious_patterns:
                if re.search(pattern, sanitized_value, re.IGNORECASE):
                    logger.warning(
                        f"Suspicious query parameter detected: {key}={value} "
                        f"from IP {request.client.host if request.client else 'unknown'}"
                    )
                    raise ValidationException(
                        f"query_param_{key}",
                        f"Query parameter '{key}' contains suspicious content"
                    )