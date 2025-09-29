#!/bin/bash

# Setup and test RAG Anything with AWS Bedrock
# This script properly installs dependencies and runs tests

echo "🔧 Setting up RAG Anything with AWS Bedrock..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this script from the raganything-aws root directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --no-cache-dir

# Install required dependencies
echo "📦 Installing required dependencies..."

# Install core dependencies first
pip install --no-cache-dir \
    boto3 \
    botocore \
    python-dotenv \
    asyncio-throttle \
    tenacity \
    aiofiles

# Install LightRAG (the missing dependency)
echo "📦 Installing LightRAG..."
pip install --no-cache-dir lightrag

# Install RAG Anything dependencies
echo "📦 Installing RAG Anything dependencies..."
pip install --no-cache-dir \
    numpy \
    pandas \
    scikit-learn \
    transformers \
    sentence-transformers \
    faiss-cpu \
    chromadb \
    langchain \
    langchain-community

# Install document processing libraries
echo "📦 Installing document processing libraries..."
pip install --no-cache-dir \
    python-docx \
    openpyxl \
    python-pptx \
    PyPDF2 \
    pdfplumber \
    Pillow

# Install the current package in development mode
echo "📦 Installing RAG Anything in development mode..."
pip install -e . --no-cache-dir

# Set up environment variables
echo "⚙️  Setting up environment variables..."
if [ ! -f ".env" ]; then
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
    echo "✅ Created .env file"
else
    echo "✅ .env file already exists"
fi

# Create a simple test script
echo "📝 Creating test script..."
cat > test_bedrock_simple.py << 'EOF'
#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

try:
    from raganything.bedrock_rag import BedrockRAGAnything
    from raganything import RAGAnythingConfig
    from raganything.bedrock import BedrockConfig
    print("✅ Successfully imported RAG Anything modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Available modules:")
    try:
        import raganything
        print(f"  - raganything: {raganything.__file__}")
    except:
        print("  - raganything: Not available")
    
    try:
        import lightrag
        print(f"  - lightrag: {lightrag.__file__}")
    except:
        print("  - lightrag: Not available")
    
    sys.exit(1)

async def test_bedrock_integration():
    """Test basic Bedrock integration"""
    
    print("🚀 Testing RAG Anything with AWS Bedrock")
    print("=" * 50)
    
    try:
        # Create configurations
        rag_config = RAGAnythingConfig(
            working_dir="./rag_storage",
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )
        
        bedrock_config = BedrockConfig.from_env()
        print(f"✅ Configuration loaded - Region: {bedrock_config.aws_region}")
        
        # Initialize RAG Anything with Bedrock
        rag = BedrockRAGAnything(
            config=rag_config,
            bedrock_config=bedrock_config
        )
        
        print("✅ RAG Anything initialized successfully")
        
        # Validate Bedrock access
        print("\n🔍 Validating Bedrock access...")
        if await rag.validate_bedrock_access():
            print("✅ Bedrock access validation successful")
        else:
            print("❌ Bedrock access validation failed")
            print("   Make sure your EC2 instance has the proper IAM role for Bedrock access")
            return False
        
        # Test basic text query
        print("\n🔍 Testing basic text query...")
        result = await rag.aquery(
            "What is artificial intelligence?",
            mode="naive"
        )
        print(f"✅ Query successful!")
        print(f"📝 Response: {result[:200]}...")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bedrock_integration())
    if success:
        print("\n✅ RAG Anything with Bedrock is working correctly!")
    else:
        print("\n❌ There were issues with the setup")
    sys.exit(0 if success else 1)
EOF

chmod +x test_bedrock_simple.py

echo ""
echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure your EC2 instance has IAM role with Bedrock permissions"
echo "2. Run the test: python test_bedrock_simple.py"
echo "3. If test passes, you can run the examples"
echo ""
echo "🔧 To run examples:"
echo "   source venv/bin/activate"
echo "   python examples/bedrock_basic_example.py"
echo ""
echo "📁 Files created:"
echo "   - venv/ (virtual environment)"
echo "   - .env (environment configuration)"
echo "   - test_bedrock_simple.py (simple test script)"