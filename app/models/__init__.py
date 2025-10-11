"""
Pydantic models for the Financial AI Agents system.

This module contains all request and response models used by the API endpoints.
"""

from app.models.requests import (
    BaseRequest,
    ResearchRequest,
    StockAnalysisRequest,
    RAGEvaluationRequest,
    StreamingRequest,
    BatchRequest,
    AnalysisType,
    EvaluationCriteria
)

from app.models.responses import (
    BaseResponse,
    ErrorResponse,
    ResearchResponse,
    StockAnalysisResponse,
    RAGEvaluationResponse,
    StreamingResponse,
    BatchResponse,
    HealthResponse,
    AgentInfoResponse,
    ResponseStatus,
    SourceInfo,
    StockMetrics,
    StockAnalysis,
    EvaluationScore
)

__all__ = [
    # Request models
    "BaseRequest",
    "ResearchRequest", 
    "StockAnalysisRequest",
    "RAGEvaluationRequest",
    "StreamingRequest",
    "BatchRequest",
    "AnalysisType",
    "EvaluationCriteria",
    
    # Response models
    "BaseResponse",
    "ErrorResponse",
    "ResearchResponse",
    "StockAnalysisResponse", 
    "RAGEvaluationResponse",
    "StreamingResponse",
    "BatchResponse",
    "HealthResponse",
    "AgentInfoResponse",
    "ResponseStatus",
    "SourceInfo",
    "StockMetrics",
    "StockAnalysis",
    "EvaluationScore"
]