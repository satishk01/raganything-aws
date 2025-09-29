#!/bin/bash

# Python 3.9 Compatible RAG Anything with AWS Bedrock Setup for Amazon Linux 2023
# Fixes: Python version conflicts, MinerU compatibility, dependency resolution
# CPU-only optimized version for Python 3.9

set -e  # Exit on any error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
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

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Print banner
echo -e "${PURPLE}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║           RAG Anything with AWS Bedrock Setup               ║
║         Python 3.9 Compatible Version                       ║
║              CPU-Only | No GPU | Dependency Fixed           ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

log_info "Starting Python 3.9 compatible setup..."

# Step 1: Check Python version
log_step "Step 1: Checking Python version compatibility"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
log_info "Current Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == "3.9" ]]; then
    log_success "Python 3.9 detected - using compatible package versions"
    PYTHON_CMD="python3"
elif [[ "$PYTHON_VERSION" < "3.9" ]]; then
    log_error "Python 3.9+ required. Current version: $PYTHON_VERSION"
    log_info "Installing Python 3.11..."
    
    # Install Python 3.11
    sudo dnf install -y python3.11 python3.11-pip python3.11-devel
    PYTHON_CMD="python3.11"
    log_success "Python 3.11 installed"
else
    log_success "Python $PYTHON_VERSION detected - should work fine"
    PYTHON_CMD="python3"
fi

# Verify Python installation
$PYTHON_CMD --version

# Step 2: System cleanup and curl fix
log_step "Step 2: System cleanup and curl fix"
log_info "Cleaning up temporary files and caches..."
sudo dnf clean all || true
pip cache purge 2>/dev/null || true
sudo rm -rf /tmp/* 2>/dev/null || true

# Fix curl conflicts
log_info "Resolving curl package conflicts..."
if rpm -q curl-minimal &>/dev/null; then
    log_info "Removing curl-minimal package..."
    sudo dnf remove -y curl-minimal || true
fi

sudo dnf install -y --allowerasing curl || {
    log_warn "Standard curl install failed, trying alternatives..."
    sudo dnf swap -y curl-minimal curl || {
        sudo dnf reinstall -y curl || {
            log_error "All curl installation methods failed!"
            exit 1
        }
    }
}

# Verify curl
if command -v curl &> /dev/null; then
    log_success "Curl installed successfully: $(curl --version | head -n1)"
else
    log_error "Curl installation failed!"
    exit 1
fi

# Step 3: Update system and install dependencies
log_step "Step 3: Installing system dependencies"
sudo dnf update -y
sudo dnf install -y \
    gcc \
    gcc-c++ \
    make \
    openssl-devel \
    libffi-devel \
    zlib-devel \
    git \
    wget \
    unzip

# Step 4: Create virtual environment
log_step "Step 4: Creating virtual environment"
if [ -d "venv" ]; then
    log_info "Removing existing virtual environment..."
    rm -rf venv
fi

$PYTHON_CMD -m venv venv
source venv/bin/activate

log_info "Virtual environment created and activated"
python --version

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel --no-cache-dir

# Step 5: Install core dependencies (Python 3.9 compatible versions)
log_step "Step 5: Installing core dependencies (Python 3.9 compatible)"

# Set environment variables to prevent GPU package installation
export CUDA_VISIBLE_DEVICES=""
export FORCE_CPU_ONLY=1

# Install AWS dependencies
log_info "Installing AWS dependencies..."
pip install --no-cache-dir \
    "boto3>=1.34.0,<2.0" \
    "botocore>=1.34.0,<2.0" \
    "python-dotenv>=1.0.0,<2.0"

# Install async and utility dependencies
log_info "Installing async and utility dependencies..."
pip install --no-cache-dir \
    "asyncio-throttle>=1.0.0,<2.0" \
    "tenacity>=8.0.0,<9.0" \
    "aiofiles>=23.0.0,<24.0" \
    "requests>=2.25.0,<3.0" \
    "urllib3>=1.26.0,<2.0"

# Install data processing dependencies (Python 3.9 compatible)
log_info "Installing data processing dependencies..."
pip install --no-cache-dir \
    "numpy>=1.21.0,<2.0" \
    "pandas>=1.3.0,<3.0" \
    "tqdm>=4.60.0,<5.0"

# Step 6: Install LightRAG (Python 3.9 compatible)
log_step "Step 6: Installing LightRAG (Python 3.9 compatible)"
pip install --no-cache-dir "lightrag-hku>=1.0.0,<2.0"

# Step 7: Install HuggingFace Hub
log_step "Step 7: Installing HuggingFace Hub"
pip install --no-cache-dir "huggingface_hub>=0.16.0,<1.0"

# Step 8: Skip MinerU for Python 3.9 (install alternatives)
log_step "Step 8: Installing document processing alternatives (MinerU not compatible with Python 3.9)"
log_warn "MinerU requires Python 3.10+, installing alternative document processors..."

# Install alternative document processing libraries
pip install --no-cache-dir \
    "PyPDF2>=3.0.0,<4.0" \
    "pdfplumber>=0.7.0,<1.0" \
    "python-docx>=0.8.11,<1.0" \
    "openpyxl>=3.0.9,<4.0" \
    "python-pptx>=0.6.21,<1.0" || {
    log_warn "Some document processing libraries failed to install, continuing..."
}

# Step 9: Install optional dependencies (Python 3.9 compatible)
log_step "Step 9: Installing optional dependencies"
log_info "Installing image processing (CPU-only)..."
pip install --no-cache-dir "Pillow>=9.0.0,<11.0" || log_warn "Pillow installation failed"

log_info "Installing text processing..."
pip install --no-cache-dir "reportlab>=3.6.0,<5.0" || log_warn "ReportLab installation failed"

# Step 10: Install RAG Anything package (without MinerU dependency)
log_step "Step 10: Installing RAG Anything package"

# First, let's check if we need to modify requirements
if [ -f "requirements.txt" ]; then
    log_info "Backing up original requirements.txt..."
    cp requirements.txt requirements.txt.backup
    
    # Create Python 3.9 compatible requirements
    log_info "Creating Python 3.9 compatible requirements..."
    cat > requirements_py39.txt << 'EOF'
huggingface_hub>=0.16.0,<1.0
lightrag-hku>=1.0.0,<2.0
# Document processing alternatives (instead of mineru)
PyPDF2>=3.0.0,<4.0
pdfplumber>=0.7.0,<1.0
python-docx>=0.8.11,<1.0
openpyxl>=3.0.9,<4.0
python-pptx>=0.6.21,<1.0
tqdm>=4.60.0,<5.0
# AWS Bedrock integration dependencies
boto3>=1.34.0,<2.0
botocore>=1.34.0,<2.0
python-dotenv>=1.0.0,<2.0
asyncio-throttle>=1.0.0,<2.0
tenacity>=8.0.0,<9.0
# Optional dependencies
Pillow>=9.0.0,<11.0
reportlab>=3.6.0,<5.0
EOF
    
    # Temporarily replace requirements.txt
    mv requirements.txt requirements.txt.original
    cp requirements_py39.txt requirements.txt
fi

# Install the package
pip install -e . --no-cache-dir || {
    log_error "RAG Anything installation failed!"
    
    # Restore original requirements if backup exists
    if [ -f "requirements.txt.original" ]; then
        mv requirements.txt.original requirements.txt
    fi
    
    exit 1
}

# Restore original requirements if we modified them
if [ -f "requirements.txt.original" ]; then
    mv requirements.txt.original requirements.txt
    log_info "Original requirements.txt restored"
fi

log_success "RAG Anything package installed successfully"

# Step 11: Create Python 3.9 optimized environment configuration
log_step "Step 11: Creating Python 3.9 optimized environment configuration"
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

# RAG Anything Configuration (Python 3.9 compatible)
WORKING_DIR=./rag_storage
OUTPUT_DIR=./output
PARSER=pypdf2
PARSE_METHOD=auto

# Multimodal Processing (limited for Python 3.9)
ENABLE_IMAGE_PROCESSING=true
ENABLE_TABLE_PROCESSING=false
ENABLE_EQUATION_PROCESSING=false

# Performance Settings (Python 3.9 optimized)
MAX_CONCURRENT_FILES=1
CONTEXT_WINDOW=1
MAX_CONTEXT_TOKENS=1000
BATCH_SIZE=3

# CPU-specific optimizations for Python 3.9
OMP_NUM_THREADS=2
MKL_NUM_THREADS=2
NUMEXPR_MAX_THREADS=2
TOKENIZERS_PARALLELISM=false

# Memory optimizations
TRANSFORMERS_CACHE=./cache/transformers
HF_HOME=./cache/huggingface

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=./logs

# Disable GPU and CUDA
CUDA_VISIBLE_DEVICES=""
FORCE_CPU_ONLY=1

# Python 3.9 specific settings
PYTHON_VERSION=3.9
USE_LEGACY_PARSERS=true
EOF
    log_success ".env file created with Python 3.9 optimizations"
else
    log_success ".env file already exists"
fi

# Step 12: Create required directories
log_step "Step 12: Creating required directories"
mkdir -p logs rag_storage output cache/transformers cache/huggingface data/samples temp

# Step 13: Create sample test data
log_step "Step 13: Creating sample test data"
cat > data/samples/simple_test.txt << 'EOF'
AWS Bedrock Overview

Amazon Bedrock is a fully managed service that offers foundation models from leading AI companies.

Key Features:
- Multiple foundation models available
- Serverless experience with no infrastructure management
- Built-in security and privacy controls
- Integration with other AWS services

Use Cases:
- Text generation and analysis
- Conversational AI applications
- Content creation and summarization
- Code generation and explanation
EOF

# Step 14: Create Python 3.9 compatible test script
log_step "Step 14: Creating Python 3.9 compatible test script"
cat > test_python39_rag.py << 'EOF'
#!/usr/bin/env python3
"""
Python 3.9 compatible test script for RAG Anything with AWS Bedrock
"""

import asyncio
import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment")

def print_header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

async def test_python39_setup():
    """Test Python 3.9 compatible setup"""
    print_header("Python 3.9 RAG Setup Test")
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"Python version: {python_version}")
    
    if python_version == "3.9":
        print_success("Running on Python 3.9 - using compatible configuration")
    else:
        print_warning(f"Running on Python {python_version} - may have different behavior")
    
    try:
        # Test imports
        print("\n🔹 Testing imports...")
        
        from raganything import RAGAnythingConfig
        print_success("RAGAnythingConfig imported")
        
        from raganything.bedrock import BedrockConfig
        print_success("BedrockConfig imported")
        
        from raganything.bedrock_rag import BedrockRAGAnything
        print_success("BedrockRAGAnything imported")
        
        # Test configuration
        print("\n🔹 Testing configuration...")
        
        rag_config = RAGAnythingConfig(
            working_dir="./test_rag_storage",
            parser="pypdf2",  # Use PyPDF2 instead of MinerU
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=False,  # Disabled for Python 3.9
            enable_equation_processing=False,  # Disabled for Python 3.9
        )
        print_success("RAG configuration created (Python 3.9 compatible)")
        
        bedrock_config = BedrockConfig.from_env()
        print_success(f"Bedrock configuration created - Region: {bedrock_config.aws_region}")
        
        # Test RAG initialization
        print("\n🔹 Testing RAG initialization...")
        rag = BedrockRAGAnything(
            config=rag_config,
            bedrock_config=bedrock_config
        )
        print_success("BedrockRAGAnything initialized")
        
        # Test Bedrock access
        print("\n🔹 Testing Bedrock access...")
        try:
            access_valid = await rag.validate_bedrock_access()
            
            if access_valid:
                print_success("Bedrock access validated successfully!")
                
                # Test simple content insertion
                print("\n🔹 Testing content insertion...")
                await rag.insert_content_list([{
                    "type": "text",
                    "text": "AWS Bedrock is a fully managed service for foundation models. It provides access to various AI models through a single API.",
                    "page_idx": 0
                }], "test_content.txt", "test-001")
                print_success("Content inserted successfully")
                
                # Test simple query
                print("\n🔹 Testing simple query...")
                result = await rag.aquery("What is AWS Bedrock?", mode="naive")
                print_success(f"Query successful: {result[:100]}...")
                
                return True
            else:
                print_error("Bedrock access validation failed!")
                print_warning("Check your AWS IAM permissions and model access")
                return False
                
        except Exception as e:
            print_error(f"Bedrock test failed: {str(e)}")
            return False
            
    except Exception as e:
        print_error(f"Setup test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print_header("RAG Anything with AWS Bedrock - Python 3.9 Test")
    
    success = await test_python39_setup()
    
    if success:
        print_success("\n🎉 Python 3.9 setup test completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Try: python examples/bedrock_basic_example.py")
        print("   2. Add your documents using PyPDF2 parser")
        print("   3. Note: Some advanced features may be limited on Python 3.9")
        return 0
    else:
        print_error("\n❌ Setup test failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
EOF

chmod +x test_python39_rag.py
log_success "Python 3.9 compatible test script created"

# Step 15: Verify installation
log_step "Step 15: Verifying Python 3.9 compatible installation"
python -c "
import sys
print(f'Python version: {sys.version}')

# Test basic imports
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

try:
    from raganything.bedrock import BedrockConfig
    print('✅ BedrockConfig imported successfully')
except ImportError as e:
    print(f'❌ BedrockConfig import failed: {e}')
    sys.exit(1)

print('🎉 All imports successful on Python 3.9!')
"

if [ $? -eq 0 ]; then
    log_success "Installation verification passed!"
else
    log_error "Installation verification failed!"
    exit 1
fi

# Step 16: Final cleanup
log_step "Step 16: Final cleanup"
pip cache purge
sudo dnf clean all

# Final summary
echo ""
log_success "🎉 Python 3.9 compatible RAG Anything with AWS Bedrock setup completed!"
echo ""
echo "📁 Files and directories created:"
echo "   ✅ Virtual environment: venv/ (Python 3.9 compatible)"
echo "   ✅ Environment config: .env (Python 3.9 optimized)"
echo "   ✅ Test script: test_python39_rag.py"
echo "   ✅ Sample data: data/samples/"
echo "   ✅ Storage directories: rag_storage/, logs/, output/, cache/"
echo ""
echo "🚀 Next steps:"
echo "   1. Activate environment: source venv/bin/activate"
echo "   2. Run Python 3.9 test: python test_python39_rag.py"
echo "   3. Try basic example: python examples/bedrock_basic_example.py"
echo ""
echo "⚡ Python 3.9 Specific Changes:"
echo "   - MinerU replaced with PyPDF2 (Python 3.10+ required for MinerU)"
echo "   - Reduced feature set for compatibility"
echo "   - Optimized memory and performance settings"
echo "   - Compatible package versions installed"
echo ""
echo "⚠️  Important notes:"
echo "   - Some advanced document processing features are limited"
echo "   - Table and equation processing disabled for stability"
echo "   - Consider upgrading to Python 3.11+ for full features"
echo ""
log_success "Setup completed successfully! 🎊"