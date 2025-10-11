"""
Dependency injection for FastAPI endpoints.
"""

from fastapi import Depends, HTTPException, status
from functools import lru_cache

from app.config.settings import get_settings, Settings
from app.utils.exceptions import APIKeyMissingException
from app.services.research_service import ResearchService
from app.services.stock_service import StockService
from app.services.evaluation_service import EvaluationService


def get_current_settings() -> Settings:
    """Get current application settings."""
    return get_settings()


def validate_api_keys(settings: Settings = Depends(get_current_settings)) -> Settings:
    """
    Validate that required API keys are available.
    
    Args:
        settings: Application settings
        
    Returns:
        Validated settings
        
    Raises:
        HTTPException: If API keys are missing
    """
    try:
        settings.validate_api_keys()
        return settings
    except APIKeyMissingException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


def get_research_service(settings: Settings = Depends(validate_api_keys)) -> ResearchService:
    """Get research service instance with validated API keys."""
    return ResearchService(
        groq_api_key=settings.groq_api_key,
        model_name=settings.default_model,
        timeout_seconds=settings.request_timeout
    )


def get_stock_service(settings: Settings = Depends(validate_api_keys)) -> StockService:
    """Get stock service instance with validated API keys."""
    return StockService(
        groq_api_key=settings.groq_api_key,
        model_name=settings.default_model,
        timeout_seconds=settings.request_timeout
    )


def get_evaluation_service(settings: Settings = Depends(validate_api_keys)) -> EvaluationService:
    """Get evaluation service instance with validated API keys."""
    return EvaluationService(
        groq_api_key=settings.groq_api_key,
        model_name=settings.default_model,
        timeout_seconds=settings.request_timeout
    )