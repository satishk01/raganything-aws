# RAG Anything with AWS Bedrock - Amazon Linux 2023 Setup Guide

## 🚀 Complete Copy-Paste Setup Instructions

### Prerequisites
- Amazon Linux 2023 EC2 instance (t3.medium or larger recommended)
- IAM role attached to EC2 with Bedrock permissions
- Claude and Titan models enabled in AWS Bedrock console
- At least 8GB RAM and 20GB free disk space

### Step 1: Clone Repository and Run Deployment Script

```bash
# Clone the repository (replace with your actual repo URL)
git clone https://github.com/your-username/raganything.git
cd raganything

# Make deployment script executable and run it
chmod +x deploy_amazon_linux_2023.sh
./deploy_amazon_linux_2023.sh
```

### Step 2: Activate Environment and Test

```bash
# Activate the virtual environment
source venv/bin/activate

# Verify installation
python -c "from raganything.bedrock_rag import BedrockRAGAnything; print('✅ Installation successful')"

# Run comprehensive tests
python test_complete_rag.py
```

### Step 3: Run Examples

```bash
# Basic RAG example
python examples/bedrock_basic_example.py

# Multimodal example (if available)
python examples/bedrock_multimodal_example.py

# Performance comparison
python examples/bedrock_performance_comparison.py
```

## 🔧 Manual Installation (If Script Fails)

If the automated script fails, follow these manual steps:

### 1. System Dependencies
```bash
sudo dnf update -y
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y python3 python3-pip python3-devel git wget curl gcc gcc-c++ make cmake openssl-devel libffi-devel zlib-devel
```

### 2. Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### 3. Core Dependencies
```bash
pip install --no-cache-dir boto3>=1.34.0 botocore>=1.34.0 python-dotenv>=1.0.0
pip install --no-cache-dir asyncio-throttle>=1.0.0 tenacity>=8.0.0 aiofiles
pip install --no-cache-dir numpy pandas tqdm requests urllib3
pip install --no-cache-dir lightrag-hku huggingface_hub
```

### 4. Install RAG Anything
```bash
pip install -e . --no-cache-dir
```

### 5. Create Environment File
```bash
cat > .env << 'EOF'
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1
BEDROCK_CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_CLAUDE_HAIKU_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_TITAN_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_MAX_TOKENS=4096
BEDROCK_TEMPERATURE=0.7
WORKING_DIR=./rag_storage
OUTPUT_DIR=./output
PARSER=mineru
PARSE_METHOD=auto
LOG_LEVEL=INFO
LOG_DIR=./logs
EOF
```

### 6. Create Directories
```bash
mkdir -p logs rag_storage output data/samples
```

## 🧪 Quick Test Script

Create and run this quick test:

```bash
cat > quick_test.py << 'EOF'
import asyncio
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig
from raganything.bedrock_rag import BedrockRAGAnything

async def quick_test():
    print("🧪 Quick RAG Anything Test")
    
    # Create configurations
    rag_config = RAGAnythingConfig(working_dir="./test_storage")
    bedrock_config = BedrockConfig.from_env()
    
    # Initialize RAG
    rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
    
    # Test Bedrock access
    if await rag.validate_bedrock_access():
        print("✅ Bedrock access successful!")
        
        # Add sample content
        await rag.insert_content_list([{
            "type": "text",
            "text": "AWS Bedrock is a fully managed service for foundation models.",
            "page_idx": 0
        }], "test.txt", "test-001")
        
        # Test query
        result = await rag.aquery("What is AWS Bedrock?")
        print(f"✅ Query successful: {result[:100]}...")
        
        return True
    else:
        print("❌ Bedrock access failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    print("🎉 Test completed!" if success else "❌ Test failed!")
EOF

python quick_test.py
```

## 🔍 Troubleshooting

### Common Issues and Solutions

**1. Import Errors**
```bash
source venv/bin/activate
pip install -e . --no-cache-dir --force-reinstall
```

**2. Bedrock Access Denied**
```bash
# Check IAM role
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Check model access
aws bedrock get-foundation-model --model-identifier anthropic.claude-3-5-sonnet-20241022-v2:0 --region us-east-1
```

**3. Memory Issues**
```bash
# Check available memory
free -h

# Reduce concurrent processing in .env
echo "MAX_CONCURRENT_FILES=1" >> .env
echo "BATCH_SIZE=5" >> .env
```

**4. Disk Space Issues**
```bash
# Check disk space
df -h

# Clean up if needed
rm -rf /tmp/*
sudo dnf clean all
```

### Verification Commands

```bash
# Check Python environment
python --version
which python
pip list | grep -E "(lightrag|boto3|raganything)"

# Test imports
python -c "
from raganything.bedrock_rag import BedrockRAGAnything
from raganything.bedrock import BedrockConfig
from raganything import RAGAnythingConfig
print('✅ All imports successful')
"

# Check AWS configuration
aws configure list
aws sts get-caller-identity
```

## 📊 Performance Optimization for CPU-Only Instances

Add these to your `.env` file for better CPU performance:

```bash
# CPU optimizations
OMP_NUM_THREADS=4
MKL_NUM_THREADS=4
NUMEXPR_MAX_THREADS=4
TOKENIZERS_PARALLELISM=false

# Memory optimizations
MAX_CONCURRENT_FILES=2
BATCH_SIZE=10
CONTEXT_WINDOW=1
MAX_CONTEXT_TOKENS=2000
```

## 🎯 Next Steps

1. **Test with Your Documents**: Place your documents in a folder and use `rag.insert_folder()`
2. **Customize Models**: Edit `.env` to use different Claude or Titan models
3. **Build Applications**: Use the RAG system in your Python applications
4. **Monitor Performance**: Check logs in `logs/` directory for optimization

## 📞 Support

If you encounter issues:
1. Run the comprehensive test: `python test_complete_rag.py`
2. Check logs in `logs/` directory
3. Verify AWS permissions and model access
4. Ensure sufficient system resources

## 🏆 Success Indicators

You'll know everything is working when:
- ✅ All imports succeed without errors
- ✅ Bedrock access validation passes
- ✅ Sample queries return relevant responses
- ✅ Document processing completes successfully
- ✅ Performance metrics show reasonable response times

Happy RAG building with AWS Bedrock! 🚀