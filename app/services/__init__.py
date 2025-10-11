"""
Service layer for the Financial AI Agents system.

This module provides business logic services that orchestrate agent operations,
handle error management, retry logic, and ensure consistent response formatting.
"""

# from .research_service import ResearchService  # ResearchAgent not implemented yet
from .stock_service import StockService
from .evaluation_service import EvaluationService

__all__ = [
    # "ResearchService",  # ResearchAgent not implemented yet
    "StockService", 
    "EvaluationService"
]