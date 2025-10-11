"""
Unit tests for ResearchAgent.

This module contains comprehensive tests for the ResearchAgent class,
including mocked external API calls and validation of research logic.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import json

from app.agents.research_agent import ResearchAgent
from app.utils.exceptions import (
    ValidationException,
    DataSourceException,
    AgentProcessingException
)
from app.models.requests import ResearchRequest
from app.models.responses import ResearchResponse, SourceInfo


class TestResearchAgent:
    """Test suite for ResearchAgent class."""
    
    @pytest.fixture
    def mock_groq_client(self):
        """Mock Groq client for testing."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        # Federal Reserve Policy Analysis
        
        ## Executive Summary
        The Federal Reserve is maintaining a cautious approach to monetary policy...
        
        ## Analysis
        Current economic indicators suggest...
        
        ## Future Outlook
        Looking ahead, the Fed is likely to...
        '''
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def research_agent(self, mock_groq_client):
        """Create ResearchAgent instance with mocked dependencies."""
        with patch('app.agents.research_agent.AsyncGroq', return_value=mock_groq_client):
            agent = ResearchAgent(groq_api_key="test_key")
            return agent
    
    @pytest.fixture
    def sample_search_results(self):
        """Sample search results for testing."""
        return [
            {
                "title": "Federal Reserve Announces Policy Decision",
                "href": "https://example.com/fed-policy-1",
                "body": "The Federal Reserve announced today that it will maintain current interest rates..."
            },
            {
                "title": "Economic Analysis: Fed Policy Impact",
                "href": "https://example.com/fed-analysis-1",
                "body": "Recent Federal Reserve decisions have significant implications for the economy..."
            },
            {
                "title": "Market Response to Fed Announcement",
                "href": "https://example.com/market-response-1",
                "body": "Financial markets reacted positively to the Federal Reserve's latest policy statement..."
            }
        ]
    
    @pytest.fixture
    def sample_article_content(self):
        """Sample article content for testing."""
        return {
            "title": "Federal Reserve Policy Analysis",
            "text": "The Federal Reserve's recent policy decisions reflect a careful balance between supporting economic growth and controlling inflation. Key factors influencing the decision include employment data, inflation metrics, and global economic conditions.",
            "authors": ["John Smith", "Jane Doe"],
            "publish_date": "2024-01-15",
            "url": "https://example.com/fed-policy-analysis"
        }
    
    def test_init(self, research_agent):
        """Test ResearchAgent initialization."""
        assert research_agent.agent_name == "Financial Research Analyst"
        assert research_agent.agent_type == "financial_research"
        assert research_agent.model_name == "qwen/qwen3-32b"
        assert research_agent.max_sources == 10
        assert research_agent.search_timeout == 30
    
    def test_validate_request_valid(self, research_agent):
        """Test request validation with valid data."""
        valid_request = {
            "topic": "Federal Reserve interest rate policy",
            "sources_limit": 5,
            "include_outlook": True,
            "focus_areas": ["monetary policy", "inflation"],
            "time_horizon": "6 months"
        }
        
        assert research_agent.validate_request(valid_request) is True
    
    def test_validate_request_invalid_empty_topic(self, research_agent):
        """Test request validation with empty topic."""
        invalid_request = {
            "topic": "",
            "sources_limit": 5
        }
        
        with pytest.raises(ValidationException):
            research_agent.validate_request(invalid_request)
    
    def test_validate_request_invalid_sources_limit(self, research_agent):
        """Test request validation with invalid sources limit."""
        invalid_request = {
            "topic": "Test topic",
            "sources_limit": 0
        }
        
        with pytest.raises(ValidationException):
            research_agent.validate_request(invalid_request)
    
    @patch('app.agents.research_agent.DDGS')
    @pytest.mark.asyncio
    async def test_search_sources_success(self, mock_ddgs, research_agent, sample_search_results):
        """Test successful source searching."""
        # Mock DuckDuckGo search
        mock_ddgs_instance = Mock()
        mock_ddgs_instance.text.return_value = sample_search_results
        mock_ddgs.return_value = mock_ddgs_instance
        
        results = await research_agent._search_sources("Federal Reserve policy", 3)
        
        assert len(results) == 3
        assert all("title" in result for result in results)
        assert all("href" in result for result in results)
        assert all("body" in result for result in results)
    
    @patch('app.agents.research_agent.DDGS')
    @pytest.mark.asyncio
    async def test_search_sources_failure(self, mock_ddgs, research_agent):
        """Test source searching failure."""
        # Mock DuckDuckGo to raise exception
        mock_ddgs.side_effect = Exception("Search API Error")
        
        with pytest.raises(DataSourceException):
            await research_agent._search_sources("test topic", 5)
    
    @patch('app.agents.research_agent.newspaper')
    @pytest.mark.asyncio
    async def test_extract_article_content_success(self, mock_newspaper, research_agent, sample_article_content):
        """Test successful article content extraction."""
        # Mock newspaper article
        mock_article = Mock()
        mock_article.title = sample_article_content["title"]
        mock_article.text = sample_article_content["text"]
        mock_article.authors = sample_article_content["authors"]
        mock_article.publish_date = datetime.strptime(sample_article_content["publish_date"], "%Y-%m-%d")
        mock_article.url = sample_article_content["url"]
        
        mock_newspaper.Article.return_value = mock_article
        
        result = await research_agent._extract_article_content("https://example.com/test")
        
        assert result["title"] == sample_article_content["title"]
        assert result["text"] == sample_article_content["text"]
        assert result["authors"] == sample_article_content["authors"]
        assert result["url"] == sample_article_content["url"]
    
    @patch('app.agents.research_agent.newspaper')
    @pytest.mark.asyncio
    async def test_extract_article_content_failure(self, mock_newspaper, research_agent):
        """Test article content extraction failure."""
        # Mock newspaper to raise exception
        mock_newspaper.Article.side_effect = Exception("Article extraction failed")
        
        result = await research_agent._extract_article_content("https://example.com/test")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_research_report(self, research_agent):
        """Test research report generation."""
        topic = "Federal Reserve policy"
        sources_data = [
            {
                "title": "Fed Policy Update",
                "text": "The Federal Reserve announced new policy measures...",
                "url": "https://example.com/fed-1",
                "relevance_score": 0.95
            },
            {
                "title": "Economic Impact Analysis",
                "text": "The economic implications of recent Fed decisions...",
                "url": "https://example.com/analysis-1",
                "relevance_score": 0.88
            }
        ]
        
        with patch.object(research_agent, '_get_ai_analysis') as mock_ai:
            mock_ai.return_value = '''
            # Federal Reserve Policy Analysis
            
            ## Executive Summary
            The Federal Reserve maintains cautious monetary policy...
            
            ## Analysis
            Current economic conditions suggest...
            
            ## Future Outlook
            Looking ahead, policy adjustments are likely...
            '''
            
            result = await research_agent._generate_research_report(topic, sources_data, True)
            
            assert isinstance(result, dict)
            assert "headline" in result
            assert "executive_summary" in result
            assert "analysis" in result
            assert "future_outlook" in result
    
    def test_parse_research_report_valid(self, research_agent):
        """Test parsing valid research report."""
        ai_response = '''
        # Federal Reserve Policy Analysis
        
        ## Executive Summary
        The Federal Reserve is maintaining current interest rates while monitoring inflation indicators.
        
        ## Analysis
        Recent economic data shows mixed signals with employment remaining strong but inflation concerns persisting.
        
        ## Future Outlook
        The Fed is likely to adopt a wait-and-see approach in the coming months.
        '''
        
        result = research_agent._parse_research_report(ai_response)
        
        assert result["headline"] == "Federal Reserve Policy Analysis"
        assert "Federal Reserve is maintaining" in result["executive_summary"]
        assert "Recent economic data" in result["analysis"]
        assert "wait-and-see approach" in result["future_outlook"]
    
    def test_parse_research_report_missing_sections(self, research_agent):
        """Test parsing research report with missing sections."""
        ai_response = '''
        # Federal Reserve Policy Analysis
        
        ## Executive Summary
        The Federal Reserve is maintaining current rates.
        '''
        
        result = research_agent._parse_research_report(ai_response)
        
        assert result["headline"] == "Federal Reserve Policy Analysis"
        assert "Federal Reserve is maintaining" in result["executive_summary"]
        assert "Analysis not available" in result["analysis"]
        assert "Outlook not available" in result["future_outlook"]
    
    def test_calculate_relevance_score(self, research_agent):
        """Test relevance score calculation."""
        topic = "Federal Reserve interest rates"
        content = "The Federal Reserve announced changes to interest rate policy affecting monetary conditions"
        
        score = research_agent._calculate_relevance_score(topic, content)
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)
        assert score > 0.5  # Should be high relevance
    
    def test_calculate_relevance_score_low_relevance(self, research_agent):
        """Test relevance score with low relevance content."""
        topic = "Federal Reserve interest rates"
        content = "Weather patterns and climate change impact agricultural productivity"
        
        score = research_agent._calculate_relevance_score(topic, content)
        
        assert 0.0 <= score <= 1.0
        assert score < 0.3  # Should be low relevance
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, research_agent, sample_search_results, sample_article_content):
        """Test successful request processing."""
        request_data = {
            "topic": "Federal Reserve policy impact",
            "sources_limit": 3,
            "include_outlook": True,
            "focus_areas": ["monetary policy"],
            "time_horizon": "6 months"
        }
        
        with patch.object(research_agent, '_search_sources') as mock_search, \
             patch.object(research_agent, '_extract_article_content') as mock_extract, \
             patch.object(research_agent, '_generate_research_report') as mock_generate:
            
            mock_search.return_value = sample_search_results
            mock_extract.return_value = sample_article_content
            mock_generate.return_value = {
                "headline": "Federal Reserve Policy Analysis",
                "executive_summary": "The Fed maintains cautious approach...",
                "analysis": "Current economic indicators suggest...",
                "future_outlook": "Policy adjustments likely in coming months...",
                "key_insights": ["Interest rates stable", "Inflation monitored"],
                "confidence_score": 0.85
            }
            
            result = await research_agent.process_request(request_data)
            
            assert isinstance(result, dict)
            assert result["headline"] == "Federal Reserve Policy Analysis"
            assert result["topic"] == "Federal Reserve policy impact"
            assert result["confidence_score"] == 0.85
            assert len(result["key_insights"]) == 2
            assert len(result["sources"]) > 0
    
    @pytest.mark.asyncio
    async def test_process_request_validation_error(self, research_agent):
        """Test request processing with validation error."""
        invalid_request = {"topic": ""}  # Empty topic
        
        with pytest.raises(ValidationException):
            await research_agent.process_request(invalid_request)
    
    @pytest.mark.asyncio
    async def test_process_request_search_failure(self, research_agent):
        """Test request processing with search failure."""
        request_data = {
            "topic": "Test topic",
            "sources_limit": 5
        }
        
        with patch.object(research_agent, '_search_sources') as mock_search:
            mock_search.side_effect = DataSourceException("research", "Search failed")
            
            with pytest.raises(AgentProcessingException):
                await research_agent.process_request(request_data)
    
    @pytest.mark.asyncio
    async def test_stream_response_success(self, research_agent):
        """Test successful streaming response."""
        request_data = {
            "topic": "Federal Reserve policy",
            "sources_limit": 3,
            "include_outlook": True
        }
        
        with patch.object(research_agent, 'process_request') as mock_process:
            mock_process.return_value = {
                "headline": "Test Analysis",
                "executive_summary": "Test summary",
                "analysis": "Test analysis",
                "future_outlook": "Test outlook",
                "sources": [],
                "processing_time": 10.5
            }
            
            chunks = []
            async for chunk in research_agent.stream_response(request_data):
                chunks.append(chunk)
            
            assert len(chunks) > 0
            
            # Check that streaming includes expected content
            full_response = "".join(chunks)
            assert "Financial Research Analysis Starting" in full_response
            assert "Test Analysis" in full_response
            assert "Analysis Complete" in full_response
    
    @pytest.mark.asyncio
    async def test_stream_response_error(self, research_agent):
        """Test streaming response with error."""
        invalid_request = {"topic": ""}  # Invalid request
        
        chunks = []
        async for chunk in research_agent.stream_response(invalid_request):
            chunks.append(chunk)
        
        full_response = "".join(chunks)
        assert "Research Failed" in full_response
    
    def test_get_agent_info(self, research_agent):
        """Test agent info retrieval."""
        info = research_agent.get_agent_info()
        
        assert info["agent_name"] == "Financial Research Analyst"
        assert info["agent_type"] == "financial_research"
        assert "capabilities" in info
        assert "tools" in info
        assert "data_sources" in info
        assert len(info["capabilities"]) > 0
        
        # Check specific capabilities
        capabilities = info["capabilities"]
        assert "Market research and analysis" in capabilities
        assert "Multi-source data aggregation" in capabilities
        assert "Real-time financial news monitoring" in capabilities
    
    def test_create_research_prompt(self, research_agent):
        """Test research prompt creation."""
        topic = "Federal Reserve policy"
        sources_data = [
            {"title": "Fed Update", "text": "Policy announcement", "url": "test.com"}
        ]
        focus_areas = ["monetary policy", "inflation"]
        
        prompt = research_agent._create_research_prompt(topic, sources_data, True, focus_areas, "6 months")
        
        assert topic in prompt
        assert "monetary policy" in prompt
        assert "inflation" in prompt
        assert "6 months" in prompt
        assert "Future Outlook" in prompt
    
    def test_extract_key_insights(self, research_agent):
        """Test key insights extraction."""
        analysis_text = """
        The Federal Reserve's decision reflects several key factors:
        - Interest rates remain stable at current levels
        - Inflation shows signs of moderation
        - Employment data indicates continued strength
        - Global economic uncertainty persists
        """
        
        insights = research_agent._extract_key_insights(analysis_text)
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        assert any("interest rates" in insight.lower() for insight in insights)
        assert any("inflation" in insight.lower() for insight in insights)
    
    def test_calculate_confidence_score(self, research_agent):
        """Test confidence score calculation."""
        sources_data = [
            {"relevance_score": 0.9, "text": "High quality content with detailed analysis"},
            {"relevance_score": 0.8, "text": "Good content with relevant information"},
            {"relevance_score": 0.7, "text": "Adequate content"}
        ]
        
        confidence = research_agent._calculate_confidence_score(sources_data, "comprehensive")
        
        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)
        assert confidence > 0.5  # Should be reasonably high with good sources


class TestResearchAgentEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def research_agent(self):
        """Create ResearchAgent instance for edge case testing."""
        with patch('app.agents.research_agent.AsyncGroq'):
            return ResearchAgent(groq_api_key="test_key")
    
    def test_empty_search_results(self, research_agent):
        """Test handling of empty search results."""
        with patch.object(research_agent, '_search_sources') as mock_search:
            mock_search.return_value = []
            
            # Should handle gracefully
            sources_data = []
            confidence = research_agent._calculate_confidence_score(sources_data, "basic")
            assert confidence == 0.0
    
    def test_malformed_article_content(self, research_agent):
        """Test handling of malformed article content."""
        malformed_content = {
            "title": None,
            "text": "",
            "url": "invalid-url"
        }
        
        score = research_agent._calculate_relevance_score("test topic", malformed_content.get("text", ""))
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, research_agent):
        """Test timeout handling in async operations."""
        with patch.object(research_agent, '_search_sources') as mock_search:
            mock_search.side_effect = asyncio.TimeoutError("Search timeout")
            
            with pytest.raises(DataSourceException):
                await research_agent._search_sources("test topic", 5)
    
    def test_very_long_topic(self, research_agent):
        """Test handling of very long research topics."""
        long_topic = "A" * 1000  # Very long topic
        
        request_data = {
            "topic": long_topic,
            "sources_limit": 5
        }
        
        with pytest.raises(ValidationException):
            research_agent.validate_request(request_data)
    
    def test_special_characters_in_topic(self, research_agent):
        """Test handling of special characters in topic."""
        special_topic = "Federal Reserve & ECB: Policy Coordination (2024) - Impact Analysis!"
        
        request_data = {
            "topic": special_topic,
            "sources_limit": 5
        }
        
        # Should handle special characters gracefully
        assert research_agent.validate_request(request_data) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])