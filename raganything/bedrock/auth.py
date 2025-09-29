"""
AWS Bedrock authentication and client management
"""

import asyncio
import logging
from typing import Optional, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from botocore.config import Config

from .config import BedrockConfig
from .exceptions import BedrockAuthenticationError, BedrockConfigurationError


logger = logging.getLogger(__name__)


class BedrockAuthenticator:
    """Handle AWS authentication and Bedrock client management"""
    
    def __init__(self, config: BedrockConfig):
        self.config = config
        self.session = None
        self.bedrock_client = None
        self.bedrock_runtime_client = None
        self._client_lock = asyncio.Lock()
        
    async def get_bedrock_client(self) -> Any:
        """Get authenticated Bedrock client with automatic refresh"""
        async with self._client_lock:
            if self.bedrock_client is None:
                await self._create_clients()
            return self.bedrock_client
    
    async def get_bedrock_runtime_client(self) -> Any:
        """Get authenticated Bedrock Runtime client with automatic refresh"""
        async with self._client_lock:
            if self.bedrock_runtime_client is None:
                await self._create_clients()
            return self.bedrock_runtime_client
    
    async def _create_clients(self):
        """Create Bedrock clients with proper configuration"""
        try:
            # Create boto3 session
            if self.config.aws_profile:
                self.session = boto3.Session(profile_name=self.config.aws_profile)
            else:
                self.session = boto3.Session()
            
            # Configure boto3 client settings
            client_config = Config(
                region_name=self.config.aws_region,
                retries={
                    'max_attempts': self.config.retry_max_attempts,
                    'mode': 'adaptive'
                },
                max_pool_connections=self.config.max_concurrent_requests,
                read_timeout=self.config.request_timeout,
                connect_timeout=30,
            )
            
            # Create Bedrock clients
            self.bedrock_client = self.session.client(
                'bedrock',
                config=client_config
            )
            
            self.bedrock_runtime_client = self.session.client(
                'bedrock-runtime',
                config=client_config
            )
            
            logger.info(f"Created Bedrock clients for region: {self.config.aws_region}")
            
        except (NoCredentialsError, PartialCredentialsError) as e:
            error_msg = f"AWS credentials not found or incomplete: {str(e)}"
            logger.error(error_msg)
            raise BedrockAuthenticationError(error_msg) from e
        except ClientError as e:
            error_msg = f"Failed to create Bedrock clients: {str(e)}"
            logger.error(error_msg)
            raise BedrockAuthenticationError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error creating Bedrock clients: {str(e)}"
            logger.error(error_msg)
            raise BedrockAuthenticationError(error_msg) from e
    
    async def validate_permissions(self) -> bool:
        """Validate that the credentials have required Bedrock permissions"""
        try:
            client = await self.get_bedrock_client()
            
            # Test basic Bedrock access by listing foundation models
            response = client.list_foundation_models()
            models = response.get('modelSummaries', [])
            
            # Check if required models are available
            available_model_ids = {model['modelId'] for model in models}
            
            required_models = [
                self.config.claude_model_id,
                self.config.claude_haiku_model_id,
                self.config.titan_embedding_model_id
            ]
            
            missing_models = []
            for model_id in required_models:
                if model_id not in available_model_ids:
                    missing_models.append(model_id)
            
            if missing_models:
                error_msg = f"Required models not available or accessible: {missing_models}"
                logger.error(error_msg)
                raise BedrockAuthenticationError(error_msg)
            
            logger.info("Successfully validated Bedrock permissions and model access")
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = f"Permission validation failed with error {error_code}: {str(e)}"
            logger.error(error_msg)
            raise BedrockAuthenticationError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during permission validation: {str(e)}"
            logger.error(error_msg)
            raise BedrockAuthenticationError(error_msg) from e
    
    async def test_model_access(self, model_id: str) -> bool:
        """Test access to a specific model"""
        try:
            client = await self.get_bedrock_client()
            
            # Get model details to verify access
            response = client.get_foundation_model(modelIdentifier=model_id)
            
            model_details = response.get('modelDetails', {})
            logger.info(f"Successfully accessed model {model_id}: {model_details.get('modelName', 'Unknown')}")
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'AccessDeniedException':
                error_msg = f"Access denied to model {model_id}. Check IAM permissions."
            elif error_code == 'ResourceNotFoundException':
                error_msg = f"Model {model_id} not found or not available in region {self.config.aws_region}"
            else:
                error_msg = f"Failed to access model {model_id} with error {error_code}: {str(e)}"
            
            logger.error(error_msg)
            raise BedrockAuthenticationError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error testing model access for {model_id}: {str(e)}"
            logger.error(error_msg)
            raise BedrockAuthenticationError(error_msg) from e
    
    def handle_auth_error(self, error: Exception) -> None:
        """Handle authentication errors with appropriate logging"""
        if isinstance(error, ClientError):
            error_code = error.response.get('Error', {}).get('Code', 'Unknown')
            error_message = error.response.get('Error', {}).get('Message', str(error))
            
            if error_code == 'UnauthorizedOperation':
                logger.error("Unauthorized operation. Check IAM permissions for Bedrock access.")
            elif error_code == 'AccessDeniedException':
                logger.error("Access denied. Ensure IAM role has necessary Bedrock permissions.")
            elif error_code == 'TokenRefreshRequired':
                logger.error("AWS credentials expired. Refresh credentials or check IAM role.")
            else:
                logger.error(f"AWS error {error_code}: {error_message}")
        else:
            logger.error(f"Authentication error: {str(error)}")
    
    async def refresh_clients(self):
        """Force refresh of Bedrock clients"""
        async with self._client_lock:
            self.bedrock_client = None
            self.bedrock_runtime_client = None
            await self._create_clients()
            logger.info("Refreshed Bedrock clients")
    
    def get_caller_identity(self) -> dict:
        """Get AWS caller identity for debugging"""
        try:
            sts_client = self.session.client('sts')
            return sts_client.get_caller_identity()
        except Exception as e:
            logger.error(f"Failed to get caller identity: {str(e)}")
            return {}
    
    def close(self):
        """Clean up resources"""
        if self.bedrock_client:
            self.bedrock_client.close()
        if self.bedrock_runtime_client:
            self.bedrock_runtime_client.close()
        logger.info("Closed Bedrock clients")