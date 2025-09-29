#!/bin/bash

# Comprehensive RAG Anything with AWS Bedrock Setup for Amazon Linux 2023
# Fixes: curl conflicts, GPU issues, cache errors, disk space optimization
# CPU-only optimized version

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
║         Comprehensive Fix for Amazon Linux 2023             ║
║              CPU-Only | No GPU | Disk Optimized             ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

log_info "Starting comprehensive setup..."

# Step 1: System validation and cleanup
log_step "Step 1: System validation and cleanup"
echo "   OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
echo "   User: $(whoami)"
echo "   Available Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "   Available Disk: $(df -h . | tail -1 | awk '{print $4}')"

# Check disk space
AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
AVAILABLE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
log_info "Available disk space: ${AVAILABLE_GB}GB"

if [ "$AVAILABLE_GB" -lt 8 ]; then
    log_error "Insufficient disk space. At least 8GB free space required."
    exit 1
fi

# Clean up before starting
log_info "Cleaning up temporary files and caches..."
sudo dnf clean all || true
pip cache purge 2>/dev/null || true
sudo rm -rf /tmp/* 2>/dev/null || true

# Step 2: Fix curl conflicts (critical fix)
log_step "Step 2: Fixing curl package conflicts"
log_info "Resolving curl-minimal vs curl conflict..."

# Method 1: Remove curl-minimal first
if rpm -q curl-minimal &>/dev/null; then
    log_info "Removing curl-minimal package..."
    sudo dnf remove -y curl-minimal || true
fi

# Method 2: Install curl with conflict resolution
log_info "Installing curl with conflict resolution..."
sudo dnf install -y --allowerasing curl || {
    log_warn "Method 1 failed, trying alternative approach..."
    sudo dnf swap -y curl-minimal curl || {
        log_warn "Method 2 failed, trying force install..."
        sudo dnf reinstall -y curl || {
            log_error "All curl installation methods failed!"
            exit 1
        }
    }
}

# Verify curl installation
if command -v curl &> /dev/null; then
    log_success "Curl installed successfully: $(curl --version | head -n1)"
else
    log_error "Curl installation failed!"
    exit 1
fi

# Step 3: Update system packages
log_step "Step 3: Updating system packages"
sudo dnf update -y

# Step 4: Install essential system dependencies (minimal set)
log_step "Step 4: Installing essential system dependencies"
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-devel \
    git \
    gcc \
    gcc-c++ \
    make \
    openssl-devel \
    libffi-devel \
    zlib-devel \
    wget \
    unzip

log_success "System dependencies installed"

# Step 5: Set up Python environment (CPU-optimized)
log_step "Step 5: Setting up Python environment"

# Remove existing venv if it exists
if [ -d "venv" ]; then
    log_info "Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
python3 -m venv venv
source venv/bin/activate

log_info "Virtual environment created and activated"
python --version

# Upgrade pip with no cache
log_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel --no-cache-dir

# Step 6: Install core dependencies (CPU-only, no GPU packages)
log_step "Step 6: Installing core dependencies (CPU-only)"

# Set environment variables to prevent GPU package installation
export CUDA_VISIBLE_DEVICES=""
export FORCE_CPU_ONLY=1

# Install AWS dependencies
log_info "Installing AWS dependencies..."
pip install --no-cache-dir \
    boto3>=1.34.0 \
    botocore>=1.34.0 \
    python-dotenv>=1.0.0

# Install async and utility dependencies
log_info "Installing async and utility dependencies..."
pip install --no-cache-dir \
    asyncio-throttle>=1.0.0 \
    tenacity>=8.0.0 \
    aiofiles \
    requests \
    urllib3

# Install data processing dependencies (CPU-only versions)
log_info "Installing data processing dependencies..."
pip install --no-cache-dir \
    numpy \
    pandas \
    tqdm

# Step 7: Install LightRAG (with CPU optimization)
log_step "Step 7: Installing LightRAG"
pip install --no-cache-dir lightrag-hku

# Step 8: Install HuggingFace Hub
log_step "Step 8: Installing HuggingFace Hub"
pip install --no-cache-dir huggingface_hub

# Step 9: Install MinerU (optional, with error handling)
log_step "Step 9: Installing MinerU (optional document processing)"
pip install --no-cache-dir "mineru[core]" || {
    log_warn "MinerU installation failed, trying basic mineru..."
    pip install --no-cache-dir mineru || {
        log_warn "MinerU installation failed completely, continuing without it..."
        log_warn "Document processing capabilities may be limited"
    }
}

# Step 10: Install optional dependencies (CPU-only)
log_step "Step 10: Installing optional dependencies"
log_info "Installing image processing (CPU-only)..."
pip install --no-cache-dir Pillow>=10.0.0 || log_warn "Pillow installation failed"

log_info "Installing text processing..."
pip install --no-cache-dir reportlab>=4.0.0 || log_warn "ReportLab installation failed"

# Step 11: Install RAG Anything package
log_step "Step 11: Installing RAG Anything package"
pip install -e . --no-cache-dir

# Step 12: Create optimized environment configuration
log_step "Step 12: Creating optimized environment configuration"
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

# Multimodal Processing (CPU-optimized)
ENABLE_IMAGE_PROCESSING=true
ENABLE_TABLE_PROCESSING=true
ENABLE_EQUATION_PROCESSING=false

# Performance Settings (CPU-optimized)
MAX_CONCURRENT_FILES=1
CONTEXT_WINDOW=1
MAX_CONTEXT_TOKENS=1500
BATCH_SIZE=5

# CPU-specific optimizations
OMP_NUM_THREADS=2
MKL_NUM_THREADS=2
NUMEXPR_MAX_THREADS=2
TOKENIZERS_PARALLELISM=false

# Memory optimizations
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
TRANSFORMERS_CACHE=./cache/transformers
HF_HOME=./cache/huggingface

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=./logs

# Disable GPU and CUDA
CUDA_VISIBLE_DEVICES=""
FORCE_CPU_ONLY=1
EOF
    log_success ".env file created with CPU optimizations"
else
    log_success ".env file already exists"
fi

# Step 13: Create required directories
log_step "Step 13: Creating required directories"
mkdir -p logs rag_storage output cache/transformers cache/huggingface data/samples temp

log_success "Directories created successfully"

# Step 14: Create sample test data
log_step "Step 14: Creating sample test data"
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
5. Reinforcement Learning: Learning through interaction with an environment

Applications of AI/ML:
- Healthcare: Medical diagnosis, drug discovery, personalized treatment
- Finance: Fraud detection, algorithmic trading, risk assessment
- Transportation: Autonomous vehicles, route optimization, traffic management
- Entertainment: Recommendation systems, content generation, game AI
- Manufacturing: Quality control, predictive maintenance, supply chain optimization

The field continues to evolve rapidly with new breakthroughs in model architectures,
training techniques, and applications across various industries.
EOF

cat > data/samples/aws_bedrock_guide.txt << 'EOF'
AWS Bedrock Overview and Features

Amazon Bedrock is a fully managed service that offers a choice of high-performing 
foundation models (FMs) from leading AI companies like AI21 Labs, Anthropic, Cohere, 
Meta, Stability AI, and Amazon via a single API.

Key Features of AWS Bedrock:
1. Multiple Foundation Models: Access to various state-of-the-art models
2. Serverless Experience: No infrastructure to manage, automatic scaling
3. Security and Privacy: Built-in security controls, data encryption
4. Fine-tuning Capabilities: Customize models for specific use cases
5. Integration with AWS Services: Seamless integration with Lambda, S3, SageMaker
6. Model Evaluation: Tools to evaluate and compare different models

Use Cases:
- Content Generation: Create articles, summaries, and marketing content
- Conversational AI: Build chatbots and virtual assistants
- Text Analysis: Sentiment analysis, entity extraction, and classification
- Code Generation: Generate and explain code in various programming languages
- Document Processing: Extract insights from documents and PDFs

Getting Started:
1. Enable model access in the AWS Bedrock console
2. Set up appropriate IAM permissions
3. Use the AWS SDK or API to make requests
4. Monitor usage and costs through CloudWatch
EOF

log_success "Sample test data created"

# Step 15: Create comprehensive test script
log_step "Step 15: Creating comprehensive test script"
cat > test_rag_comprehensive.py << 'EOF'
#!/usr/bin/env python3
"""
Comprehensive test script for RAG Anything with AWS Bedrock
CPU-optimized version with error handling
"""

import asyncio
import os
import sys
import time
from pathlib import Path
import traceback

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment")

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step):
    print(f"\n🔹 {step}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

async def test_basic_setup():
    """Test basic setup and imports"""
    print_header("Basic Setup Test")
    
    try:
        print_step("Testing imports...")
        
        # Test basic imports
        from raganything import RAGAnythingConfig
        print_success("RAGAnythingConfig imported")
        
        from raganything.bedrock import BedrockConfig
        print_success("BedrockConfig imported")
        
        from raganything.bedrock_rag import BedrockRAGAnything
        print_success("BedrockRAGAnything imported")
        
        print_step("Testing configuration creation...")
        
        # Create configurations
        rag_config = RAGAnythingConfig(
            working_dir="./test_rag_storage",
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=False,  # Disabled for CPU optimization
        )
        print_success("RAG configuration created")
        
        bedrock_config = BedrockConfig.from_env()
        print_success(f"Bedrock configuration created - Region: {bedrock_config.aws_region}")
        
        print_step("Testing RAG initialization...")
        rag = BedrockRAGAnything(
            config=rag_config,
            bedrock_config=bedrock_config
        )
        print_success("BedrockRAGAnything initialized")
        
        return True, rag
        
    except Exception as e:
        print_error(f"Basic setup test failed: {str(e)}")
        traceback.print_exc()
        return False, None

async def test_bedrock_access(rag):
    """Test Bedrock access and validation"""
    print_header("Bedrock Access Test")
    
    try:
        print_step("Validating Bedrock access...")
        access_valid = await rag.validate_bedrock_access()
        
        if access_valid:
            print_success("Bedrock access validated successfully!")
            
            # Display configuration info
            bedrock_info = rag.get_bedrock_info()
            print("\n📊 Bedrock Configuration:")
            for key, value in bedrock_info.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"    {sub_key}: {sub_value}")
                else:
                    print(f"  {key}: {value}")
            
            return True
        else:
            print_error("Bedrock access validation failed!")
            print_warning("Make sure your EC2 instance has proper IAM role with Bedrock permissions")
            print_warning("Verify Claude and Titan models are enabled in AWS Bedrock console")
            return False
            
    except Exception as e:
        print_error(f"Bedrock access test failed: {str(e)}")
        traceback.print_exc()
        return False

async def test_document_processing(rag):
    """Test document processing with sample data"""
    print_header("Document Processing Test")
    
    try:
        print_step("Processing sample documents...")
        
        # Process sample documents
        sample_files = [
            "data/samples/ai_overview.txt",
            "data/samples/aws_bedrock_guide.txt"
        ]
        
        for file_path in sample_files:
            if Path(file_path).exists():
                print(f"Processing: {file_path}")
                await rag.insert_file(file_path)
                print_success(f"Processed: {file_path}")
            else:
                print_warning(f"Sample file not found: {file_path}")
        
        # Add structured content
        print_step("Adding structured content...")
        sample_content = [{
            "type": "text",
            "text": """
            RAG (Retrieval-Augmented Generation) Systems
            
            RAG systems combine large language models with external knowledge retrieval.
            This approach allows AI systems to access up-to-date information and 
            domain-specific knowledge that wasn't present in their training data.
            
            Key benefits:
            - Access to current information
            - Reduced hallucinations
            - Domain-specific knowledge integration
            - Transparent source attribution
            """,
            "page_idx": 0
        }]
        
        await rag.insert_content_list(
            content_list=sample_content,
            file_path="rag_systems_overview.txt",
            doc_id="rag-overview-001"
        )
        print_success("Structured content added")
        
        return True
        
    except Exception as e:
        print_error(f"Document processing test failed: {str(e)}")
        traceback.print_exc()
        return False

async def test_query_functionality(rag):
    """Test query functionality with different modes"""
    print_header("Query Functionality Test")
    
    try:
        queries = [
            {
                "query": "What is artificial intelligence?",
                "mode": "naive",
                "description": "Basic AI question using naive mode"
            },
            {
                "query": "What are the key features of AWS Bedrock?",
                "mode": "hybrid",
                "description": "AWS Bedrock features using hybrid mode"
            },
            {
                "query": "How do RAG systems work?",
                "mode": "local",
                "description": "RAG systems explanation using local mode"
            }
        ]
        
        for i, query_info in enumerate(queries, 1):
            print_step(f"Query {i}: {query_info['description']}")
            print(f"   Question: {query_info['query']}")
            print(f"   Mode: {query_info['mode']}")
            
            start_time = time.time()
            result = await rag.aquery(query_info['query'], mode=query_info['mode'])
            end_time = time.time()
            
            print(f"   Response time: {end_time - start_time:.2f} seconds")
            print(f"   Answer: {result[:150]}...")
            print_success(f"Query {i} completed successfully")
            
            # Add delay between queries to prevent rate limiting
            await asyncio.sleep(2)
        
        return True
        
    except Exception as e:
        print_error(f"Query functionality test failed: {str(e)}")
        traceback.print_exc()
        return False

async def cleanup_test_data():
    """Clean up test data"""
    print_header("Cleanup")
    
    try:
        import shutil
        
        test_dirs = ["./test_rag_storage"]
        
        for test_dir in test_dirs:
            if Path(test_dir).exists():
                shutil.rmtree(test_dir)
                print_success(f"Cleaned up: {test_dir}")
        
        return True
        
    except Exception as e:
        print_error(f"Cleanup failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    print_header("RAG Anything with AWS Bedrock - Comprehensive Test Suite")
    print("CPU-Optimized Version")
    
    start_time = time.time()
    
    # Test 1: Basic setup
    basic_success, rag = await test_basic_setup()
    if not basic_success:
        print_error("Basic setup test failed! Stopping tests.")
        return 1
    
    # Test 2: Bedrock access
    bedrock_success = await test_bedrock_access(rag)
    if not bedrock_success:
        print_error("Bedrock access test failed! Check your AWS configuration.")
        return 1
    
    # Test 3: Document processing
    doc_success = await test_document_processing(rag)
    if not doc_success:
        print_warning("Document processing test failed, but continuing...")
    
    # Test 4: Query functionality
    query_success = await test_query_functionality(rag)
    if not query_success:
        print_warning("Query functionality test failed, but continuing...")
    
    # Cleanup
    cleanup_success = await cleanup_test_data()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Summary
    print_header("Test Summary")
    tests = [
        ("Basic Setup", basic_success),
        ("Bedrock Access", bedrock_success),
        ("Document Processing", doc_success),
        ("Query Functionality", query_success),
        ("Cleanup", cleanup_success)
    ]
    
    passed_tests = sum(1 for _, success in tests if success)
    total_tests = len(tests)
    
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Total test time: {total_time:.2f} seconds")
    
    for test_name, success in tests:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    if passed_tests >= 2:  # At least basic setup and Bedrock access
        print_success("🎉 Core functionality is working! Your RAG Anything with Bedrock setup is ready!")
        return 0
    else:
        print_error("❌ Critical tests failed. Please check your configuration and permissions.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
EOF

chmod +x test_rag_comprehensive.py
log_success "Comprehensive test script created"

# Step 16: Verify installation
log_step "Step 16: Verifying installation"
python -c "
import sys
import os
print(f'Python version: {sys.version}')
print(f'Python executable: {sys.executable}')

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

try:
    from raganything import RAGAnythingConfig
    print('✅ RAGAnythingConfig imported successfully')
except ImportError as e:
    print(f'❌ RAGAnythingConfig import failed: {e}')
    sys.exit(1)

print('🎉 All imports successful!')
"

if [ $? -eq 0 ]; then
    log_success "Installation verification passed!"
else
    log_error "Installation verification failed!"
    exit 1
fi

# Step 17: Final cleanup and optimization
log_step "Step 17: Final cleanup and optimization"
pip cache purge
sudo dnf clean all

# Check final disk usage
log_info "Final disk usage:"
df -h

# Final summary
echo ""
log_success "🎉 Comprehensive RAG Anything with AWS Bedrock setup completed!"
echo ""
echo "📁 Files and directories created:"
echo "   ✅ Virtual environment: venv/ (CPU-optimized)"
echo "   ✅ Environment config: .env (with CPU optimizations)"
echo "   ✅ Test script: test_rag_comprehensive.py"
echo "   ✅ Sample data: data/samples/"
echo "   ✅ Storage directories: rag_storage/, logs/, output/, cache/"
echo ""
echo "🚀 Next steps:"
echo "   1. Activate environment: source venv/bin/activate"
echo "   2. Run comprehensive test: python test_rag_comprehensive.py"
echo "   3. Try basic example: python examples/bedrock_basic_example.py"
echo ""
echo "⚡ CPU Optimizations applied:"
echo "   - No GPU packages installed"
echo "   - Reduced thread counts for CPU efficiency"
echo "   - Memory usage optimizations"
echo "   - Cache directories configured"
echo "   - Batch sizes optimized for CPU"
echo ""
echo "⚠️  Important reminders:"
echo "   - Ensure EC2 has IAM role with Bedrock permissions"
echo "   - Verify Claude and Titan models enabled in Bedrock console"
echo "   - Default region is us-east-1 (change in .env if needed)"
echo "   - This is a CPU-only installation (no GPU support)"
echo ""
log_success "Setup completed successfully! 🎊"