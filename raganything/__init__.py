from .raganything import RAGAnything as RAGAnything
from .config import RAGAnythingConfig as RAGAnythingConfig

# AWS Bedrock integration
try:
    from .bedrock_rag import BedrockRAGAnything as BedrockRAGAnything
    from .bedrock import BedrockConfig as BedrockConfig
    _bedrock_available = True
except ImportError:
    _bedrock_available = False
    BedrockRAGAnything = None
    BedrockConfig = None

__version__ = "1.2.8"
__author__ = "Zirui Guo"
__url__ = "https://github.com/HKUDS/RAG-Anything"

if _bedrock_available:
    __all__ = ["RAGAnything", "RAGAnythingConfig", "BedrockRAGAnything", "BedrockConfig"]
else:
    __all__ = ["RAGAnything", "RAGAnythingConfig"]
