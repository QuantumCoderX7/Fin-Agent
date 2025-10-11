"""
Unit tests for ResearchService.

This module tests the business logic layer for research operations,
including error handling, retry logic, and response formatting.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from app.services.research_service import ResearchService
from app.models.requests import ResearchRequest
from app.models.responses import ResearchResponse, ResponseStatus
from app.utils.exceptions import (
    ValidationException,
    DataSourceException,
    AgentProcessingException,
    TimeoutException,
    RateLimitException
)


class TestResearchService:
    """Test cases for ResearchService."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock research agent."""
        agent = Mock()
        agent.process_request = AsyncMock()
        agent.stream_response = AsyncMock()
        agent.get_agent_info = Mock(return_value={
            "agent_name": "ResearchAgent",
            "capabilities": ["research", "analysis"]
        })
        agent.model_name = "test-model"
        return agent
    
    @pytest.fixture
    def service(self, mock_agent):
        """Create a ResearchService instance with mocked agent."""
        with patch('app.services.research_service.ResearchAgent', return_value=mock_agent):
            return ResearchService(
                groq_api_key="test-key",
                timeout_seconds=30,
                max_retries=2
            )
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample research request."""
        return ResearchRequest(
            topic="Federal Reserve interest rate policy",
            sources_limit=5,
            include_outlook=True
        )
    
    @pytest.fixture
    def sample_agent_response(self):
        """Create a sample agent response."""
        return {
            "status": ResponseStatus.SUCCESS,
            "headline": "Fed Policy Analysis",
            "executive_summary": "Interest rates remain elevated",
            "analysis": "Detailed analysis of Fed policy",
            "future_outlook": "Rates may decrease in 2024",
            "key_insights": ["Inflation concerns", "Economic growth"],
            "sources": [],
            "topic": "Federal Reserve interest rate policy",
            "confidence_score": 0.85
        }
    
    @pytest.mark.asyncio
    async def test_execute_research_analysis_success(
        self, 
        service, 
        mock_agent, 
        sample_request, 
        sample_agent_response
    ):
        """Test successful research analysis execution."""
        # Setup
        mock_agent.process_request.return_value = sample_agent_response
        
        # Execute
        result = await service.execute_research_analysis(sample_request)
        
        # Verify
        assert isinstance(result, ResearchResponse)
        assert result.headline == "Fed Policy Analysis"
        assert result.topic == "Federal Reserve interest rate policy"
        assert result.processing_time is not None
        mock_agent.process_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_research_analysis_with_retry(
        self, 
        service, 
        mock_agent, 
        sample_request, 
        sample_agent_response
    ):
        """Test research analysis with retry on failure."""
        # Setup - fail first, succeed second
        mock_agent.process_request.side_effect = [
            DataSourceException("DuckDuckGo", "Temporary failure"),
            sample_agent_response
        ]
        
        # Execute
        result = await service.execute_research_analysis(sample_request)
        
        # Verify
        assert isinstance(result, ResearchResponse)
        assert mock_agent.process_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_research_analysis_timeout(
        self, 
        service, 
        mock_agent, 
        sample_request
    ):
        """Test research analysis timeout handling."""
        # Setup
        mock_agent.process_request.side_effect = asyncio.TimeoutError()
        
        # Execute & Verify
        with pytest.raises(TimeoutException):
            await service.execute_research_analysis(sample_request)
    
    @pytest.mark.asyncio
    async def test_execute_research_analysis_max_retries_exceeded(
        self, 
        service, 
        mock_agent, 
        sample_request
    ):
        """Test research analysis when max retries are exceeded."""
        # Setup - always fail
        mock_agent.process_request.side_effect = DataSourceException(
            "DuckDuckGo", "Persistent failure"
        )
        
        # Execute & Verify
        with pytest.raises(DataSourceException):
            await service.execute_research_analysis(sample_request)
        
        # Should try 3 times (initial + 2 retries)
        assert mock_agent.process_request.call_count == 3
    
    @pytest.mark.asyncio
    async def test_stream_research_analysis_success(
        self, 
        service, 
        mock_agent, 
        sample_request
    ):
        """Test successful streaming research analysis."""
        # Setup
        mock_chunks = ["Chunk 1", "Chunk 2", "Final chunk"]
        
        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk
        
        mock_agent.stream_response.return_value = mock_stream()
        
        # Execute
        chunks = []
        async for chunk in service.stream_research_analysis(sample_request):
            chunks.append(chunk)
        
        # Verify
        assert chunks == mock_chunks
        mock_agent.stream_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_research_analysis_error(
        self, 
        service, 
        mock_agent, 
        sample_request
    ):
        """Test streaming research analysis error handling."""
        # Setup
        async def mock_stream_error():
            yield "Starting..."
            raise AgentProcessingException("ResearchAgent", "Stream failed")
        
        mock_agent.stream_response.return_value = mock_stream_error()
        
        # Execute
        chunks = []
        with pytest.raises(AgentProcessingException):
            async for chunk in service.stream_research_analysis(sample_request):
                chunks.append(chunk)
        
        # Verify we got the first chunk and error message
        assert len(chunks) >= 1
        assert "Starting..." in chunks
    
    @pytest.mark.asyncio
    async def test_get_research_suggestions_finance(self, service):
        """Test getting research suggestions for finance domain."""
        # Execute
        result = await service.get_research_suggestions("finance")
        
        # Verify
        assert result["domain"] == "finance"
        assert "suggested_topics" in result
        assert len(result["suggested_topics"]) > 0
        assert "Federal Reserve interest rate policy impact" in result["suggested_topics"]
        assert "generated_at" in result
    
    @pytest.mark.asyncio
    async def test_get_research_suggestions_markets(self, service):
        """Test getting research suggestions for markets domain."""
        # Execute
        result = await service.get_research_suggestions("markets")
        
        # Verify
        assert result["domain"] == "markets"
        assert "Emerging markets investment opportunities" in result["suggested_topics"]
    
    @pytest.mark.asyncio
    async def test_get_research_suggestions_unknown_domain(self, service):
        """Test getting research suggestions for unknown domain."""
        # Execute
        result = await service.get_research_suggestions("unknown")
        
        # Verify - should default to finance topics
        assert result["domain"] == "unknown"
        assert "Federal Reserve interest rate policy impact" in result["suggested_topics"]
    
    def test_get_service_info(self, service, mock_agent):
        """Test getting service information."""
        # Execute
        info = service.get_service_info()
        
        # Verify
        assert info["service_name"] == "ResearchService"
        assert info["agent_type"] == "financial_research"
        assert info["version"] == "1.0.0"
        assert "capabilities" in info
        assert "configuration" in info
        assert "agent_info" in info
        assert info["configuration"]["timeout_seconds"] == 30
        assert info["configuration"]["max_retries"] == 2
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(
        self, 
        service, 
        mock_agent, 
        sample_request, 
        sample_agent_response
    ):
        """Test rate limit exception handling with exponential backoff."""
        # Setup - rate limited first, then success
        mock_agent.process_request.side_effect = [
            RateLimitException("Groq", "Rate limited", retry_after=1),
            sample_agent_response
        ]
        
        # Execute
        start_time = datetime.utcnow()
        result = await service.execute_research_analysis(sample_request)
        end_time = datetime.utcnow()
        
        # Verify
        assert isinstance(result, ResearchResponse)
        assert mock_agent.process_request.call_count == 2
        # Should have waited at least 1 second for retry
        assert (end_time - start_time).total_seconds() >= 1.0
    
    @pytest.mark.asyncio
    async def test_validation_error_propagation(self, service, mock_agent, sample_request):
        """Test that validation errors are properly propagated."""
        # Setup
        validation_error = ValidationException(
            field_name="topic",
            message="Invalid topic format"
        )
        mock_agent.process_request.side_effect = validation_error
        
        # Execute & Verify
        with pytest.raises(ValidationException) as exc_info:
            await service.execute_research_analysis(sample_request)
        
        assert exc_info.value.details["field_name"] == "topic"
        # Should not retry validation errors
        assert mock_agent.process_request.call_count == 1