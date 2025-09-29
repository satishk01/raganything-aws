# RAG Anything with AWS Bedrock - API Reference

## Table of Contents
1. [Overview](#overview)
2. [Core Classes](#core-classes)
3. [Configuration](#configuration)
4. [Providers](#providers)
5. [Utilities](#utilities)
6. [Examples](#examples)
7. [Error Handling](#error-handling)

## Overview

The RAG Anything AWS Bedrock integration provides a comprehensive set of classes and utilities for building multimodal RAG applications using AWS Bedrock foundation models.

### Key Components
- **BedrockRAGAnything**: Main integration class
- **BedrockConfig**: Configuration management
- **Provider Classes**: LLM, Vision, and Embedding providers
- **Utilities**: Caching, retry logic, and performance monitoring

## Core Classes

### BedrockRAGAnything

The main class that extends RAGAnything with AWS Bedrock integration.

```python
class BedrockRAGAnything(RAGAnything):
    def __init__(
        self,
        config: Optional[RAGAnythingConfig] = None,
        bedrock_config: Optional[BedrockConfig] = None,
        **kwargs
    )
```

#### Parameters
- `config`: RAGAnything configuration object
- `bedrock_config`: AWS Bedrock specific configuration
- `**kwargs`: Additional arguments passed to parent class

#### Methods

##### `validate_bedrock_access() -> bool`
Validates that AWS Bedrock models are accessible.

```python
async def validate_bedrock_access() -> bool:
    """
    Validate that Bedrock models are accessible
    
    Returns:
        bool: True if all required models are accessible
    """
```

**Example:**
```python
rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
if await rag.validate_bedrock_access():
    print("Bedrock access validated!")
```

##### `get_bedrock_info() -> Dict[str, Any]`
Returns information about the Bedrock configuration and status.

```python
def get_bedrock_info() -> Dict[str, Any]:
    """
    Get information about Bedrock configuration and status
    
    Returns:
        Dict containing configuration details and provider information
    """
```

**Example:**
```python
info = rag.get_bedrock_info()
print(f"Region: {info['bedrock_config']['region']}")
print(f"Embedding dimension: {info['embedding_dimension']}")
```

### create_bedrock_rag()

Convenience function for easy initialization.

```python
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
```

**Example:**
```python
rag = create_bedrock_rag(
    working_dir="./my_rag_storage",
    aws_region="us-west-2",
    enable_image_processing=True
)
```

## Configuration

### BedrockConfig

Configuration class for AWS Bedrock settings.

```python
@dataclass
class BedrockConfig:
    aws_region: str = "us-east-1"
    claude_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    claude_haiku_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    titan_embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    max_tokens: int = 4096
    temperature: float = 0.7
    retry_config: RetryConfig = field(default_factory=RetryConfig)
```

#### Class Methods

##### `from_env() -> BedrockConfig`
Create configuration from environment variables.

```python
@classmethod
def from_env(cls) -> 'BedrockConfig':
    """Create configuration from environment variables"""
```

**Environment Variables:**
- `AWS_REGION`: AWS region
- `BEDROCK_CLAUDE_MODEL_ID`: Claude model ID
- `BEDROCK_CLAUDE_HAIKU_MODEL_ID`: Claude Haiku model ID
- `BEDROCK_TITAN_EMBEDDING_MODEL_ID`: Titan embedding model ID
- `BEDROCK_MAX_TOKENS`: Maximum tokens for generation
- `BEDROCK_TEMPERATURE`: Temperature for generation
- `BEDROCK_RETRY_MAX_ATTEMPTS`: Maximum retry attempts
- `BEDROCK_RETRY_BACKOFF_FACTOR`: Backoff factor for retries

**Example:**
```python
# Set environment variables
os.environ["AWS_REGION"] = "us-west-2"
os.environ["BEDROCK_MAX_TOKENS"] = "8192"

# Create config from environment
config = BedrockConfig.from_env()
```

##### `validate() -> bool`
Validate configuration settings.

```python
def validate(self) -> bool:
    """Validate configuration settings"""
```

### RetryConfig

Configuration for retry logic.

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_factor: float = 2.0
    max_backoff: float = 60.0
    retryable_errors: List[str] = field(default_factory=lambda: [
        'ThrottlingException',
        'ServiceUnavailableException',
        'InternalServerException'
    ])
```

## Providers

### BedrockLLMProvider

Provides LLM functionality using AWS Bedrock Claude models.

```python
class BedrockLLMProvider:
    def __init__(self, config: BedrockConfig, authenticator: BedrockAuthenticator)
```

#### Methods

##### `complete() -> str`
Generate text completion using Claude models.

```python
async def complete(
    self,
    prompt: str,
    system_prompt: Optional[str] = None,
    history_messages: List[Dict] = None,
    model_id: Optional[str] = None,
    **kwargs
) -> str:
    """
    Generate text completion using Claude models
    
    Args:
        prompt: Input prompt
        system_prompt: Optional system prompt
        history_messages: Conversation history
        model_id: Specific model to use (defaults to config)
        **kwargs: Additional model parameters
    
    Returns:
        Generated text response
    """
```

**Example:**
```python
provider = BedrockLLMProvider(config, auth)
response = await provider.complete(
    prompt="What is machine learning?",
    system_prompt="You are a helpful AI assistant.",
    max_tokens=1000,
    temperature=0.7
)
```

##### `complete_batch() -> List[str]`
Process multiple prompts efficiently.

```python
async def complete_batch(
    self,
    prompts: List[str],
    **kwargs
) -> List[str]:
    """Process multiple prompts efficiently"""
```

### BedrockVisionProvider

Handles multimodal (text + image) processing using Claude's vision capabilities.

```python
class BedrockVisionProvider:
    def __init__(self, config: BedrockConfig, authenticator: BedrockAuthenticator)
```

#### Methods

##### `analyze_image() -> str`
Analyze single images with text prompts.

```python
async def analyze_image(
    self,
    prompt: str,
    image_data: str,  # base64 encoded
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """
    Analyze image with text prompt using Claude vision
    
    Args:
        prompt: Text prompt for analysis
        image_data: Base64 encoded image data
        system_prompt: Optional system prompt
        **kwargs: Additional parameters
    
    Returns:
        Analysis result
    """
```

**Example:**
```python
provider = BedrockVisionProvider(config, auth)
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

result = await provider.analyze_image(
    prompt="Describe what you see in this image",
    image_data=image_data
)
```

##### `analyze_multimodal_messages() -> str`
Process multimodal messages format.

```python
async def analyze_multimodal_messages(
    self,
    messages: List[Dict],
    **kwargs
) -> str:
    """Process multimodal messages format"""
```

### BedrockEmbeddingProvider

Generate text embeddings using Amazon Titan models.

```python
class BedrockEmbeddingProvider:
    def __init__(self, config: BedrockConfig, authenticator: BedrockAuthenticator)
```

#### Methods

##### `embed_texts() -> List[List[float]]`
Generate embeddings for multiple texts.

```python
async def embed_texts(
    self,
    texts: List[str],
    batch_size: int = 25
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts
    
    Args:
        texts: List of texts to embed
        batch_size: Batch size for processing
    
    Returns:
        List of embedding vectors
    """
```

**Example:**
```python
provider = BedrockEmbeddingProvider(config, auth)
texts = ["Hello world", "Machine learning", "AWS Bedrock"]
embeddings = await provider.embed_texts(texts)
print(f"Generated {len(embeddings)} embeddings")
```

##### `embed_single() -> List[float]`
Generate embedding for single text.

```python
async def embed_single(self, text: str) -> List[float]:
    """Generate embedding for single text"""
```

##### `get_embedding_dimension() -> int`
Return the embedding dimension for the configured model.

```python
def get_embedding_dimension() -> int:
    """Return the embedding dimension for the configured model"""
```

## Utilities

### BedrockAuthenticator

Handles AWS authentication using IAM roles and temporary credentials.

```python
class BedrockAuthenticator:
    def __init__(self, config: BedrockConfig)
```

#### Methods

##### `get_bedrock_client() -> Any`
Get authenticated Bedrock client with automatic refresh.

```python
async def get_bedrock_client() -> Any:
    """Get authenticated Bedrock client with automatic refresh"""
```

##### `validate_permissions() -> bool`
Validate that the instance has required Bedrock permissions.

```python
async def validate_permissions() -> bool:
    """Validate that the instance has required Bedrock permissions"""
```

### BedrockCache

In-memory cache for Bedrock responses with TTL and LRU eviction.

```python
class BedrockCache:
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600)
```

#### Methods

##### `get() -> Optional[Any]`
Get item from cache.

```python
def get(self, key: str) -> Optional[Any]:
    """Get item from cache"""
```

##### `put() -> None`
Put item in cache.

```python
def put(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
    """Put item in cache"""
```

##### `get_stats() -> Dict[str, Any]`
Get cache statistics.

```python
def get_stats() -> Dict[str, Any]:
    """Get cache statistics"""
```

### BedrockRetryHandler

Handles retry logic with exponential backoff.

```python
class BedrockRetryHandler:
    def __init__(self, config: RetryConfig)
```

#### Methods

##### `execute_with_retry() -> Any`
Execute operation with exponential backoff retry.

```python
async def execute_with_retry(
    self,
    operation: Callable,
    *args,
    **kwargs
) -> Any:
    """Execute operation with exponential backoff retry"""
```

## Examples

### Basic Usage

```python
import asyncio
from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig

async def basic_example():
    # Configure RAG Anything
    rag_config = RAGAnythingConfig(
        working_dir="./rag_storage",
        enable_image_processing=True,
        enable_table_processing=True,
    )
    
    # Configure Bedrock
    bedrock_config = BedrockConfig(
        aws_region="us-east-1",
        max_tokens=4096,
        temperature=0.7
    )
    
    # Initialize
    rag = BedrockRAGAnything(
        config=rag_config,
        bedrock_config=bedrock_config
    )
    
    # Validate access
    if await rag.validate_bedrock_access():
        print("Bedrock access validated!")
    
    # Process document
    await rag.process_document_complete(
        file_path="document.pdf",
        output_dir="./output"
    )
    
    # Query
    result = await rag.aquery(
        "What are the main topics in the document?",
        mode="hybrid"
    )
    print(result)

# Run example
asyncio.run(basic_example())
```

### Multimodal Query

```python
async def multimodal_example():
    rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
    
    # Query with external table data
    result = await rag.aquery_with_multimodal(
        "Analyze this performance data",
        multimodal_content=[{
            "type": "table",
            "table_data": "Model,Accuracy\nBERT,94%\nGPT-3,97%",
            "table_caption": "Model Performance"
        }],
        mode="hybrid"
    )
    print(result)
```

### Vision Analysis

```python
async def vision_example():
    rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
    
    # Query with image
    with open("chart.png", "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    result = await rag.aquery_with_multimodal(
        "What does this chart show?",
        multimodal_content=[{
            "type": "image",
            "img_path": "chart.png",
            "image_caption": ["Performance Chart"]
        }],
        mode="hybrid"
    )
    print(result)
```

## Error Handling

### Exception Classes

The integration defines several custom exception classes:

```python
class BedrockError(Exception):
    """Base exception for Bedrock-related errors"""

class BedrockConfigurationError(BedrockError):
    """Configuration-related errors"""

class BedrockAuthenticationError(BedrockError):
    """Authentication-related errors"""

class BedrockModelError(BedrockError):
    """Model-specific errors"""

class BedrockRateLimitError(BedrockError):
    """Rate limiting errors"""

class BedrockEmbeddingError(BedrockError):
    """Embedding-specific errors"""
```

### Error Handling Patterns

```python
try:
    result = await rag.aquery("What is AI?")
except BedrockRateLimitError:
    print("Rate limit exceeded, waiting...")
    await asyncio.sleep(60)
    result = await rag.aquery("What is AI?")
except BedrockAuthenticationError:
    print("Authentication failed, check IAM permissions")
except BedrockError as e:
    print(f"Bedrock error: {e}")
```

### Retry Logic

The integration automatically handles retryable errors:

```python
# Automatic retry for throttling
provider = BedrockLLMProvider(config, auth)
result = await provider.complete("Hello")  # Automatically retries on throttling
```

### Logging

Enable detailed logging for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed Bedrock API calls and responses
rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
```

## Performance Considerations

### Batch Processing

Use batch methods for better performance:

```python
# Efficient batch embedding
embeddings = await embedding_provider.embed_texts(
    texts=["text1", "text2", "text3"],
    batch_size=25
)

# Efficient batch completion
results = await llm_provider.complete_batch([
    "prompt1", "prompt2", "prompt3"
])
```

### Caching

Enable caching for repeated queries:

```python
# Cache is automatically used for identical queries
result1 = await rag.aquery("What is AI?")  # Calls Bedrock
result2 = await rag.aquery("What is AI?")  # Uses cache
```

### Model Selection

Choose appropriate models for your use case:

```python
# Use Haiku for faster responses
config = BedrockConfig(
    claude_model_id="anthropic.claude-3-haiku-20240307-v1:0"  # Faster
)

# Use Sonnet for better quality
config = BedrockConfig(
    claude_model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"  # Higher quality
)
```

This API reference provides comprehensive documentation for using RAG Anything with AWS Bedrock. For more examples and advanced usage patterns, see the examples directory in the repository.