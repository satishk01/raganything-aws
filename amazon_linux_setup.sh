#!/bin/bash

# Complete setup script for RAG Anything with AWS Bedrock on Amazon Linux 2
# This script handles all dependencies and testing

set -e  # Exit on any error

echo "🚀 RAG Anything with AWS Bedrock - Amazon Linux 2 Setup"
echo "=" * 60

# Function to print colored output
print_status() {
    echo -e "\033[1;32m$1\033[0m"
}

print_error() {
    echo -e "\033[1;31m$1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m$1\033[0m"
}

# Check if we're running on Amazon Linux
if ! grep -q "Amazon Linux" /etc/os-release 2>/dev/null; then
    print_warning "⚠️  This script is optimized for Amazon Linux 2"
    print_warning "   It may work on other systems but is not guaranteed"
fi

print_status "📋 System Information:"
echo "   OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
echo "   Architecture: $(uname -m)"
echo "   User: $(whoami)"
echo "   Working Directory: $(pwd)"

# Step 1: Update system packages
print_status "\n📦 Step 1: Updating system packages..."
sudo yum update -y

# Step 2: Install system dependencies
print_status "\n📦 Step 2: Installing system dependencies..."
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
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
    zlib-devel \
    bzip2-devel \
    readline-devel \
    sqlite-devel \
    tk-devel \
    libxml2-devel \
    libxslt-devel \
    libjpeg-devel \
    freetype-devel

# Step 3: Install Python 3.11 if not available
print_status "\n🐍 Step 3: Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "   Current Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.9" ]]; then
    print_status "   Installing Python 3.11 from source..."
    cd /tmp
    wget https://www.python.org/ftp/python/3.11.7/Python-3.11.7.tgz
    tar xzf Python-3.11.7.tgz
    cd Python-3.11.7
    ./configure --enable-optimizations --with-ensurepip=install
    make -j$(nproc)
    sudo make altinstall
    cd -
    PYTHON_CMD="python3.11"
else
    PYTHON_CMD="python3"
fi

echo "   Using Python: $PYTHON_CMD"

# Step 4: Create virtual environment
print_status "\n📦 Step 4: Creating virtual environment..."
if [ -d "venv" ]; then
    print_status "   Removing existing virtual environment..."
    rm -rf venv
fi

$PYTHON_CMD -m venv venv
source venv/bin/activate

# Upgrade pip in virtual environment
print_status "   Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Step 5: Install core dependencies
print_status "\n📦 Step 5: Installing core dependencies..."
pip install --no-cache-dir \
    boto3>=1.34.0 \
    botocore>=1.34.0 \
    python-dotenv>=1.0.0 \
    asyncio-throttle>=1.0.0 \
    tenacity>=8.0.0 \
    aiofiles \
    numpy \
    pandas \
    tqdm

# Step 6: Install LightRAG
print_status "\n📦 Step 6: Installing LightRAG..."
pip install --no-cache-dir lightrag-hku

# Step 7: Install MinerU (optional, for document processing)
print_status "\n📦 Step 7: Installing MinerU..."
pip install --no-cache-dir "mineru[core]" || {
    print_warning "   ⚠️  MinerU installation failed, continuing without it..."
    print_warning "   Document processing may be limited"
}

# Step 8: Install HuggingFace Hub
print_status "\n📦 Step 8: Installing HuggingFace Hub..."
pip install --no-cache-dir huggingface_hub

# Step 9: Install the RAG Anything package
print_status "\n📦 Step 9: Installing RAG Anything package..."
pip install -e . --no-cache-dir

# Step 10: Create environment configuration
print_status "\n⚙️  Step 10: Creating environment configuration..."
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
    print_status "   ✅ .env file created"
else
    print_status "   ✅ .env file already exists"
fi

# Step 11: Verify installation
print_status "\n🧪 Step 11: Verifying installation..."
python -c "
import sys
print(f'Python version: {sys.version}')
print(f'Python executable: {sys.executable}')

try:
    import raganything
    print('✅ raganything module imported successfully')
    print(f'   Location: {raganything.__file__}')
except ImportError as e:
    print(f'❌ Failed to import raganything: {e}')
    sys.exit(1)

try:
    from raganything.bedrock_rag import BedrockRAGAnything
    print('✅ BedrockRAGAnything imported successfully')
except ImportError as e:
    print(f'❌ Failed to import BedrockRAGAnything: {e}')
    sys.exit(1)

try:
    from raganything.bedrock import BedrockConfig
    print('✅ BedrockConfig imported successfully')
except ImportError as e:
    print(f'❌ Failed to import BedrockConfig: {e}')
    sys.exit(1)

print('🎉 All imports successful!')
"

if [ $? -eq 0 ]; then
    print_status "✅ Installation verification passed!"
else
    print_error "❌ Installation verification failed!"
    exit 1
fi

# Step 12: Create test directories
print_status "\n📁 Step 12: Creating test directories..."
mkdir -p logs
mkdir -p rag_storage
mkdir -p output

print_status "\n🎉 Setup completed successfully!"
print_status "\n📋 Next steps:"
echo "   1. Activate virtual environment: source venv/bin/activate"
echo "   2. Test basic functionality: python test_bedrock_setup.py"
echo "   3. Run basic example: python examples/bedrock_basic_example.py"
echo "   4. Try multimodal example: python examples/bedrock_multimodal_example.py"

print_status "\n🔧 Important notes:"
echo "   - Make sure your EC2 instance has IAM role with Bedrock permissions"
echo "   - Ensure Claude and Titan models are enabled in AWS Bedrock console"
echo "   - Default region is set to us-east-1 in .env file"

print_status "\n📁 Files created:"
echo "   - venv/ (Python virtual environment)"
echo "   - .env (environment configuration)"
echo "   - logs/ (log directory)"
echo "   - rag_storage/ (RAG storage directory)"
echo "   - output/ (output directory)"

print_status "\n✅ Amazon Linux 2 setup complete!"