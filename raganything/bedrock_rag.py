"""
BedrockRAGAnything - RAGAnything with AWS Bedrock integration
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass

from lightrag.utils import EmbeddingFunc

from .raganything import RAGAnything
from .config import RAGAnythingConfig
from .bedrock import (
    BedrockConfig,
    BedrockAuthenticator,
    BedrockLLMProvider,
    BedrockVisionProvider,
    BedrockEmbeddingProvider,
    BedrockConfigurationError
)


class BedrockRAGAnything(RAGAnything):
    """Extended RAGAnything class with AWS Bedrock integration"""
    
    def __init__(
        self,
        config: Optional[RAGAnythingConfig] = None,
        bedrock_config: Optional[BedrockConfig] = None,
        **kwargs
    ):
        """
        Initialize BedrockRAGAnything with AWS Bedrock providers
        
        Args:
            config: RAGAnything configuration
            bedrock_config: AWS Bedrock configuration
            **kwargs: Additional arguments passed to parent class
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize Bedrock configuration
        self.bedrock_config = bedrock_config or BedrockConfig.from_env()
        
        # Validate Bedrock configuration
        if not self.bedrock_config.validate():
            raise BedrockConfigurationError("Invalid Bedrock configuration")
            
        # Initialize Bedrock components
        self.bedrock_auth = BedrockAuthenticator(self.bedrock_config)
        self.bedrock_llm = BedrockLLMProvider(self.bedrock_config, self.bedrock_auth)
        self.bedrock_vision = BedrockVisionProvider(self.bedrock_config, self.bedrock_auth)
        self.bedrock_embedding = BedrockEmbeddingProvider(self.bedrock_config, self.bedrock_auth)
        
        self.logger.info("Initialized Bedrock providers")
        
        # Create function wrappers for LightRAG compatibility
        llm_func = self._create_llm_func()
        vision_func = self._create_vision_func()
        embedding_func = self._create_embedding_func()
        
        # Initialize parent class with Bedrock functions
        super().__init__(
            config=config,
            llm_model_func=llm_func,
            vision_model_func=vision_func,
            embedding_func=embedding_func,
            **kwargs
        )
        
        self.logger.info("BedrockRAGAnything initialized successfully")
    
    def _create_llm_func(self) -> Callable:
        """Create LLM function compatible with LightRAG interface"""
        
        async def llm_model_func(
            prompt: str,
            system_prompt: Optional[str] = None,
            history_messages: List[Dict] = None,
            **kwargs
        ) -> str:
            """LLM function wrapper for Bedrock"""
            try:
                # Determine which model to use based on kwargs or default
                model_id = kwargs.get('model_id')
                if not model_id:
                    # Use Haiku for faster responses if specified
                    use_haiku = kwargs.get('use_haiku', False)
                    model_id = (self.bedrock_config.claude_haiku_model_id 
                              if use_haiku 
                              else self.bedrock_config.claude_model_id)
                
                return await self.bedrock_llm.complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    history_messages=history_messages or [],
                    model_id=model_id,
                    **kwargs
                )
            except Exception as e:
                self.logger.error(f"LLM function error: {str(e)}")
                raise
        
        return llm_model_func
    
    def _create_vision_func(self) -> Callable:
        """Create vision function compatible with LightRAG interface"""
        
        async def vision_model_func(
            prompt: str,
            system_prompt: Optional[str] = None,
            history_messages: List[Dict] = None,
            image_data: Optional[str] = None,
            messages: Optional[List[Dict]] = None,
            **kwargs
        ) -> str:
            """Vision function wrapper for Bedrock"""
            try:
                # Handle different input formats
                if messages:
                    # Multimodal messages format
                    return await self.bedrock_vision.analyze_multimodal_messages(
                        messages=messages,
                        **kwargs
                    )
                elif image_data:
                    # Single image format
                    return await self.bedrock_vision.analyze_image(
                        prompt=prompt,
                        image_data=image_data,
                        system_prompt=system_prompt,
                        **kwargs
                    )
                else:
                    # Pure text format - fallback to LLM
                    return await self.bedrock_llm.complete(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        history_messages=history_messages or [],
                        **kwargs
                    )
            except Exception as e:
                self.logger.error(f"Vision function error: {str(e)}")
                raise
        
        return vision_model_func
    
    def _create_embedding_func(self) -> EmbeddingFunc:
        """Create embedding function compatible with LightRAG interface"""
        
        async def embedding_func(texts: List[str]) -> List[List[float]]:
            """Embedding function wrapper for Bedrock"""
            try:
                return await self.bedrock_embedding.embed_texts(texts)
            except Exception as e:
                self.logger.error(f"Embedding function error: {str(e)}")
                raise
        
        return EmbeddingFunc(
            embedding_dim=self.bedrock_embedding.get_embedding_dimension(),
            max_token_size=8192,  # Conservative limit for Titan
            func=embedding_func
        )
    
    async def validate_bedrock_access(self) -> bool:
        """Validate that Bedrock models are accessible"""
        try:
            self.logger.info("Validating Bedrock access...")
            
            # Test authentication
            if not await self.bedrock_auth.validate_permissions():
                self.logger.error("Bedrock authentication failed")
                return False
            
            # Test LLM access
            test_result = await self.bedrock_llm.complete(
                prompt="Hello, this is a test.",
                max_tokens=10
            )
            if not test_result:
                self.logger.error("LLM test failed")
                return False
            
            # Test embedding access
            test_embedding = await self.bedrock_embedding.embed_single("test")
            if not test_embedding:
                self.logger.error("Embedding test failed")
                return False
            
            self.logger.info("✅ Bedrock access validation successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Bedrock access validation failed: {str(e)}")
            return False
    
    def get_bedrock_info(self) -> Dict[str, Any]:
        """Get information about Bedrock configuration and status"""
        return {
            "bedrock_config": {
                "region": self.bedrock_config.aws_region,
                "claude_model": self.bedrock_config.claude_model_id,
                "claude_haiku_model": self.bedrock_config.claude_haiku_model_id,
                "titan_embedding_model": self.bedrock_config.titan_embedding_model_id,
                "max_tokens": self.bedrock_config.max_tokens,
                "temperature": self.bedrock_config.temperature,
            },
            "embedding_dimension": self.bedrock_embedding.get_embedding_dimension(),
            "providers": {
                "llm": self.bedrock_llm.__class__.__name__,
                "vision": self.bedrock_vision.__class__.__name__,
                "embedding": self.bedrock_embedding.__class__.__name__,
            }
        }


# Convenience function for easy initialization
def create_bedrock_rag(
    working_dir: str = "./rag_storage",
    aws_region: str = "us-east-1",
    **kwargs
) -> BedrockRAGAnything:
    """
    Create a BedrockRAGAnything instance with sensible defaults
    
    Args:
        working_dir: Directory for RAG storage
        aws_region: AWS region for Bedrock
        **kwargs: Additional configuration options
    
    Returns:
        Configured BedrockRAGAnything instance
    """
    rag_config = RAGAnythingConfig(
        working_dir=working_dir,
        **kwargs
    )
    
    bedrock_config = BedrockConfig(
        aws_region=aws_region,
        **kwargs
    )
    
    return BedrockRAGAnything(
        config=rag_config,
        bedrock_config=bedrock_config
    )