#!/bin/bash

# Quick install of missing dependencies for RAG Anything with Bedrock

echo "🔧 Quick installation of missing dependencies..."

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Not in a virtual environment. Creating one..."
    python3.11 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "✅ Already in virtual environment: $VIRTUAL_ENV"
fi

# Install missing dependencies
echo "📦 Installing missing dependencies..."

# Install LightRAG (the main missing dependency)
pip install --no-cache-dir lightrag

# Install other required dependencies
pip install --no-cache-dir \
    boto3 \
    botocore \
    python-dotenv \
    asyncio-throttle \
    tenacity \
    numpy \
    pandas

# Install the current package
echo "📦 Installing current package..."
pip install -e . --no-cache-dir

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cat > .env << 'EOF'
AWS_REGION=us-east-1
BEDROCK_CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_CLAUDE_HAIKU_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_TITAN_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_MAX_TOKENS=4096
BEDROCK_TEMPERATURE=0.7
WORKING_DIR=./rag_storage
OUTPUT_DIR=./output
PARSER=mineru
PARSE_METHOD=auto
ENABLE_IMAGE_PROCESSING=true
ENABLE_TABLE_PROCESSING=true
ENABLE_EQUATION_PROCESSING=true
LOG_LEVEL=INFO
EOF
    echo "✅ .env file created"
fi

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "🧪 Test the installation:"
echo "   python examples/bedrock_basic_example.py"
echo ""
echo "📋 If you get import errors, make sure to:"
echo "   source venv/bin/activate  # (if not already activated)"
echo "   export PYTHONPATH=\$PWD:\$PYTHONPATH"