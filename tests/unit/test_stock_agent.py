"""
Unit tests for the Stock Market Analyst Agent.

This module contains comprehensive tests for the StockAgent class,
including mocked external API calls and validation of analysis logic.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import pandas as pd

from app.agents.stock_agent import StockAgent
from app.utils.exceptions import (
    ValidationException,
    DataSourceException,
    AgentProcessingException
)
from app.models.requests import StockAnalysisRequest
from app.models.responses import StockAnalysis, StockMetrics


class TestStockAgent:
    """Test suite for StockAgent class."""
    
    @pytest.fixture
    def mock_groq_client(self):
        """Mock Groq client for testing."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "summary": "Apple Inc. shows strong fundamentals with solid revenue growth and market position.",
            "recommendation": "BUY",
            "risk_level": "MEDIUM",
            "strengths": ["Strong brand", "Solid financials", "Innovation pipeline"],
            "weaknesses": ["High valuation", "Market saturation"],
            "catalysts": ["New product launches", "Services growth"]
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def stock_agent(self, mock_groq_client):
        """Create StockAgent instance with mocked dependencies."""
        with patch('app.agents.stock_agent.AsyncGroq', return_value=mock_groq_client):
            agent = StockAgent(groq_api_key="test_key")
            return agent
    
    @pytest.fixture
    def sample_stock_data(self):
        """Sample stock data for testing."""
        # Create mock historical data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        hist_data = pd.DataFrame({
            'Close': [150.0 + i * 0.1 for i in range(len(dates))],
            'Volume': [1000000 + i * 1000 for i in range(len(dates))]
        }, index=dates)
        
        return {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "current_price": 180.50,
            "market_cap": 2800000000000,
            "pe_ratio": 28.5,
            "eps": 6.34,
            "dividend_yield": 0.52,
            "beta": 1.2,
            "volume": 45000000,
            "day_change": 1.5,
            "year_high": 195.0,
            "year_low": 140.0,
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "historical_data": hist_data,
            "info": {"longName": "Apple Inc."}
        }
    
    def test_init(self, stock_agent):
        """Test StockAgent initialization."""
        assert stock_agent.agent_name == "Stock Market Analyst"
        assert stock_agent.agent_type == "stock_analysis"
        assert stock_agent.model_name == "qwen/qwen3-32b"
        assert len(stock_agent.default_metrics) > 0    

    def test_validate_request_valid(self, stock_agent):
        """Test request validation with valid data."""
        valid_request = {
            "symbols": ["AAPL", "GOOGL"],
            "analysis_type": "comprehensive",
            "include_comparison": True
        }
        
        assert stock_agent.validate_request(valid_request) is True
    
    def test_validate_request_invalid(self, stock_agent):
        """Test request validation with invalid data."""
        invalid_request = {
            "symbols": [],  # Empty symbols list
            "analysis_type": "invalid_type"
        }
        
        with pytest.raises(ValidationException):
            stock_agent.validate_request(invalid_request)
    
    @patch('app.agents.stock_agent.yf.Ticker')
    @pytest.mark.asyncio
    async def test_get_stock_data_success(self, mock_ticker, stock_agent, sample_stock_data):
        """Test successful stock data retrieval."""
        # Mock yfinance ticker
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = sample_stock_data["info"]
        mock_ticker_instance.history.return_value = sample_stock_data["historical_data"]
        mock_ticker.return_value = mock_ticker_instance
        
        result = await stock_agent.get_stock_data("AAPL")
        
        assert result["symbol"] == "AAPL"
        assert "current_price" in result
        assert "market_cap" in result
        mock_ticker.assert_called_once_with("AAPL")
    
    @patch('app.agents.stock_agent.yf.Ticker')
    @pytest.mark.asyncio
    async def test_get_stock_data_failure(self, mock_ticker, stock_agent):
        """Test stock data retrieval failure."""
        # Mock yfinance to raise exception
        mock_ticker.side_effect = Exception("API Error")
        
        with pytest.raises(DataSourceException):
            await stock_agent.get_stock_data("INVALID")
    
    @pytest.mark.asyncio
    async def test_analyze_single_stock(self, stock_agent, sample_stock_data):
        """Test single stock analysis."""
        with patch.object(stock_agent, '_get_ai_analysis') as mock_ai:
            mock_ai.return_value = '''
            {
                "summary": "Strong performance expected",
                "recommendation": "BUY",
                "risk_level": "LOW",
                "strengths": ["Market leader", "Strong financials"],
                "weaknesses": ["High valuation"],
                "catalysts": ["Product innovation"]
            }
            '''
            
            result = await stock_agent.analyze_single_stock("AAPL", sample_stock_data)
            
            assert isinstance(result, StockAnalysis)
            assert result.symbol == "AAPL"
            assert result.recommendation == "BUY"
            assert result.risk_level == "LOW"
            assert len(result.strengths) > 0
    
    def test_create_analysis_prompt(self, stock_agent, sample_stock_data):
        """Test analysis prompt creation."""
        prompt = stock_agent._create_analysis_prompt(sample_stock_data, "comprehensive")
        
        assert "Apple Inc." in prompt
        assert "AAPL" in prompt
        assert "Financial Metrics" in prompt
        assert "JSON" in prompt
    
    def test_parse_ai_response_valid_json(self, stock_agent):
        """Test parsing valid JSON AI response."""
        ai_response = '''
        Here is the analysis:
        {
            "summary": "Test summary",
            "recommendation": "BUY",
            "risk_level": "MEDIUM",
            "strengths": ["strength1"],
            "weaknesses": ["weakness1"],
            "catalysts": ["catalyst1"]
        }
        Additional text here.
        '''
        
        result = stock_agent._parse_ai_response(ai_response, {})
        
        assert result["summary"] == "Test summary"
        assert result["recommendation"] == "BUY"
        assert result["risk_level"] == "MEDIUM"
    
    def test_parse_ai_response_invalid_json(self, stock_agent):
        """Test parsing invalid JSON AI response."""
        ai_response = "This is not JSON format response"
        
        result = stock_agent._parse_ai_response(ai_response, {})
        
        # Should return fallback values
        assert "recommendation" in result
        assert "risk_level" in result
        assert result["recommendation"] == "HOLD"   
 
    @pytest.mark.asyncio
    async def test_compare_stocks(self, stock_agent):
        """Test stock comparison functionality."""
        # Create mock analyses
        analysis1 = StockAnalysis(
            symbol="AAPL",
            company_name="Apple Inc.",
            metrics=StockMetrics(symbol="AAPL", current_price=180.0),
            analysis_summary="Strong company",
            recommendation="BUY",
            risk_level="MEDIUM",
            strengths=["Innovation"],
            weaknesses=["Valuation"],
            catalysts=["New products"]
        )
        
        analysis2 = StockAnalysis(
            symbol="GOOGL",
            company_name="Alphabet Inc.",
            metrics=StockMetrics(symbol="GOOGL", current_price=2500.0),
            analysis_summary="Search leader",
            recommendation="HOLD",
            risk_level="LOW",
            strengths=["Market dominance"],
            weaknesses=["Regulation"],
            catalysts=["AI development"]
        )
        
        with patch.object(stock_agent, '_get_ai_analysis') as mock_ai:
            mock_ai.return_value = "Comparative analysis completed"
            
            result = await stock_agent.compare_stocks([analysis1, analysis2])
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_compare_stocks_insufficient_data(self, stock_agent):
        """Test stock comparison with insufficient data."""
        analysis1 = StockAnalysis(
            symbol="AAPL",
            company_name="Apple Inc.",
            metrics=StockMetrics(symbol="AAPL"),
            analysis_summary="Test",
            recommendation="BUY",
            risk_level="MEDIUM",
            strengths=[],
            weaknesses=[],
            catalysts=[]
        )
        
        result = await stock_agent.compare_stocks([analysis1])
        assert "requires at least 2 stocks" in result
    
    def test_get_agent_info(self, stock_agent):
        """Test agent info retrieval."""
        info = stock_agent.get_agent_info()
        
        assert info["agent_name"] == "Stock Market Analyst"
        assert info["agent_type"] == "stock_analysis"
        assert "capabilities" in info
        assert "tools" in info
        assert "data_sources" in info
        assert len(info["capabilities"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])