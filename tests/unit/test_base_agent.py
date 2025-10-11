"""
Unit tests for BaseAgent abstract class.

This module tests the base agent interface and common functionality
that all specialized agents inherit from.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from abc import ABC

from app.agents.base_agent import BaseAgent
from app.utils.exceptions import ValidationException, AgentProcessingException


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    def __init__(self, groq_api_key: str = "test-key"):
        super().__init__(groq_api_key)
        self.model_name = "test-model"
    
    async def process_request(self, request: dict) -> dict:
        """Test implementation of process_request."""
        if request.get("should_fail"):
            raise AgentProcessingException("ConcreteAgent", "Test failure")
        return {"status": "success", "data": request}
    
    async def stream_response(self, request: dict):
        """Test implementation of stream_response."""
        chunks = ["chunk1", "chunk2", "chunk3"]
        for chunk in chunks:
            yield chunk
    
    def validate_request(self, request: dict) -> bool:
        """Test implementation of validate_request."""
        if not isinstance(request, dict):
            return False
        if "invalid" in request:
            return False
        return True
    
    def get_agent_info(self) -> dict:
        """Test implementation of get_agent_info."""
        return {
            "agent_name": "ConcreteAgent",
            "capabilities": ["test"],
            "model": self.model_name
        }


class TestBaseAgent:
    """Test cases for BaseAgent abstract class."""
    
    @pytest.fixture
    def agent(self):
        """Create a concrete agent instance for testing."""
        return ConcreteAgent()
    
    def test_base_agent_is_abstract(self):
        """Test that BaseAgent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAgent("test-key")
    
    def test_concrete_agent_initialization(self, agent):
        """Test that concrete agent initializes properly."""
        assert agent.groq_api_key == "test-key"
        assert agent.model_name == "test-model"
        assert hasattr(agent, 'client')
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, agent):
        """Test successful request processing."""
        request = {"topic": "test", "data": "sample"}
        result = await agent.process_request(request)
        
        assert result["status"] == "success"
        assert result["data"] == request
    
    @pytest.mark.asyncio
    async def test_process_request_failure(self, agent):
        """Test request processing failure."""
        request = {"should_fail": True}
        
        with pytest.raises(AgentProcessingException) as exc_info:
            await agent.process_request(request)
        
        assert "ConcreteAgent" in str(exc_info.value)
        assert "Test failure" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stream_response(self, agent):
        """Test streaming response functionality."""
        request = {"topic": "test"}
        chunks = []
        
        async for chunk in agent.stream_response(request):
            chunks.append(chunk)
        
        assert chunks == ["chunk1", "chunk2", "chunk3"]
    
    def test_validate_request_valid(self, agent):
        """Test request validation with valid input."""
        valid_request = {"topic": "test", "data": "sample"}
        assert agent.validate_request(valid_request) is True
    
    def test_validate_request_invalid_type(self, agent):
        """Test request validation with invalid type."""
        invalid_request = "not a dict"
        assert agent.validate_request(invalid_request) is False
    
    def test_validate_request_invalid_content(self, agent):
        """Test request validation with invalid content."""
        invalid_request = {"invalid": True}
        assert agent.validate_request(invalid_request) is False
    
    def test_get_agent_info(self, agent):
        """Test getting agent information."""
        info = agent.get_agent_info()
        
        assert info["agent_name"] == "ConcreteAgent"
        assert info["capabilities"] == ["test"]
        assert info["model"] == "test-model"
    
    def test_required_methods_exist(self, agent):
        """Test that all required abstract methods are implemented."""
        # These should not raise NotImplementedError
        assert hasattr(agent, 'process_request')
        assert hasattr(agent, 'stream_response')
        assert hasattr(agent, 'validate_request')
        assert hasattr(agent, 'get_agent_info')
        
        # Test that they are callable
        assert callable(agent.process_request)
        assert callable(agent.stream_response)
        assert callable(agent.validate_request)
        assert callable(agent.get_agent_info)
    
    def test_groq_client_initialization(self, agent):
        """Test that Groq client is properly initialized."""
        assert hasattr(agent, 'client')
        # The client should be initialized with the API key
        # We can't test the actual client without mocking, but we can verify it exists
    
    @patch('app.agents.base_agent.Groq')
    def test_groq_client_creation(self, mock_groq):
        """Test Groq client creation with mocked Groq."""
        mock_client = Mock()
        mock_groq.return_value = mock_client
        
        agent = ConcreteAgent("test-api-key")
        
        mock_groq.assert_called_once_with(api_key="test-api-key")
        assert agent.client == mock_client
    
    def test_inheritance_structure(self):
        """Test that BaseAgent properly inherits from ABC."""
        assert issubclass(BaseAgent, ABC)
        assert hasattr(BaseAgent, '__abstractmethods__')
        
        # Check that the abstract methods are properly defined
        abstract_methods = BaseAgent.__abstractmethods__
        expected_methods = {'process_request', 'stream_response', 'validate_request', 'get_agent_info'}
        assert abstract_methods == expected_methods