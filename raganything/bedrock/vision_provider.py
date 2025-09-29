"""
AWS Bedrock vision provider for multimodal image analysis
"""

import json
import asyncio
import logging
import base64
from typing import Dict, List, Optional, Any, Union
from PIL import Image
import io
from botocore.exceptions import ClientError

from .config import BedrockConfig
from .auth import BedrockAuthenticator
from .retry_handler import BedrockRetryHandler
from .exceptions import BedrockModelError, BedrockTimeoutError


logger = logging.getLogger(__name__)


class BedrockVisionProvider:
    """Handle multimodal (text + image) processing using Claude's vision capabilities"""
    
    def __init__(self, config: BedrockConfig, authenticator: BedrockAuthenticator):
        self.config = config
        self.auth = authenticator
        self.retry_handler = BedrockRetryHandler(config.get_retry_config())
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        
    async def analyze_image(
        self,
        prompt: str,
        image_data: str,  # base64 encoded
        system_prompt: Optional[str] = None,
        model_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Analyze image with text prompt using Claude vision"""
        
        # Use Claude Sonnet for vision tasks (has vision capabilities)
        if model_id is None:
            model_id = self.config.claude_model_id
        
        # Prepare image data
        processed_image_data = self._prepare_image_for_bedrock(image_data)
        
        # Build multimodal message
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": processed_image_data
                    }
                }
            ]
        }]
        
        # Prepare request payload
        request_payload = self._prepare_vision_request(
            messages=messages,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Execute request with retry logic
        async with self._semaphore:
            response = await self.retry_handler.execute_with_retry(
                self._invoke_vision_model,
                model_id=model_id,
                request_payload=request_payload
            )
        
        return self._extract_text_from_response(response)
    
    async def analyze_multimodal_messages(
        self,
        messages: List[Dict],
        model_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Process multimodal messages format"""
        
        # Use Claude Sonnet for vision tasks
        if model_id is None:
            model_id = self.config.claude_model_id
        
        # Process messages to ensure images are properly formatted
        processed_messages = self._process_multimodal_messages(messages)
        
        # Extract system prompt if present
        system_prompt = None
        filtered_messages = []
        
        for message in processed_messages:
            if message.get("role") == "system":
                system_prompt = message.get("content", "")
            else:
                filtered_messages.append(message)
        
        # Prepare request payload
        request_payload = self._prepare_vision_request(
            messages=filtered_messages,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Execute request with retry logic
        async with self._semaphore:
            response = await self.retry_handler.execute_with_retry(
                self._invoke_vision_model,
                model_id=model_id,
                request_payload=request_payload
            )
        
        return self._extract_text_from_response(response)
    
    async def analyze_multiple_images(
        self,
        prompt: str,
        image_data_list: List[str],  # List of base64 encoded images
        system_prompt: Optional[str] = None,
        model_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Analyze multiple images with a single prompt"""
        
        # Use Claude Sonnet for vision tasks
        if model_id is None:
            model_id = self.config.claude_model_id
        
        # Build content with text and multiple images
        content = [{"type": "text", "text": prompt}]
        
        for i, image_data in enumerate(image_data_list):
            processed_image_data = self._prepare_image_for_bedrock(image_data)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": processed_image_data
                }
            })
        
        # Build message
        messages = [{
            "role": "user",
            "content": content
        }]
        
        # Prepare request payload
        request_payload = self._prepare_vision_request(
            messages=messages,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Execute request with retry logic
        async with self._semaphore:
            response = await self.retry_handler.execute_with_retry(
                self._invoke_vision_model,
                model_id=model_id,
                request_payload=request_payload
            )
        
        return self._extract_text_from_response(response)
    
    def _prepare_image_for_bedrock(
        self,
        image_data: str,
        max_size: Optional[int] = None
    ) -> str:
        """Prepare and optimize image data for Bedrock"""
        try:
            if max_size is None:
                max_size = self.config.max_image_size
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            
            # Open image with PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if image is too large
            if max(image.size) > max_size:
                # Calculate new size maintaining aspect ratio
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                
                logger.debug(f"Resized image from {image_bytes.__sizeof__()} to {new_size}")
            
            # Save optimized image to bytes
            output_buffer = io.BytesIO()
            
            # Determine quality based on config
            quality = 85 if self.config.image_quality == "standard" else 95
            
            image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            optimized_bytes = output_buffer.getvalue()
            
            # Encode back to base64
            optimized_base64 = base64.b64encode(optimized_bytes).decode('utf-8')
            
            logger.debug(f"Image optimization: {len(image_bytes)} -> {len(optimized_bytes)} bytes")
            
            return optimized_base64
            
        except Exception as e:
            logger.error(f"Error preparing image for Bedrock: {str(e)}")
            # Return original image data if optimization fails
            return image_data
    
    def _process_multimodal_messages(self, messages: List[Dict]) -> List[Dict]:
        """Process multimodal messages to ensure proper format"""
        processed_messages = []
        
        for message in messages:
            if not isinstance(message, dict):
                continue
            
            role = message.get("role", "user")
            content = message.get("content")
            
            if isinstance(content, str):
                # Simple text message
                processed_messages.append({
                    "role": role,
                    "content": content
                })
            elif isinstance(content, list):
                # Multimodal content
                processed_content = []
                
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            processed_content.append({
                                "type": "text",
                                "text": item.get("text", "")
                            })
                        elif item.get("type") == "image_url":
                            # Extract base64 data from image URL
                            image_url = item.get("image_url", {}).get("url", "")
                            if image_url.startswith("data:image/"):
                                # Extract base64 data
                                base64_data = image_url.split(",", 1)[-1]
                                processed_image_data = self._prepare_image_for_bedrock(base64_data)
                                
                                processed_content.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": processed_image_data
                                    }
                                })
                
                if processed_content:
                    processed_messages.append({
                        "role": role,
                        "content": processed_content
                    })
        
        return processed_messages
    
    def _prepare_vision_request(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """Prepare request payload for vision model"""
        
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
    
    async def _invoke_vision_model(self, model_id: str, request_payload: Dict) -> Dict:
        """Invoke Bedrock vision model with request payload"""
        try:
            client = await self.auth.get_bedrock_runtime_client()
            
            # Convert request payload to JSON
            request_body = json.dumps(request_payload)
            
            logger.debug(f"Invoking vision model {model_id} with payload size: {len(request_body)} bytes")
            
            # Make the API call
            response = client.invoke_model(
                modelId=model_id,
                body=request_body,
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Log token usage if available
            if 'usage' in response_body:
                usage = response_body['usage']
                logger.info(f"Vision model token usage - Input: {usage.get('input_tokens', 0)}, Output: {usage.get('output_tokens', 0)}")
            
            return response_body
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == 'ValidationException':
                # Check if it's an image-related validation error
                if "image" in error_message.lower():
                    raise BedrockModelError(f"Image validation error for model {model_id}: {error_message}") from e
                else:
                    raise BedrockModelError(f"Invalid request for vision model {model_id}: {error_message}") from e
            else:
                raise BedrockModelError(f"Vision model {model_id} error {error_code}: {error_message}") from e
        
        except Exception as e:
            raise BedrockModelError(f"Unexpected error invoking vision model {model_id}: {str(e)}") from e
    
    def _extract_text_from_response(self, response: Dict) -> str:
        """Extract text content from Claude vision response"""
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
            logger.warning(f"No text content found in vision response: {response}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from vision response: {str(e)}")
            return ""
    
    def validate_image_data(self, image_data: str) -> bool:
        """Validate base64 image data"""
        try:
            # Try to decode and open the image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Check image size
            if max(image.size) > self.config.max_image_size * 2:  # Allow some buffer
                logger.warning(f"Image size {image.size} exceeds recommended maximum")
                return False
            
            # Check image format
            if image.format not in ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP']:
                logger.warning(f"Unsupported image format: {image.format}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Invalid image data: {str(e)}")
            return False
    
    def get_image_info(self, image_data: str) -> Dict:
        """Get information about an image"""
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            return {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height,
                "bytes": len(image_bytes)
            }
        except Exception as e:
            logger.error(f"Error getting image info: {str(e)}")
            return {}