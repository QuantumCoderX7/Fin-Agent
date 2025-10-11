"""
Input validation utilities for the Financial AI Agents system.

This module provides validation functions and utilities for ensuring
data integrity and security across all agent operations.
"""

import re
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.utils.exceptions import ValidationException


class InputValidator:
    """
    Utility class for input validation across the system.
    
    This class provides static methods for validating various types
    of input data used throughout the financial agents system.
    """
    
    # Regular expressions for common validations
    STOCK_SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,10}(\.[A-Z]{1,3})?(-[A-Z]{1,3})?$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    @staticmethod
    def validate_stock_symbol(symbol: str) -> str:
        """
        Validate and normalize a stock symbol.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            Normalized stock symbol
            
        Raises:
            ValidationException: If symbol is invalid
        """
        if not symbol or not isinstance(symbol, str):
            raise ValidationException(
                "symbol", 
                "Stock symbol must be a non-empty string"
            )
        
        # Clean and normalize
        symbol = symbol.strip().upper()
        
        if not symbol:
            raise ValidationException(
                "symbol", 
                "Stock symbol cannot be empty after normalization"
            )
        
        # Validate format
        if not InputValidator.STOCK_SYMBOL_PATTERN.match(symbol):
            raise ValidationException(
                "symbol",
                f"Invalid stock symbol format: {symbol}. "
                "Must be 1-10 uppercase letters, optionally followed by "
                "a dot and 1-3 letters, or a hyphen and 1-3 letters."
            )
        
        return symbol  
  
    @staticmethod
    def validate_stock_symbols(symbols: List[str]) -> List[str]:
        """
        Validate and normalize a list of stock symbols.
        
        Args:
            symbols: List of stock symbols to validate
            
        Returns:
            List of normalized stock symbols
            
        Raises:
            ValidationException: If any symbol is invalid
        """
        if not symbols or not isinstance(symbols, list):
            raise ValidationException(
                "symbols",
                "Stock symbols must be provided as a non-empty list"
            )
        
        validated_symbols = []
        for i, symbol in enumerate(symbols):
            try:
                validated_symbol = InputValidator.validate_stock_symbol(symbol)
                if validated_symbol not in validated_symbols:
                    validated_symbols.append(validated_symbol)
            except ValidationException as e:
                raise ValidationException(
                    f"symbols[{i}]",
                    f"Invalid symbol at position {i}: {e.message}"
                )
        
        if not validated_symbols:
            raise ValidationException(
                "symbols",
                "No valid stock symbols found after validation"
            )
        
        return validated_symbols
    
    @staticmethod
    def validate_text_input(
        text: str, 
        field_name: str,
        min_length: int = 1,
        max_length: int = 10000,
        allow_empty: bool = False
    ) -> str:
        """
        Validate text input with length constraints.
        
        Args:
            text: Text to validate
            field_name: Name of the field being validated
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            allow_empty: Whether to allow empty strings
            
        Returns:
            Validated and normalized text
            
        Raises:
            ValidationException: If text is invalid
        """
        if not isinstance(text, str):
            raise ValidationException(
                field_name,
                f"{field_name} must be a string"
            )
        
        # Normalize whitespace
        normalized_text = text.strip()
        
        if not allow_empty and not normalized_text:
            raise ValidationException(
                field_name,
                f"{field_name} cannot be empty"
            )
        
        if len(normalized_text) < min_length:
            raise ValidationException(
                field_name,
                f"{field_name} must be at least {min_length} characters long"
            )
        
        if len(normalized_text) > max_length:
            raise ValidationException(
                field_name,
                f"{field_name} must be no more than {max_length} characters long"
            )
        
        return normalized_text    

    @staticmethod
    def validate_url(url: str, field_name: str = "url") -> str:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            field_name: Name of the field being validated
            
        Returns:
            Validated URL
            
        Raises:
            ValidationException: If URL is invalid
        """
        if not isinstance(url, str):
            raise ValidationException(
                field_name,
                f"{field_name} must be a string"
            )
        
        url = url.strip()
        
        if not url:
            raise ValidationException(
                field_name,
                f"{field_name} cannot be empty"
            )
        
        if not InputValidator.URL_PATTERN.match(url):
            raise ValidationException(
                field_name,
                f"Invalid URL format: {url}"
            )
        
        return url
    
    @staticmethod
    def validate_numeric_range(
        value: Union[int, float],
        field_name: str,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        allow_none: bool = False
    ) -> Union[int, float, None]:
        """
        Validate numeric value within a specified range.
        
        Args:
            value: Numeric value to validate
            field_name: Name of the field being validated
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_none: Whether to allow None values
            
        Returns:
            Validated numeric value
            
        Raises:
            ValidationException: If value is invalid
        """
        if value is None:
            if allow_none:
                return None
            else:
                raise ValidationException(
                    field_name,
                    f"{field_name} cannot be None"
                )
        
        if not isinstance(value, (int, float)):
            raise ValidationException(
                field_name,
                f"{field_name} must be a number"
            )
        
        if min_value is not None and value < min_value:
            raise ValidationException(
                field_name,
                f"{field_name} must be at least {min_value}"
            )
        
        if max_value is not None and value > max_value:
            raise ValidationException(
                field_name,
                f"{field_name} must be no more than {max_value}"
            )
        
        return value  
  
    @staticmethod
    def validate_list_input(
        items: List[Any],
        field_name: str,
        min_items: int = 0,
        max_items: int = 100,
        item_validator: Optional[callable] = None
    ) -> List[Any]:
        """
        Validate list input with size constraints and optional item validation.
        
        Args:
            items: List to validate
            field_name: Name of the field being validated
            min_items: Minimum number of items required
            max_items: Maximum number of items allowed
            item_validator: Optional function to validate each item
            
        Returns:
            Validated list
            
        Raises:
            ValidationException: If list is invalid
        """
        if not isinstance(items, list):
            raise ValidationException(
                field_name,
                f"{field_name} must be a list"
            )
        
        if len(items) < min_items:
            raise ValidationException(
                field_name,
                f"{field_name} must contain at least {min_items} items"
            )
        
        if len(items) > max_items:
            raise ValidationException(
                field_name,
                f"{field_name} must contain no more than {max_items} items"
            )
        
        if item_validator:
            validated_items = []
            for i, item in enumerate(items):
                try:
                    validated_item = item_validator(item)
                    validated_items.append(validated_item)
                except Exception as e:
                    raise ValidationException(
                        f"{field_name}[{i}]",
                        f"Invalid item at position {i}: {str(e)}"
                    )
            return validated_items
        
        return items
    
    @staticmethod
    def validate_time_period(period: str, field_name: str = "time_period") -> str:
        """
        Validate time period format (e.g., '1y', '6m', '3d').
        
        Args:
            period: Time period string to validate
            field_name: Name of the field being validated
            
        Returns:
            Validated time period
            
        Raises:
            ValidationException: If time period is invalid
        """
        if not isinstance(period, str):
            raise ValidationException(
                field_name,
                f"{field_name} must be a string"
            )
        
        period = period.strip().lower()
        
        if not period:
            raise ValidationException(
                field_name,
                f"{field_name} cannot be empty"
            )
        
        # Valid time period pattern: number followed by unit (d, w, m, y)
        time_pattern = re.compile(r'^\d+[dwmy]$')
        
        if not time_pattern.match(period):
            raise ValidationException(
                field_name,
                f"Invalid time period format: {period}. "
                "Must be a number followed by 'd' (days), 'w' (weeks), "
                "'m' (months), or 'y' (years). Examples: '1y', '6m', '30d'"
            )
        
        return period    

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize input text to prevent injection attacks.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return str(text)
        
        # Remove potentially dangerous characters and patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
            r'<iframe[^>]*>.*?</iframe>',  # Iframe tags
        ]
        
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    @staticmethod
    def validate_request_size(data: Dict[str, Any], max_size_mb: float = 10.0) -> bool:
        """
        Validate that request data doesn't exceed size limits.
        
        Args:
            data: Request data to validate
            max_size_mb: Maximum size in megabytes
            
        Returns:
            True if size is acceptable
            
        Raises:
            ValidationException: If request is too large
        """
        import json
        import sys
        
        try:
            # Estimate size by serializing to JSON
            json_str = json.dumps(data, default=str)
            size_bytes = sys.getsizeof(json_str)
            size_mb = size_bytes / (1024 * 1024)
            
            if size_mb > max_size_mb:
                raise ValidationException(
                    "request_size",
                    f"Request size ({size_mb:.2f} MB) exceeds maximum allowed "
                    f"size ({max_size_mb} MB)"
                )
            
            return True
            
        except (TypeError, ValueError) as e:
            raise ValidationException(
                "request_format",
                f"Invalid request format: {str(e)}"
            )


def validate_pydantic_model(model_class, data: Dict[str, Any]) -> Any:
    """
    Validate data against a Pydantic model and return the validated instance.
    
    Args:
        model_class: Pydantic model class to validate against
        data: Data to validate
        
    Returns:
        Validated model instance
        
    Raises:
        ValidationException: If validation fails
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        # Convert Pydantic validation errors to our custom exception
        error_details = {}
        for error in e.errors():
            field_path = '.'.join(str(loc) for loc in error['loc'])
            error_details[field_path] = error['msg']
        
        raise ValidationException(
            "model_validation",
            f"Model validation failed for {model_class.__name__}",
            validation_errors=error_details
        )