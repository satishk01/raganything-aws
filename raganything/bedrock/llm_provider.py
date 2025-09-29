"""
AWS Bedrock LLM provider for Claude models
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from botocore.exceptions import ClientError
import time

from .config import BedrockConfig
from .auth import BedrockAuthenticator
from .retry_handler import BedrockRetryHandler
from .exceptions import BedrockModelError, BedrockTimeoutError, BedrockRateLimitError


logger = logging.getLogger(__name__)


class BedrockLLMProvider:
    """Provide LLM functionality using AWS Bedrock Claude models"""
    
    def __init__(self, config: BedrockConfig, authenticator: BedrockAuthenticator):
        self.config = config
        self.auth = authenticator
        self.retry_handler = BedrockRetryHandler(config.get_retry_config())
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: Optional[List[Dict]] = None,
        model_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text completion using Claude models"""
        
        # Use default model if not specified
        if model_id is None:
            model_id = self.config.claude_model_id
        
        # Prepare request payload
        request_payload = self._prepare_claude_request(
            prompt=prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            **kwargs
        )
        
        # Execute request with retry logic
        async with self._semaphore:
            response = await self.retry_handler.execute_with_retry(
                self._invoke_model,
                model_id=model_id,
                request_payload=request_payload
            )
        
        return self._extract_text_from_response(response)
    
    async def complete_fast(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: Optional[List[Dict]] = None,
        **kwargs
    ) -> str:
        """Generate fast completion using Claude Haiku"""
        return await self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            model_id=self.config.claude_haiku_model_id,
            **kwargs
        )
    
    async def complete_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        model_id: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """Process multiple prompts efficiently"""
        
        if not prompts:
            return []
        
        # Create tasks for concurrent processing
        tasks = []
        for prompt in prompts:
            task = self.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                model_id=model_id,
                **kwargs
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing prompt {i}: {str(result)}")
                processed_results.append(f"Error: {str(result)}")
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def complete_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: Optional[List[Dict]] = None,
        model_id: Optional[str] = None,
        **kwargs
    ):
        """Generate streaming completion (async generator)"""
        
        # Use default model if not specified
        if model_id is None:
            model_id = self.config.claude_model_id
        
        # Prepare request payload
        request_payload = self._prepare_claude_request(
            prompt=prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            **kwargs
        )
        
        # Execute streaming request
        async with self._semaphore:
            async for chunk in self._invoke_model_streaming(model_id, request_payload):
                yield chunk
    
    def _prepare_claude_request(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict:
        """Prepare request payload for Claude models"""
        
        # Build messages array
        messages = []
        
        # Add history messages if provided
        if history_messages:
            for msg in history_messages:
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Add current prompt as user message
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Build request payload
        request_body = {
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "top_k": kwargs.get("top_k", self.config.top_k),
            "anthropic_version": "bedrock-2023-05-31"
        }
        
        # Add system prompt if provided
        if system_prompt:
            request_body["system"] = system_prompt
        
        # Add stop sequences if provided
        if "stop_sequences" in kwargs:
            request_body["stop_sequences"] = kwargs["stop_sequences"]
        
        return request_body
    
    async def _invoke_model(self, model_id: str, request_payload: Dict) -> Dict:
        """Invoke Bedrock model with request payload"""
        try:
            client = await self.auth.get_bedrock_runtime_client()
            
            # Convert request payload to JSON
            request_body = json.dumps(request_payload)
            
            logger.debug(f"Invoking model {model_id} with payload size: {len(request_body)} bytes")
            
            # Make the API call
            start_time = time.time()
            response = client.invoke_model(
                modelId=model_id,
                body=request_body,
                contentType="application/json",
                accept="application/json"
            )
            
            # Log response time
            response_time = time.time() - start_time
            logger.debug(f"Model {model_id} responded in {response_time:.2f} seconds")
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Log token usage if available
            if 'usage' in response_body:
                usage = response_body['usage']
                logger.info(f"Token usage - Input: {usage.get('input_tokens', 0)}, Output: {usage.get('output_tokens', 0)}")
            
            return response_body
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == 'ThrottlingException':
                raise BedrockRateLimitError(f"Rate limit exceeded for model {model_id}: {error_message}") from e
            elif error_code == 'ValidationException':
                raise BedrockModelError(f"Invalid request for model {model_id}: {error_message}") from e
            elif error_code == 'AccessDeniedException':
                raise BedrockModelError(f"Access denied to model {model_id}: {error_message}") from e
            elif error_code == 'ModelTimeoutException':
                raise BedrockTimeoutError(f"Model {model_id} timed out: {error_message}") from e
            else:
                raise BedrockModelError(f"Model {model_id} error {error_code}: {error_message}") from e
        
        except json.JSONDecodeError as e:
            raise BedrockModelError(f"Failed to parse response from model {model_id}: {str(e)}") from e
        
        except Exception as e:
            raise BedrockModelError(f"Unexpected error invoking model {model_id}: {str(e)}") from e
    
    async def _invoke_model_streaming(self, model_id: str, request_payload: Dict):
        """Invoke Bedrock model with streaming response"""
        try:
            client = await self.auth.get_bedrock_runtime_client()
            
            # Convert request payload to JSON
            request_body = json.dumps(request_payload)
            
            logger.debug(f"Invoking streaming model {model_id}")
            
            # Make the streaming API call
            response = client.invoke_model_with_response_stream(
                modelId=model_id,
                body=request_body,
                contentType="application/json",
                accept="application/json"
            )
            
            # Process streaming response
            stream = response.get('body')
            if stream:
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_data = json.loads(chunk.get('bytes').decode())
                        
                        # Extract text from chunk
                        if 'delta' in chunk_data and 'text' in chunk_data['delta']:
                            yield chunk_data['delta']['text']
                        elif 'content' in chunk_data:
                            for content in chunk_data['content']:
                                if content.get('type') == 'text':
                                    yield content.get('text', '')
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            raise BedrockModelError(f"Streaming error for model {model_id} ({error_code}): {error_message}") from e
        
        except Exception as e:
            raise BedrockModelError(f"Unexpected streaming error for model {model_id}: {str(e)}") from e
    
    def _extract_text_from_response(self, response: Dict) -> str:
        """Extract text content from Claude response"""
        try:
            # Claude response format
            if 'content' in response:
                content_blocks = response['content']
                if isinstance(content_blocks, list) and len(content_blocks) > 0:
                    # Get the first text block
                    for block in content_blocks:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            return block.get('text', '')
            
            # Fallback: look for direct text field
            if 'text' in response:
                return response['text']
            
            # If no text found, return empty string
            logger.warning(f"No text content found in response: {response}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from response: {str(e)}")
            return ""
    
    async def get_model_info(self, model_id: Optional[str] = None) -> Dict:
        """Get information about a specific model"""
        if model_id is None:
            model_id = self.config.claude_model_id
        
        try:
            client = await self.auth.get_bedrock_client()
            response = client.get_foundation_model(modelIdentifier=model_id)
            return response.get('modelDetails', {})
        except Exception as e:
            logger.error(f"Error getting model info for {model_id}: {str(e)}")
            return {}
    
    async def list_available_models(self) -> List[Dict]:
        """List all available foundation models"""
        try:
            client = await self.auth.get_bedrock_client()
            response = client.list_foundation_models()
            return response.get('modelSummaries', [])
        except Exception as e:
            logger.error(f"Error listing available models: {str(e)}")
            return []