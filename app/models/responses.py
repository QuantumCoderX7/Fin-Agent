"""
Pydantic response models for the Financial AI Agents system.

This module defines all response models used by the API endpoints,
providing structured output and documentation for each agent type.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """Enumeration of response statuses."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    ERROR = "error"
    PROCESSING = "processing"


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    
    status: ResponseStatus = Field(
        ResponseStatus.SUCCESS,
        description="Status of the response"
    )
    
    request_id: Optional[str] = Field(
        None,
        description="Request ID for tracking"
    )
    
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when response was generated"
    )
    
    processing_time: Optional[float] = Field(
        None,
        description="Processing time in seconds"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """
    Error response model for handling failures.
    
    This model provides structured error information with details
    for debugging and user feedback.
    """
    
    error_code: str = Field(
        ...,
        description="Machine-readable error code"
    )
    
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when error occurred"
    )
    
    request_id: Optional[str] = Field(
        None,
        description="Request ID for tracking"
    )
    
    suggestions: Optional[List[str]] = Field(
        None,
        description="Suggestions for resolving the error"
    )


class SourceInfo(BaseModel):
    """Information about a data source used in analysis."""
    
    url: str = Field(..., description="Source URL")
    title: Optional[str] = Field(None, description="Source title")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")
    excerpt: Optional[str] = Field(None, description="Key excerpt from source")


class ResearchResponse(BaseResponse):
    """
    Response model for financial research analysis.
    
    This model structures the output from the Financial Research Agent,
    providing comprehensive research findings in a professional format.
    """
    
    headline: str = Field(
        ...,
        description="Executive headline summarizing the research"
    )
    
    executive_summary: str = Field(
        ...,
        description="Brief executive summary of key findings"
    )
    
    analysis: str = Field(
        ...,
        description="Detailed analysis of the research topic"
    )
    
    future_outlook: Optional[str] = Field(
        None,
        description="Future outlook and predictions"
    )
    
    key_insights: List[str] = Field(
        default_factory=list,
        description="List of key insights from the research"
    )
    
    sources: List[SourceInfo] = Field(
        default_factory=list,
        description="Sources used in the research"
    )
    
    topic: str = Field(
        ...,
        description="Original research topic"
    )
    
    confidence_score: Optional[float] = Field(
        None,
        description="Confidence score for the analysis (0-1)",
        ge=0.0,
        le=1.0
    )
    
    risk_factors: Optional[List[str]] = Field(
        None,
        description="Identified risk factors"
    )
    
    opportunities: Optional[List[str]] = Field(
        None,
        description="Identified opportunities"
    )


class StockMetrics(BaseModel):
    """Financial metrics for a stock."""
    
    symbol: str = Field(..., description="Stock symbol")
    current_price: Optional[float] = Field(None, description="Current stock price")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    pe_ratio: Optional[float] = Field(None, description="Price-to-earnings ratio")
    eps: Optional[float] = Field(None, description="Earnings per share")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield")
    beta: Optional[float] = Field(None, description="Beta coefficient")
    volume: Optional[int] = Field(None, description="Trading volume")
    day_change: Optional[float] = Field(None, description="Day change percentage")
    year_high: Optional[float] = Field(None, description="52-week high")
    year_low: Optional[float] = Field(None, description="52-week low")


class StockAnalysis(BaseModel):
    """Analysis results for a single stock."""
    
    symbol: str = Field(..., description="Stock symbol")
    company_name: Optional[str] = Field(None, description="Company name")
    metrics: StockMetrics = Field(..., description="Financial metrics")
    analysis_summary: str = Field(..., description="Analysis summary")
    recommendation: str = Field(..., description="Investment recommendation")
    target_price: Optional[float] = Field(None, description="Target price")
    risk_level: str = Field(..., description="Risk level assessment")
    strengths: List[str] = Field(default_factory=list, description="Company strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Company weaknesses")
    catalysts: List[str] = Field(default_factory=list, description="Potential catalysts")


class StockAnalysisResponse(BaseResponse):
    """
    Response model for stock market analysis.
    
    This model structures the output from the Stock Market Analyst Agent,
    providing comprehensive stock analysis and recommendations.
    """
    
    symbols: List[str] = Field(
        ...,
        description="Stock symbols analyzed"
    )
    
    analyses: List[StockAnalysis] = Field(
        ...,
        description="Individual stock analyses"
    )
    
    market_sentiment: Optional[str] = Field(
        None,
        description="Overall market sentiment"
    )
    
    sector_analysis: Optional[str] = Field(
        None,
        description="Sector-specific analysis"
    )
    
    comparison_summary: Optional[str] = Field(
        None,
        description="Comparative analysis summary (for multi-stock requests)"
    )
    
    portfolio_recommendations: Optional[List[str]] = Field(
        None,
        description="Portfolio-level recommendations"
    )
    
    risk_assessment: Optional[str] = Field(
        None,
        description="Overall risk assessment"
    )
    
    data_freshness: Optional[datetime] = Field(
        None,
        description="Timestamp of the most recent data used"
    )


class EvaluationScore(BaseModel):
    """Score for a specific evaluation criterion."""
    
    criterion: str = Field(..., description="Evaluation criterion name")
    score: int = Field(..., description="Score (1-5)", ge=1, le=5)
    justification: str = Field(..., description="Justification for the score")
    examples: Optional[List[str]] = Field(None, description="Specific examples")
    suggestions: Optional[List[str]] = Field(None, description="Improvement suggestions")


class RAGEvaluationResponse(BaseResponse):
    """
    Response model for RAG response evaluation.
    
    This model structures the output from the RAG Evaluator Agent,
    providing detailed quality assessment and recommendations.
    """
    
    overall_score: float = Field(
        ...,
        description="Overall quality score (1-5)",
        ge=1.0,
        le=5.0
    )
    
    scores: List[EvaluationScore] = Field(
        ...,
        description="Detailed scores for each evaluation criterion"
    )
    
    summary: str = Field(
        ...,
        description="Executive summary of the evaluation"
    )
    
    strengths: List[str] = Field(
        default_factory=list,
        description="Identified strengths in the response"
    )
    
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Identified weaknesses in the response"
    )
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="Specific recommendations for improvement"
    )
    
    query: str = Field(
        ...,
        description="Original query that was evaluated"
    )
    
    response_length: int = Field(
        ...,
        description="Length of the evaluated response in characters"
    )
    
    context_utilization: Optional[float] = Field(
        None,
        description="How well the context was utilized (0-1)",
        ge=0.0,
        le=1.0
    )
    
    factual_accuracy: Optional[str] = Field(
        None,
        description="Assessment of factual accuracy"
    )


class StreamingResponse(BaseModel):
    """
    Response model for streaming operations.
    
    This model represents individual chunks in a streaming response.
    """
    
    chunk_id: int = Field(..., description="Sequential chunk identifier")
    content: str = Field(..., description="Chunk content")
    is_final: bool = Field(False, description="Whether this is the final chunk")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchResponse(BaseResponse):
    """
    Response model for batch processing operations.
    
    This model aggregates results from multiple individual requests.
    """
    
    total_requests: int = Field(..., description="Total number of requests processed")
    successful_requests: int = Field(..., description="Number of successful requests")
    failed_requests: int = Field(..., description="Number of failed requests")
    
    results: List[Union[BaseResponse, ErrorResponse]] = Field(
        ...,
        description="Individual results for each request"
    )
    
    summary: str = Field(
        ...,
        description="Summary of batch processing results"
    )
    
    errors: Optional[List[ErrorResponse]] = Field(
        None,
        description="Detailed error information for failed requests"
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""
    
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    dependencies: Optional[Dict[str, str]] = Field(None, description="Dependency health status")


class AgentInfoResponse(BaseModel):
    """Response model for agent information endpoints."""
    
    agent_name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Agent type")
    capabilities: List[str] = Field(..., description="Agent capabilities")
    supported_models: List[str] = Field(..., description="Supported LLM models")
    version: str = Field(..., description="Agent version")
    description: str = Field(..., description="Agent description")
    tools: Optional[List[str]] = Field(None, description="Available tools")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")