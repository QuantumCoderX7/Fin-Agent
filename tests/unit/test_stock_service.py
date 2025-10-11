"""
Unit tests for StockService.

This module tests the business logic layer for stock analysis operations,
including error handling, retry logic, and response formatting.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from app.services.stock_service import StockService
from app.models.requests import StockAnalysisRequest
from app.models.responses import StockAnalysisResponse, StockAnalysis, StockMetrics, ResponseStatus
from app.utils.exceptions import (
    ValidationException,
    DataSourceException,
    AgentProcessingException,
    TimeoutException
)


class TestStockService:
    """Test cases for StockService."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock stock agent."""
        agent = Mock()
        agent.process_request = AsyncMock()
        agent.stream_response = AsyncMock()
        agent.get_stock_data = AsyncMock()
        agent.get_agent_info = Mock(return_value={
            "agent_name": "StockAgent",
            "capabilities": ["stock_analysis", "comparison"]
        })
        agent.model_name = "test-model"
        return agent
    
    @pytest.fixture
    def service(self, mock_agent):
        """Create a StockService instance with mocked agent."""
        with patch('app.services.stock_service.StockAgent', return_value=mock_agent):
            return StockService(
                groq_api_key="test-key",
                timeout_seconds=30,
                max_retries=2
            )
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample stock analysis request."""
        return StockAnalysisRequest(
            symbols=["AAPL", "GOOGL"],
            analysis_type="comprehensive",
            include_comparison=True
        )
    
    @pytest.fixture
    def sample_stock_metrics(self):
        """Create sample stock metrics."""
        return StockMetrics(
            symbol="AAPL",
            current_price=150.0,
            market_cap=2500000000000,
            pe_ratio=25.5,
            eps=6.0,
            dividend_yield=0.5,
            beta=1.2,
            volume=50000000,
            day_change=2.5,
            year_high=180.0,
            year_low=120.0
        )
    
    @pytest.fixture
    def sample_stock_analysis(self, sample_stock_metrics):
        """Create a sample stock analysis."""
        return StockAnalysis(
            symbol="AAPL",
            company_name="Apple Inc.",
            metrics=sample_stock_metrics,
            analysis_summary="Strong technology company with solid fundamentals",
            recommendation="BUY",
            target_price=170.0,
            risk_level="MEDIUM",
            strengths=["Strong brand", "Innovation"],
            weaknesses=["High valuation"],
            catalysts=["New product launches"]
        )
    
    @pytest.fixture
    def sample_agent_response(self, sample_stock_analysis):
        """Create a sample agent response."""
        return {
            "status": ResponseStatus.SUCCESS,
            "symbols": ["AAPL"],
            "analyses": [sample_stock_analysis],
            "market_sentiment": "Positive",
            "comparison_summary": "AAPL shows strong performance",
            "data_freshness": datetime.utcnow()
        }
    
    @pytest.fixture
    def sample_stock_data(self):
        """Create sample stock data."""
        return {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "current_price": 150.0,
            "market_cap": 2500000000000,
            "pe_ratio": 25.5,
            "eps": 6.0,
            "dividend_yield": 0.5,
            "beta": 1.2,
            "volume": 50000000,
            "day_change": 2.5,
            "year_high": 180.0,
            "year_low": 120.0,
            "sector": "Technology",
            "industry": "Consumer Electronics"
        }
    
    @pytest.mark.asyncio
    async def test_execute_stock_analysis_success(
        self, 
        service, 
        mock_agent, 
        sample_request, 
        sample_agent_response
    ):
        """Test successful stock analysis execution."""
        # Setup
        mock_agent.process_request.return_value = sample_agent_response
        
        # Execute
        result = await service.execute_stock_analysis(sample_request)
        
        # Verify
        assert isinstance(result, StockAnalysisResponse)
        assert result.symbols == ["AAPL"]
        assert result.market_sentiment == "Positive"
        assert result.processing_time is not None
        mock_agent.process_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_stock_analysis_with_retry(
        self, 
        service, 
        mock_agent, 
        sample_request, 
        sample_agent_response
    ):
        """Test stock analysis with retry on failure."""
        # Setup - fail first, succeed second
        mock_agent.process_request.side_effect = [
            DataSourceException("Yahoo Finance", "Temporary failure"),
            sample_agent_response
        ]
        
        # Execute
        result = await service.execute_stock_analysis(sample_request)
        
        # Verify
        assert isinstance(result, StockAnalysisResponse)
        assert mock_agent.process_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_stream_stock_analysis_success(
        self, 
        service, 
        mock_agent, 
        sample_request
    ):
        """Test successful streaming stock analysis."""
        # Setup
        mock_chunks = ["Starting analysis...", "Analyzing AAPL...", "Analysis complete"]
        
        async def mock_stream(*args, **kwargs):
            for chunk in mock_chunks:
                yield chunk
        
        mock_agent.stream_response = mock_stream
        
        # Execute
        chunks = []
        async for chunk in service.stream_stock_analysis(sample_request):
            chunks.append(chunk)
        
        # Verify
        assert chunks == mock_chunks
        # Note: Can't assert on mock_stream calls since it's not a Mock object
    
    @pytest.mark.asyncio
    async def test_get_stock_info_success(
        self, 
        service, 
        mock_agent, 
        sample_stock_data
    ):
        """Test successful stock info retrieval."""
        # Setup
        mock_agent.get_stock_data.return_value = sample_stock_data
        
        # Execute
        result = await service.get_stock_info("AAPL")
        
        # Verify
        assert result["symbol"] == "AAPL"
        assert result["company_name"] == "Apple Inc."
        assert result["current_price"] == 150.0
        assert result["sector"] == "Technology"
        assert "retrieved_at" in result
        mock_agent.get_stock_data.assert_called_once_with("AAPL")
    
    @pytest.mark.asyncio
    async def test_get_stock_info_invalid_symbol(self, service):
        """Test stock info retrieval with invalid symbol."""
        # Execute & Verify
        with pytest.raises(ValidationException) as exc_info:
            await service.get_stock_info("")
        
        assert exc_info.value.details["field_name"] == "symbol"
    
    @pytest.mark.asyncio
    async def test_get_stock_info_data_source_failure(
        self, 
        service, 
        mock_agent
    ):
        """Test stock info retrieval with data source failure."""
        # Setup
        mock_agent.get_stock_data.side_effect = DataSourceException(
            "Yahoo Finance", "Symbol not found"
        )
        
        # Execute & Verify
        with pytest.raises(DataSourceException):
            await service.get_stock_info("INVALID")
    
    @pytest.mark.asyncio
    async def test_compare_stocks_success(
        self, 
        service, 
        mock_agent, 
        sample_agent_response
    ):
        """Test successful stock comparison."""
        # Setup
        mock_agent.process_request.return_value = sample_agent_response
        
        # Execute
        result = await service.compare_stocks(["AAPL", "GOOGL"])
        
        # Verify
        assert "symbols" in result
        assert "comparison_summary" in result
        assert "individual_analyses" in result
        assert result["symbols"] == ["AAPL"]
        mock_agent.process_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compare_stocks_insufficient_symbols(self, service):
        """Test stock comparison with insufficient symbols."""
        # Execute & Verify
        with pytest.raises(ValidationException) as exc_info:
            await service.compare_stocks(["AAPL"])
        
        assert "At least 2 symbols are required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_market_overview_general(self, service, mock_agent, sample_stock_data):
        """Test getting general market overview."""
        # Setup
        mock_agent.get_stock_data.return_value = sample_stock_data
        
        # Execute
        result = await service.get_market_overview()
        
        # Verify
        assert result["sector"] == "general_market"
        assert "symbols_analyzed" in result
        assert "generated_at" in result
        # Should have called get_stock_data multiple times for different symbols
        assert mock_agent.get_stock_data.call_count > 0
    
    @pytest.mark.asyncio
    async def test_get_market_overview_technology_sector(
        self, 
        service, 
        mock_agent, 
        sample_stock_data
    ):
        """Test getting technology sector market overview."""
        # Setup
        mock_agent.get_stock_data.return_value = sample_stock_data
        
        # Execute
        result = await service.get_market_overview("technology")
        
        # Verify
        assert result["sector"] == "technology"
        # Should include both market ETFs and tech stocks
        assert mock_agent.get_stock_data.call_count >= 4
    
    @pytest.mark.asyncio
    async def test_get_market_overview_with_failures(
        self, 
        service, 
        mock_agent, 
        sample_stock_data
    ):
        """Test market overview when some stock data fails."""
        # Setup - some calls succeed, some fail
        mock_agent.get_stock_data.side_effect = [
            sample_stock_data,  # SPY succeeds
            DataSourceException("Yahoo Finance", "Failed"),  # QQQ fails
            sample_stock_data,  # DIA succeeds
        ]
        
        # Execute
        result = await service.get_market_overview()
        
        # Verify - should handle failures gracefully
        assert result["sector"] == "general_market"
        assert result["symbols_analyzed"] >= 0  # Some may have failed
    
    def test_get_service_info(self, service, mock_agent):
        """Test getting service information."""
        # Execute
        info = service.get_service_info()
        
        # Verify
        assert info["service_name"] == "StockService"
        assert info["agent_type"] == "stock_analysis"
        assert info["version"] == "1.0.0"
        assert "capabilities" in info
        assert "Individual stock analysis" in info["capabilities"]
        assert "Multi-stock comparison" in info["capabilities"]
        assert "configuration" in info
        assert info["configuration"]["timeout_seconds"] == 30
        assert info["configuration"]["max_retries"] == 2
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, service, mock_agent, sample_request):
        """Test timeout exception handling."""
        # Setup
        mock_agent.process_request.side_effect = asyncio.TimeoutError()
        
        # Execute & Verify
        with pytest.raises(TimeoutException):
            await service.execute_stock_analysis(sample_request)
    
    @pytest.mark.asyncio
    async def test_unexpected_error_wrapping(self, service, mock_agent, sample_request):
        """Test that unexpected errors are properly wrapped."""
        # Setup
        mock_agent.process_request.side_effect = ValueError("Unexpected error")
        
        # Execute & Verify
        with pytest.raises(AgentProcessingException) as exc_info:
            await service.execute_stock_analysis(sample_request)
        
        assert "stock_analysis failed after" in str(exc_info.value)
        assert exc_info.value.details["agent_name"] == "StockAgent"