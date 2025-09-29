"""
AWS Bedrock integration exceptions
"""


class BedrockError(Exception):
    """Base exception for AWS Bedrock integration errors"""
    pass


class BedrockConfigurationError(BedrockError):
    """Raised when there's an issue with Bedrock configuration"""
    pass


class BedrockAuthenticationError(BedrockError):
    """Raised when there's an authentication issue with AWS Bedrock"""
    pass


class BedrockModelError(BedrockError):
    """Raised when there's an issue with Bedrock model operations"""
    pass


class BedrockTimeoutError(BedrockError):
    """Raised when Bedrock requests timeout"""
    pass


class BedrockRateLimitError(BedrockError):
    """Raised when Bedrock rate limits are exceeded"""
    pass


class BedrockServiceError(BedrockError):
    """Raised when there's an AWS service error"""
    pass