"""
Configuration management using Pydantic Settings for environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import validator
from typing import List
from functools import lru_cache

from app.utils.exceptions import APIKeyMissingException
from app.config.security import SecurityValidator, validate_security_settings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Keys
    groq_api_key: str = ""
    phi_api_key: str = ""
    
    # Application Settings
    app_name: str = "Financial AI Agents"
    debug: bool = False
    log_level: str = "INFO"
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    cors_origins: List[str] = ["*"]
    
    # Agent Settings
    default_model: str = "qwen/qwen3-32b"
    max_sources: int = 10
    request_timeout: int = 300
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    def validate_api_keys(self) -> None:
        """Validate that required API keys are configured with proper format."""
        missing_keys = []
        invalid_keys = []
        
        # Check GROQ API key
        if not self.groq_api_key:
            missing_keys.append("GROQ_API_KEY")
        elif not self._is_valid_groq_key(self.groq_api_key):
            invalid_keys.append("GROQ_API_KEY (must start with 'gsk_' and be at least 50 characters)")
        
        # Check PHI API key  
        if not self.phi_api_key:
            missing_keys.append("PHI_API_KEY")
        elif not self._is_valid_phi_key(self.phi_api_key):
            invalid_keys.append("PHI_API_KEY (must start with 'sk-' and be at least 40 characters)")
        
        # Raise appropriate exceptions
        if missing_keys:
            raise APIKeyMissingException(
                f"Missing required API keys: {', '.join(missing_keys)}. "
                f"Please set these environment variables or add them to your .env file. "
                f"Example format: GROQ_API_KEY=gsk_... and PHI_API_KEY=sk-..."
            )
        
        if invalid_keys:
            raise APIKeyMissingException(
                f"Invalid API key format: {', '.join(invalid_keys)}. "
                f"Please check your API key formats and ensure they are valid."
            )
    
    def _is_valid_groq_key(self, key: str) -> bool:
        """Validate GROQ API key format."""
        return SecurityValidator.is_valid_api_key_format(key, "groq")
    
    def _is_valid_phi_key(self, key: str) -> bool:
        """Validate PHI API key format.""" 
        return SecurityValidator.is_valid_api_key_format(key, "phi")
    
    def validate_security_settings(self) -> None:
        """Validate security-related settings."""
        # Skip API key validation in debug mode for development
        if self.debug:
            print("DEBUG MODE: Skipping API key validation")
            return
            
        # Use centralized security validation
        issues = validate_security_settings(self)
        
        if issues:
            raise APIKeyMissingException(
                f"Security validation failed: {'; '.join(issues)}. "
                f"Please review your configuration for security compliance."
            )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()