# RAG Anything with AWS Bedrock - Final Deployment Instructions

## 🚀 Complete Implementation Summary

I have successfully implemented the complete AWS Bedrock integration for RAG Anything. Here's what has been created:

### ✅ Core Implementation (100% Complete)
- **AWS Bedrock Configuration** (`raganything/bedrock/config.py`)
- **Authentication Handler** (`raganything/bedrock/auth.py`)
- **LLM Provider** (`raganything/bedrock/llm_provider.py`) - Claude 3.5 Sonnet & Haiku
- **Vision Provider** (`raganything/bedrock/vision_provider.py`) - Multimodal image analysis
- **Embedding Provider** (`raganything/bedrock/embedding_provider.py`) - Titan embeddings
- **Main Integration Class** (`raganything/bedrock_rag.py`)
- **Error Handling** (`raganything/bedrock/exceptions.py`, `raganything/bedrock/retry_handler.py`)
- **Performance Optimization** (`raganything/bedrock/cache.py`)
- **Monitoring & Logging** (`raganything/bedrock/monitoring.py`)

### ✅ Deployment Infrastructure (100% Complete)
- **CloudFormation Template** (`deployment/cloudformation/bedrock-rag-infrastructure.yaml`)
- **Installation Scripts** (`deployment/scripts/install.sh`, `deployment/scripts/deploy.sh`)
- **Systemd Service** (`deployment/systemd/raganything.service`)
- **Environment Configuration** (`deployment/config/environment.template`)
- **Monitoring Setup** (`deployment/scripts/setup-monitoring.sh`)

### ✅ Examples & Documentation (100% Complete)
- **Basic Example** (`examples/bedrock_basic_example.py`)
- **Multimodal Example** (`examples/bedrock_multimodal_example.py`)
- **Batch Processing Demo** (`examples/bedrock_batch_processing_demo.py`)
- **Performance Comparison** (`examples/bedrock_performance_comparison.py`)
- **API Reference** (`docs/BEDROCK_API_REFERENCE.md`)

### ✅ Migration & Validation Tools (100% Complete)
- **Migration Tool** (`raganything/migration/migrate_to_bedrock.py`)
- **Compatibility Checker** (`raganything/migration/compatibility_checker.py`)
- **Integration Validator** (`scripts/validate_bedrock_integration.py`)

## 🎯 Quick Start - Deploy to AWS EC2

### Step 1: Prepare AWS Environment

1. **Request Bedrock Model Access**
   ```bash
   # Go to AWS Console → Bedrock → Model access
   # Request access to:
   # - anthropic.claude-3-5-sonnet-20241022-v2:0
   # - anthropic.claude-3-haiku-20240307-v1:0  
   # - amazon.titan-embed-text-v2:0
   ```

2. **Create EC2 Key Pair** (if you don't have one)
   ```bash
   aws ec2 create-key-pair --key-name raganything-key --query 'KeyMaterial' --output text > raganything-key.pem
   chmod 400 raganything-key.pem
   ```

### Step 2: Deploy Infrastructure

```bash
# Clone the repository
git clone https://github.com/HKUDS/RAG-Anything.git
cd RAG-Anything

# Deploy using CloudFormation
chmod +x deployment/scripts/deploy.sh
./deployment/scripts/deploy.sh --key-pair raganything-key --environment production

# Wait for deployment (10-15 minutes)
# Note the public IP address from the output
```

### Step 3: Connect and Verify

```bash
# SSH to your instance
ssh -i raganything-key.pem ec2-user@YOUR_INSTANCE_PUBLIC_IP

# Check installation status
sudo tail -f /var/log/cloud-init-output.log

# Test the installation
sudo -u raganything /opt/raganything/scripts/test_bedrock.py

# Start the service
sudo systemctl start raganything
sudo systemctl status raganything
```

### Step 4: Test with Your Documents

```bash
# Switch to application user
sudo su - raganything
source /opt/raganything/venv/bin/activate

# Test with a sample document
python << 'EOF'
import asyncio
from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig

async def test_document():
    # Configure
    rag_config = RAGAnythingConfig(
        working_dir="/opt/raganything/data/rag_storage"
    )
    bedrock_config = BedrockConfig.from_env()
    
    # Initialize
    rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
    
    # Add sample content
    content = [{
        "type": "text",
        "text": "This is a test document about artificial intelligence and machine learning.",
        "page_idx": 0
    }]
    
    await rag.insert_content_list(
        content_list=content,
        file_path="test.txt",
        doc_id="test-001"
    )
    
    # Query
    result = await rag.aquery("What is this document about?", mode="hybrid")
    print(f"Result: {result}")

asyncio.run(test_document())
EOF
```

## 🔧 Configuration Reference

### Environment Variables

Create `/opt/raganything/config/.env`:

```bash
# AWS Configuration
AWS_REGION=us-east-1

# Bedrock Models
BEDROCK_CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_CLAUDE_HAIKU_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_TITAN_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0

# Model Parameters
BEDROCK_MAX_TOKENS=4096
BEDROCK_TEMPERATURE=0.7

# RAG Configuration
WORKING_DIR=/opt/raganything/data/rag_storage
OUTPUT_DIR=/opt/raganything/data/output
PARSER=mineru
PARSE_METHOD=auto

# Multimodal Processing
ENABLE_IMAGE_PROCESSING=true
ENABLE_TABLE_PROCESSING=true
ENABLE_EQUATION_PROCESSING=true

# Performance
MAX_CONCURRENT_FILES=2
CONTEXT_WINDOW=1
MAX_CONTEXT_TOKENS=2000

# Logging
LOG_LEVEL=INFO
LOG_DIR=/opt/raganything/logs
```

### Python Usage

```python
import asyncio
from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig

async def main():
    # Configure
    rag_config = RAGAnythingConfig(
        working_dir="./rag_storage",
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
    )
    
    bedrock_config = BedrockConfig.from_env()
    
    # Initialize
    rag = BedrockRAGAnything(
        config=rag_config,
        bedrock_config=bedrock_config
    )
    
    # Validate
    if await rag.validate_bedrock_access():
        print("✅ Ready to use!")
    
    # Process document
    await rag.process_document_complete(
        file_path="your_document.pdf",
        output_dir="./output"
    )
    
    # Query
    result = await rag.aquery(
        "What are the main topics?",
        mode="hybrid"
    )
    print(result)

# Run
asyncio.run(main())
```

## 🎯 Key Features Available

### 1. **Text Generation**
- Claude 3.5 Sonnet for high-quality responses
- Claude 3 Haiku for fast responses
- Automatic retry and error handling
- Batch processing support

### 2. **Vision Analysis**
- Multimodal image analysis with Claude
- Support for multiple image formats
- Automatic image optimization
- VLM-enhanced queries

### 3. **Embeddings**
- Amazon Titan Text Embeddings V2
- Batch embedding generation
- 1024-dimensional vectors
- Optimized for retrieval

### 4. **Document Processing**
- PDF, Office documents, images
- Multimodal content extraction
- Table and equation processing
- Batch folder processing

### 5. **Query Capabilities**
- Pure text queries
- Multimodal queries with external content
- VLM-enhanced queries
- Multiple query modes (hybrid, local, global, naive)

## 🔍 Validation & Testing

Run the comprehensive validation:

```bash
python /opt/raganything/app/scripts/validate_bedrock_integration.py
```

This will test:
- ✅ Configuration validation
- ✅ AWS authentication
- ✅ LLM provider functionality
- ✅ Vision provider functionality
- ✅ Embedding provider functionality
- ✅ End-to-end integration
- ✅ Performance benchmarks
- ✅ Error handling

## 🚨 Troubleshooting

### Common Issues & Solutions

1. **"AccessDeniedException"**
   - Check IAM role has Bedrock permissions
   - Verify model access is granted in Bedrock console

2. **"ValidationException"**
   - Check model IDs are correct for your region
   - Verify request format matches model requirements

3. **"ThrottlingException"**
   - Reduce concurrent requests
   - Implement longer delays between calls

4. **Import Errors**
   - Ensure all dependencies are installed: `pip install 'raganything[bedrock]'`
   - Check Python path includes the application directory

5. **Memory Issues**
   - Add swap space
   - Use smaller context windows
   - Process fewer files concurrently

### Debug Commands

```bash
# Check service status
sudo systemctl status raganything

# View real-time logs
sudo journalctl -u raganything -f

# Test AWS connectivity
aws bedrock list-foundation-models --region us-east-1

# Check disk space
df -h /opt/raganything

# Monitor resource usage
htop
```

## 🎉 You're Ready!

Your RAG Anything with AWS Bedrock integration is now fully implemented and ready for production use. The system provides:

- **Complete AWS Integration** with no external API dependencies
- **Production-Ready Deployment** on Amazon Linux 2023
- **Comprehensive Monitoring** with CloudWatch integration
- **Security Best Practices** with IAM role-based authentication
- **High Performance** with caching and optimization
- **Full Multimodal Support** for text, images, tables, and equations

**Start using it now with your documents and enjoy the power of AWS Bedrock with RAG Anything!** 🚀