#!/bin/bash

# Simple RAG Anything with AWS Bedrock Setup for Amazon Linux 2023
# This script works with existing files and creates what's needed

set -e  # Exit on any error

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                RAG Anything with AWS Bedrock                 ║"
echo "║            Amazon Linux 2023 Setup Script                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

log_info "Starting setup on Amazon Linux 2023..."
log_info "Current directory: $(pwd)"

# Step 1: Check system
log_step "Step 1: Checking system..."
echo "   OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
echo "   User: $(whoami)"
echo "   Available Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "   Available Disk: $(df -h . | tail -1 | awk '{print $4}')"

# Step 2: Update system
log_step "Step 2: Updating system packages..."
sudo dnf update -y

# Step 3: Install system dependencies
log_step "Step 3: Installing system dependencies..."
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-devel \
    git \
    wget \
    curl \
    gcc \
    gcc-c++ \
    make \
    openssl-devel \
    libffi-devel \
    zlib-devel

# Step 4: Create virtual environment
log_step "Step 4: Creating virtual environment..."
if [ -d "venv" ]; then
    log_info "Removing existing virtual environment..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

log_info "Virtual environment created and activated"
python --version

# Step 5: Upgrade pip
log_step "Step 5: Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Step 6: Install core dependencies
log_step "Step 6: Installing core dependencies..."
pip install --no-cache-dir \
    boto3>=1.34.0 \
    botocore>=1.34.0 \
    python-dotenv>=1.0.0 \
    asyncio-throttle>=1.0.0 \
    tenacity>=8.0.0 \
    aiofiles \
    numpy \
    pandas \
    tqdm \
    requests

# Step 7: Install LightRAG
log_step "Step 7: Installing LightRAG..."
pip install --no-cache-dir lightrag-hku

# Step 8: Install HuggingFace Hub
log_step "Step 8: Installing HuggingFace Hub..."
pip install --no-cache-dir huggingface_hub

# Step 9: Install MinerU (optional)
log_step "Step 9: Installing MinerU..."
pip install --no-cache-dir "mineru[core]" || {
    log_warn "MinerU installation failed, continuing without it..."
}

# Step 10: Install RAG Anything package
log_step "Step 10: Installing RAG Anything package..."
pip install -e . --no-cache-dir

# Step 11: Create environment file
log_step "Step 11: Creating environment configuration..."
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

# Performance Settings (CPU-optimized)
MAX_CONCURRENT_FILES=2
CONTEXT_WINDOW=1
MAX_CONTEXT_TOKENS=2000

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=./logs
EOF
    log_info ".env file created"
else
    log_info ".env file already exists"
fi

# Step 12: Create directories
log_step "Step 12: Creating required directories..."
mkdir -p logs rag_storage output data/samples

# Step 13: Create sample data
log_step "Step 13: Creating sample test data..."
cat > data/samples/ai_overview.txt << 'EOF'
Artificial Intelligence and Machine Learning Overview

Artificial Intelligence (AI) is a broad field of computer science focused on creating 
systems that can perform tasks that typically require human intelligence. Machine Learning (ML) 
is a subset of AI that enables systems to learn and improve from experience without being 
explicitly programmed.

Key Concepts in AI/ML:
1. Neural Networks: Computing systems inspired by biological neural networks
2. Deep Learning: ML techniques using neural networks with multiple layers
3. Natural Language Processing (NLP): AI's ability to understand and generate human language
4. Computer Vision: AI's ability to interpret and understand visual information

Applications of AI/ML:
- Healthcare: Medical diagnosis, drug discovery, personalized treatment
- Finance: Fraud detection, algorithmic trading, risk assessment
- Transportation: Autonomous vehicles, route optimization
- Entertainment: Recommendation systems, content generation
EOF

# Step 14: Create simple test script
log_step "Step 14: Creating test script..."
cat > test_rag_setup.py << 'EOF'
#!/usr/bin/env python3
"""Simple test script for RAG Anything with AWS Bedrock"""

import asyncio
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment")

async def test_setup():
    print("\n🧪 Testing RAG Anything with AWS Bedrock Setup")
    print("=" * 50)
    
    # Test imports
    try:
        from raganything import RAGAnythingConfig
        from raganything.bedrock import BedrockConfig
        from raganything.bedrock_rag import BedrockRAGAnything
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test configuration
    try:
        rag_config = RAGAnythingConfig(
            working_dir="./test_rag_storage",
            parser="mineru",
            parse_method="auto"
        )
        bedrock_config = BedrockConfig.from_env()
        print(f"✅ Configuration created - Region: {bedrock_config.aws_region}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False
    
    # Test RAG initialization
    try:
        rag = BedrockRAGAnything(
            config=rag_config,
            bedrock_config=bedrock_config
        )
        print("✅ BedrockRAGAnything initialized")
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")
        return False
    
    # Test Bedrock access
    try:
        access_valid = await rag.validate_bedrock_access()
        if access_valid:
            print("✅ Bedrock access validated successfully!")
            
            # Test simple query
            await rag.insert_content_list([{
                "type": "text",
                "text": "AWS Bedrock is a fully managed service for foundation models.",
                "page_idx": 0
            }], "test.txt", "test-001")
            
            result = await rag.aquery("What is AWS Bedrock?")
            print(f"✅ Query successful: {result[:100]}...")
            
            return True
        else:
            print("❌ Bedrock access validation failed!")
            print("   Make sure your EC2 instance has IAM role with Bedrock permissions")
            return False
    except Exception as e:
        print(f"❌ Bedrock test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_setup())
        if success:
            print("\n🎉 Setup test completed successfully!")
            print("\n📋 Next steps:")
            print("   1. Try: python examples/bedrock_basic_example.py")
            print("   2. Add your documents and start querying!")
        else:
            print("\n❌ Setup test failed. Check the errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
EOF

chmod +x test_rag_setup.py

# Step 15: Verify installation
log_step "Step 15: Verifying installation..."
python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import raganything
    print('✅ raganything imported successfully')
except ImportError as e:
    print(f'❌ raganything import failed: {e}')
    sys.exit(1)

try:
    from raganything.bedrock_rag import BedrockRAGAnything
    print('✅ BedrockRAGAnything imported successfully')
except ImportError as e:
    print(f'❌ BedrockRAGAnything import failed: {e}')
    sys.exit(1)

print('🎉 Installation verification passed!')
"

if [ $? -eq 0 ]; then
    log_info "✅ Installation verification passed!"
else
    log_error "❌ Installation verification failed!"
    exit 1
fi

# Final summary
echo ""
log_info "🎉 RAG Anything with AWS Bedrock setup completed!"
echo ""
echo "📁 Files created:"
echo "   ✅ Virtual environment: venv/"
echo "   ✅ Environment config: .env"
echo "   ✅ Test script: test_rag_setup.py"
echo "   ✅ Sample data: data/samples/"
echo "   ✅ Directories: logs/, rag_storage/, output/"
echo ""
echo "🚀 Next steps:"
echo "   1. Activate environment: source venv/bin/activate"
echo "   2. Run test: python test_rag_setup.py"
echo "   3. Try examples: python examples/bedrock_basic_example.py"
echo ""
echo "⚠️  Important:"
echo "   - Ensure EC2 has IAM role with Bedrock permissions"
echo "   - Verify Claude/Titan models enabled in Bedrock console"
echo ""
log_info "Setup completed successfully! 🎊"