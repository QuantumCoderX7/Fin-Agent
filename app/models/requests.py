"""
Pydantic request models for the Financial AI Agents system.

This module defines all request models used by the API endpoints,
providing input validation and documentation for each agent type.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum


class AnalysisType(str, Enum):
    """Enumeration of available analysis types."""
    COMPREHENSIVE = "comprehensive"
    QUICK = "quick"
    DETAILED = "detailed"


class EvaluationCriteria(str, Enum):
    """Enumeration of RAG evaluation criteria."""
    FAITHFULNESS = "faithfulness"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    SOURCE_ATTRIBUTION = "source_attribution"


class BaseRequest(BaseModel):
    """Base request model with common fields."""
    
    request_id: Optional[str] = Field(
        None, 
        description="Optional request ID for tracking"
    )
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True
        validate_assignment = True


class ResearchRequest(BaseRequest):
    """
    Request model for financial research analysis.
    
    This model validates input for the Financial Research Agent,
    ensuring all required parameters are provided and valid.
    """
    
    topic: str = Field(
        ..., 
        description="Financial research topic to analyze",
        min_length=3,
        max_length=500
    )
    
    sources_limit: int = Field(
        5, 
        description="Number of sources to search and analyze",
        ge=1, 
        le=10
    )
    
    include_outlook: bool = Field(
        True, 
        description="Whether to include future outlook section"
    )
    
    focus_areas: Optional[List[str]] = Field(
        None,
        description="Specific areas to focus on in the research",
        max_items=5
    )
    
    time_horizon: Optional[str] = Field(
        None,
        description="Time horizon for analysis (e.g., '1 year', '6 months')",
        max_length=50
    )
    
    @validator('topic')
    def validate_topic(cls, v):
        """Validate research topic."""
        if not v or v.isspace():
            raise ValueError('Research topic cannot be empty or whitespace only')
        
        # Check for potentially harmful content
        forbidden_terms = ['hack', 'exploit', 'illegal', 'fraud']
        if any(term in v.lower() for term in forbidden_terms):
            raise ValueError('Research topic contains inappropriate content')
        
        return v.strip()
    
    @validator('focus_areas')
    def validate_focus_areas(cls, v):
        """Validate focus areas."""
        if v is not None:
            # Remove empty strings and strip whitespace
            v = [area.strip() for area in v if area and not area.isspace()]
            if not v:  # If all areas were empty
                return None
        return v


class StockAnalysisRequest(BaseRequest):
    """
    Request model for stock market analysis.
    
    This model validates input for the Stock Market Analyst Agent,
    supporting both single and multi-stock analysis.
    """
    
    symbols: List[str] = Field(
        ..., 
        description="Stock symbols to analyze (e.g., ['AAPL', 'GOOGL'])",
        min_items=1,
        max_items=10
    )
    
    analysis_type: AnalysisType = Field(
        AnalysisType.COMPREHENSIVE,
        description="Type of analysis to perform"
    )
    
    include_comparison: bool = Field(
        False, 
        description="Whether to include comparative analysis between stocks"
    )
    
    metrics: Optional[List[str]] = Field(
        None,
        description="Specific financial metrics to focus on",
        max_items=10
    )
    
    time_period: Optional[str] = Field(
        "1y",
        description="Time period for historical data (e.g., '1y', '6m', '3m')",
        max_length=10
    )
    
    include_recommendations: bool = Field(
        True,
        description="Whether to include investment recommendations"
    )
    
    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate stock symbols."""
        if not v:
            raise ValueError('At least one stock symbol is required')
        
        # Clean and validate symbols
        cleaned_symbols = []
        for symbol in v:
            if not symbol or symbol.isspace():
                continue
            
            # Convert to uppercase and remove whitespace
            symbol = symbol.strip().upper()
            
            # Basic symbol validation (alphanumeric, dots, hyphens)
            if not symbol.replace('.', '').replace('-', '').isalnum():
                raise ValueError(f'Invalid stock symbol format: {symbol}')
            
            if len(symbol) > 10:
                raise ValueError(f'Stock symbol too long: {symbol}')
            
            cleaned_symbols.append(symbol)
        
        if not cleaned_symbols:
            raise ValueError('No valid stock symbols provided')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symbols = []
        for symbol in cleaned_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        return unique_symbols
    
    @validator('metrics')
    def validate_metrics(cls, v):
        """Validate financial metrics."""
        if v is not None:
            # Remove empty strings and strip whitespace
            v = [metric.strip() for metric in v if metric and not metric.isspace()]
            if not v:  # If all metrics were empty
                return None
        return v


class RAGEvaluationRequest(BaseRequest):
    """
    Request model for RAG response evaluation.
    
    This model validates input for the RAG Evaluator Agent,
    ensuring all required components for evaluation are provided.
    """
    
    query: str = Field(
        ..., 
        description="Original query that generated the response",
        min_length=3,
        max_length=1000
    )
    
    response: str = Field(
        ..., 
        description="RAG-generated response to evaluate",
        min_length=10,
        max_length=10000
    )
    
    context: List[str] = Field(
        ..., 
        description="Context documents used for response generation",
        min_items=1,
        max_items=20
    )
    
    evaluation_criteria: Optional[List[EvaluationCriteria]] = Field(
        None,
        description="Specific criteria to evaluate (if not provided, all criteria will be used)"
    )
    
    include_recommendations: bool = Field(
        True,
        description="Whether to include improvement recommendations"
    )
    
    detailed_feedback: bool = Field(
        True,
        description="Whether to provide detailed feedback for each criterion"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Validate the original query."""
        if not v or v.isspace():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()
    
    @validator('response')
    def validate_response(cls, v):
        """Validate the RAG response."""
        if not v or v.isspace():
            raise ValueError('Response cannot be empty or whitespace only')
        return v.strip()
    
    @validator('context')
    def validate_context(cls, v):
        """Validate context documents."""
        if not v:
            raise ValueError('At least one context document is required')
        
        # Clean and validate context documents
        cleaned_context = []
        for doc in v:
            if not doc or doc.isspace():
                continue
            
            doc = doc.strip()
            if len(doc) < 10:
                continue  # Skip very short context documents
            
            cleaned_context.append(doc)
        
        if not cleaned_context:
            raise ValueError('No valid context documents provided')
        
        return cleaned_context


class StreamingRequest(BaseRequest):
    """
    Base request model for streaming responses.
    
    This model extends the base request with streaming-specific parameters.
    """
    
    stream_chunk_size: int = Field(
        1024,
        description="Size of streaming chunks in characters",
        ge=100,
        le=5000
    )
    
    include_progress: bool = Field(
        True,
        description="Whether to include progress indicators in the stream"
    )


class BatchRequest(BaseRequest):
    """
    Request model for batch processing operations.
    
    This model supports processing multiple requests in a single API call.
    """
    
    requests: List[Dict[str, Any]] = Field(
        ...,
        description="List of individual requests to process",
        min_items=1,
        max_items=50
    )
    
    parallel_processing: bool = Field(
        True,
        description="Whether to process requests in parallel"
    )
    
    fail_fast: bool = Field(
        False,
        description="Whether to stop processing on first failure"
    )
    
    @validator('requests')
    def validate_requests(cls, v):
        """Validate batch requests."""
        if not v:
            raise ValueError('At least one request is required for batch processing')
        
        # Basic validation that each request is a non-empty dict
        for i, req in enumerate(v):
            if not isinstance(req, dict) or not req:
                raise ValueError(f'Request at index {i} must be a non-empty dictionary')
        
        return v