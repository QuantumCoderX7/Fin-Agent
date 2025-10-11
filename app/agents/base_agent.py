"""
Abstract base agent interface for Financial AI Agents system.

This module defines the standard interface that all specialized financial agents
must implement, ensuring consistency across different agent types.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator, Optional
from pydantic import BaseModel


class BaseAgent(ABC):
    """
    Abstract base class for all financial AI agents.
    
    This class defines the standard interface that all specialized agents
    (Research, Stock, RAG Evaluator) must implement to ensure consistency
    and interoperability within the system.
    """
    
    def __init__(self, model_name: str = "qwen/qwen3-32b", **kwargs):
        """
        Initialize the base agent.
        
        Args:
            model_name: The LLM model to use for this agent
            **kwargs: Additional configuration parameters
        """
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request and return the analysis result.
        
        Args:
            request: The request data containing analysis parameters
            
        Returns:
            Dict containing the analysis results
            
        Raises:
            ValidationException: If request validation fails
            AgentProcessingException: If processing fails
        """
        pass
    
    @abstractmethod
    async def stream_response(self, request: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Process a request and stream the response in real-time.
        
        Args:
            request: The request data containing analysis parameters
            
        Yields:
            String chunks of the streaming response
            
        Raises:
            ValidationException: If request validation fails
            AgentProcessingException: If processing fails
        """
        pass
    
    @abstractmethod
    def validate_request(self, request: Dict[str, Any]) -> bool:
        """
        Validate the incoming request data.
        
        Args:
            request: The request data to validate
            
        Returns:
            True if request is valid
            
        Raises:
            ValidationException: If validation fails
        """
        pass
    
    @abstractmethod
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent's capabilities.
        
        Returns:
            Dict containing agent metadata and capabilities
        """
        pass
    
    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.model_name
    
    def update_config(self, **kwargs) -> None:
        """Update agent configuration."""
        self.config.update(kwargs)