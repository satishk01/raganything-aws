"""
AWS Bedrock configuration management
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from lightrag.utils import get_env_value
from .exceptions import BedrockConfigurationError


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    backoff_factor: float = 2.0
    max_backoff: float = 60.0
    retryable_errors: List[str] = field(default_factory=lambda: [
        'ThrottlingException',
        'ServiceUnavailableException',
        'InternalServerException',
        'ModelTimeoutException',
        'ModelNotReadyException'
    ])


@dataclass
class BedrockConfig:
    """Configuration class for AWS Bedrock integration"""
    
    # AWS Configuration
    aws_region: str = field(default_factory=lambda: get_env_value("AWS_REGION", "us-east-1", str))
    aws_profile: Optional[str] = field(default_factory=lambda: get_env_value("AWS_PROFILE", None, str))
    
    # Model Configuration
    claude_model_id: str = field(default_factory=lambda: get_env_value(
        "BEDROCK_CLAUDE_MODEL_ID", 
        "anthropic.claude-3-5-sonnet-20241022-v2:0", 
        str
    ))
    claude_haiku_model_id: str = field(default_factory=lambda: get_env_value(
        "BEDROCK_CLAUDE_HAIKU_MODEL_ID", 
        "anthropic.claude-3-haiku-20240307-v1:0", 
        str
    ))
    titan_embedding_model_id: str = field(default_factory=lambda: get_env_value(
        "BEDROCK_TITAN_EMBEDDING_MODEL_ID", 
        "amazon.titan-embed-text-v2:0", 
        str
    ))
    
    # Model Parameters
    max_tokens: int = field(default_factory=lambda: get_env_value("BEDROCK_MAX_TOKENS", 4096, int))
    temperature: float = field(default_factory=lambda: get_env_value("BEDROCK_TEMPERATURE", 0.7, float))
    top_p: float = field(default_factory=lambda: get_env_value("BEDROCK_TOP_P", 0.9, float))
    top_k: int = field(default_factory=lambda: get_env_value("BEDROCK_TOP_K", 250, int))
    
    # Retry Configuration
    retry_max_attempts: int = field(default_factory=lambda: get_env_value("BEDROCK_RETRY_MAX_ATTEMPTS", 3, int))
    retry_backoff_factor: float = field(default_factory=lambda: get_env_value("BEDROCK_RETRY_BACKOFF_FACTOR", 2.0, float))
    retry_max_backoff: float = field(default_factory=lambda: get_env_value("BEDROCK_RETRY_MAX_BACKOFF", 60.0, float))
    
    # Request Configuration
    request_timeout: int = field(default_factory=lambda: get_env_value("BEDROCK_REQUEST_TIMEOUT", 300, int))
    max_concurrent_requests: int = field(default_factory=lambda: get_env_value("BEDROCK_MAX_CONCURRENT_REQUESTS", 10, int))
    
    # Embedding Configuration
    embedding_batch_size: int = field(default_factory=lambda: get_env_value("BEDROCK_EMBEDDING_BATCH_SIZE", 25, int))
    embedding_dimensions: Optional[int] = field(default_factory=lambda: get_env_value("BEDROCK_EMBEDDING_DIMENSIONS", None, int))
    
    # Vision Configuration
    max_image_size: int = field(default_factory=lambda: get_env_value("BEDROCK_MAX_IMAGE_SIZE", 1024, int))
    image_quality: str = field(default_factory=lambda: get_env_value("BEDROCK_IMAGE_QUALITY", "standard", str))
    
    def __post_init__(self):
        """Post-initialization validation"""
        self.validate()
    
    @classmethod
    def from_env(cls) -> 'BedrockConfig':
        """Create configuration from environment variables"""
        return cls()
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        errors = []
        
        # Validate AWS region
        if not self.aws_region:
            errors.append("AWS region is required")
        
        # Validate model IDs
        if not self.claude_model_id:
            errors.append("Claude model ID is required")
        if not self.claude_haiku_model_id:
            errors.append("Claude Haiku model ID is required")
        if not self.titan_embedding_model_id:
            errors.append("Titan embedding model ID is required")
        
        # Validate numeric parameters
        if self.max_tokens <= 0:
            errors.append("max_tokens must be positive")
        if not 0.0 <= self.temperature <= 2.0:
            errors.append("temperature must be between 0.0 and 2.0")
        if not 0.0 <= self.top_p <= 1.0:
            errors.append("top_p must be between 0.0 and 1.0")
        if self.top_k <= 0:
            errors.append("top_k must be positive")
        
        # Validate retry configuration
        if self.retry_max_attempts <= 0:
            errors.append("retry_max_attempts must be positive")
        if self.retry_backoff_factor <= 1.0:
            errors.append("retry_backoff_factor must be greater than 1.0")
        if self.retry_max_backoff <= 0:
            errors.append("retry_max_backoff must be positive")
        
        # Validate request configuration
        if self.request_timeout <= 0:
            errors.append("request_timeout must be positive")
        if self.max_concurrent_requests <= 0:
            errors.append("max_concurrent_requests must be positive")
        
        # Validate embedding configuration
        if self.embedding_batch_size <= 0:
            errors.append("embedding_batch_size must be positive")
        if self.embedding_dimensions is not None and self.embedding_dimensions <= 0:
            errors.append("embedding_dimensions must be positive if specified")
        
        # Validate vision configuration
        if self.max_image_size <= 0:
            errors.append("max_image_size must be positive")
        if self.image_quality not in ["standard", "high"]:
            errors.append("image_quality must be 'standard' or 'high'")
        
        if errors:
            raise BedrockConfigurationError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return True
    
    def get_retry_config(self) -> RetryConfig:
        """Get retry configuration"""
        return RetryConfig(
            max_attempts=self.retry_max_attempts,
            backoff_factor=self.retry_backoff_factor,
            max_backoff=self.retry_max_backoff
        )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            "aws_region": self.aws_region,
            "aws_profile": self.aws_profile,
            "claude_model_id": self.claude_model_id,
            "claude_haiku_model_id": self.claude_haiku_model_id,
            "titan_embedding_model_id": self.titan_embedding_model_id,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "retry_max_attempts": self.retry_max_attempts,
            "retry_backoff_factor": self.retry_backoff_factor,
            "retry_max_backoff": self.retry_max_backoff,
            "request_timeout": self.request_timeout,
            "max_concurrent_requests": self.max_concurrent_requests,
            "embedding_batch_size": self.embedding_batch_size,
            "embedding_dimensions": self.embedding_dimensions,
            "max_image_size": self.max_image_size,
            "image_quality": self.image_quality,
        }