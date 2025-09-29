"""
AWS Bedrock embedding provider for Amazon Titan models
"""

import json
import asyncio
import logging
import time
from typing import List, Optional, Dict, Any
from botocore.exceptions import ClientError

from .config import BedrockConfig
from .auth import BedrockAuthenticator
from .exceptions import BedrockEmbeddingError, BedrockRateLimitError
from .retry_handler import BedrockRetryHandler


class BedrockEmbeddingProvider:
    """Generate text embeddings using Amazon Titan models"""
    
    def __init__(self, config: BedrockConfig, authenticator: BedrockAuthenticator):
        self.config = config
        self.auth = authenticator
        self.logger = logging.getLogger(__name__)
        self.retry_handler = BedrockRetryHandler(config.retry_config)
        self._embedding_dimension = None
        
    async def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 25
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
            
        self.logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Process in batches to respect API limits
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._process_batch(batch)
            all_embeddings.extend(batch_embeddings)
            
            # Add small delay between batches to avoid rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
                
        return all_embeddings
    
    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        embeddings = await self.embed_texts([text])
        return embeddings[0] if embeddings else []
    
    def get_embedding_dimension(self) -> int:
        """Return the embedding dimension for the configured model"""
        if self._embedding_dimension is None:
            # Titan Text Embeddings V2 dimensions
            if "titan-embed-text-v2" in self.config.titan_embedding_model_id:
                self._embedding_dimension = 1024
            else:
                # Default for other Titan models
                self._embedding_dimension = 1536
                
        return self._embedding_dimension
    
    async def _process_batch(self, texts: List[str]) -> List[List[float]]:
        """Process a batch of texts for embedding"""
        embeddings = []
        
        for text in texts:
            try:
                embedding = await self.retry_handler.execute_with_retry(
                    self._generate_single_embedding,
                    text
                )
                embeddings.append(embedding)
                
            except Exception as e:
                self.logger.error(f"Failed to generate embedding for text: {str(e)}")
                # Return zero vector as fallback
                embeddings.append([0.0] * self.get_embedding_dimension())
                
        return embeddings
    
    async def _generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not text.strip():
            return [0.0] * self.get_embedding_dimension()
            
        # Truncate text if too long (Titan has token limits)
        if len(text) > 8000:  # Conservative limit
            text = text[:8000]
            
        client = await self.auth.get_bedrock_client()
        
        request_body = self._prepare_embedding_request(text)
        
        try:
            response = await asyncio.to_thread(
                client.invoke_model,
                modelId=self.config.titan_embedding_model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            if 'embedding' in response_body:
                return response_body['embedding']
            else:
                raise BedrockEmbeddingError(f"No embedding in response: {response_body}")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ThrottlingException':
                raise BedrockRateLimitError(f"Rate limit exceeded: {str(e)}")
            else:
                raise BedrockEmbeddingError(f"Bedrock API error: {str(e)}")
                
    def _prepare_embedding_request(
        self,
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare request payload for Titan embedding model"""
        request = {
            "inputText": text,
            "dimensions": self.get_embedding_dimension(),
            "normalize": True
        }
        
        # Add any additional parameters
        request.update(kwargs)
        
        return request