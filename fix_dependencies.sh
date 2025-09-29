#!/bin/bash

# Fix all dependency issues for RAG Anything with AWS Bedrock

echo "🔧 Fixing all dependency issues..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this script from the raganything-aws root directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔄 Activating existing virtual environment..."
    source venv/bin/activate
else
    echo "📦 Creating new virtual environment..."
    python3.11 -m venv venv
    source venv/bin/activate
fi

# Clean pip cache to avoid space issues
echo "🧹 Cleaning pip cache..."
pip cache purge

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --no-cache-dir

# Install core dependencies first
echo "📦 Installing core dependencies..."
pip install --no-cache-dir \
    boto3 \
    botocore \
    python-dotenv \
    asyncio-throttle \
    tenacity

# Install LightRAG with specific version that works
echo "📦 Installing LightRAG..."
pip install --no-cache-dir lightrag

# Install numpy and basic ML libraries
echo "📦 Installing ML libraries..."
pip install --no-cache-dir \
    numpy \
    pandas \
    scikit-learn

# Install document processing libraries
echo "📦 Installing document processing libraries..."
pip install --no-cache-dir \
    python-docx \
    openpyxl \
    python-pptx \
    PyPDF2 \
    pdfplumber \
    Pillow

# Install transformers and sentence-transformers (CPU only)
echo "📦 Installing transformers (CPU only)..."
pip install --no-cache-dir \
    transformers \
    sentence-transformers \
    torch --index-url https://download.pytorch.org/whl/cpu

# Install vector database (CPU version)
echo "📦 Installing vector database..."
pip install --no-cache-dir faiss-cpu

# Install the current package in development mode
echo "📦 Installing RAG Anything in development mode..."
pip install -e . --no-cache-dir

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cat > .env << 'EOF'
# AWS Configuration
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1

# Bedrock Model Configuration
BEDROCK_CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_CLAUDE_HAIKU_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_TITAN_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0

# Model Parameters
BEDROCK_MAX_TOKENS=4096
BEDROCK_TEMPERATURE=0.7
BEDROCK_RETRY_MAX_ATTEMPTS=3
BEDROCK_RETRY_BACKOFF_FACTOR=2.0

# RAG Anything Configuration
WORKING_DIR=./rag_storage
OUTPUT_DIR=./output
PARSER=mineru
PARSE_METHOD=auto

# Multimodal Processing
ENABLE_IMAGE_PROCESSING=true
ENABLE_TABLE_PROCESSING=true
ENABLE_EQUATION_PROCESSING=true

# Performance Settings
MAX_CONCURRENT_FILES=2
CONTEXT_WINDOW=1
MAX_CONTEXT_TOKENS=2000

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=./logs
EOF
    echo "✅ .env file created"
fi

# Test the installation
echo "🧪 Testing installation..."
python -c "
import sys
print('Python version:', sys.version)

try:
    import lightrag
    print('✅ LightRAG imported successfully')
    print('   Version:', getattr(lightrag, '__version__', 'unknown'))
    print('   Location:', lightrag.__file__)
except ImportError as e:
    print('❌ LightRAG import failed:', e)

try:
    import boto3
    print('✅ Boto3 imported successfully')
except ImportError as e:
    print('❌ Boto3 import failed:', e)

try:
    from raganything.compat import get_env_value
    print('✅ Compatibility layer working')
    test_val = get_env_value('TEST_VAR', 'default', str)
    print('   Test value:', test_val)
except ImportError as e:
    print('❌ Compatibility layer failed:', e)

try:
    from raganything import RAGAnythingConfig
    print('✅ RAGAnythingConfig imported successfully')
except ImportError as e:
    print('❌ RAGAnythingConfig import failed:', e)

try:
    from raganything.bedrock import BedrockConfig
    print('✅ BedrockConfig imported successfully')
except ImportError as e:
    print('❌ BedrockConfig import failed:', e)

try:
    from raganything.bedrock_rag import BedrockRAGAnything
    print('✅ BedrockRAGAnything imported successfully')
except ImportError as e:
    print('❌ BedrockRAGAnything import failed:', e)
"

echo ""
echo "✅ Dependency fix completed!"
echo ""
echo "🧪 Now test with:"
echo "   source venv/bin/activate"
echo "   python examples/bedrock_basic_example.py"
echo ""
echo "📋 If you still get import errors:"
echo "   1. Make sure you're in the virtual environment: source venv/bin/activate"
echo "   2. Check Python path: export PYTHONPATH=\$PWD:\$PYTHONPATH"
echo "   3. Try the simple test: python test_bedrock_simple.py"