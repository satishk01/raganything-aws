# RAG Anything with AWS Bedrock - Complete Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying RAG Anything with AWS Bedrock integration on an EC2 instance running Amazon Linux 2023. The implementation is now complete and ready for production use.

## What's Included

The AWS Bedrock integration includes:

### ✅ Core Components (Implemented)
- **BedrockConfig**: Configuration management with environment variable support
- **BedrockAuthenticator**: IAM role-based authentication
- **BedrockLLMProvider**: Claude 3.5 Sonnet and Claude 3 Haiku integration
- **BedrockVisionProvider**: Multimodal image analysis with Claude
- **BedrockEmbeddingProvider**: Amazon Titan Text Embeddings V2
- **BedrockRAGAnything**: Main integration class extending RAGAnything
- **Error Handling**: Comprehensive retry logic and exception handling
- **Caching**: Performance optimization with TTL and LRU eviction
- **Monitoring**: CloudWatch integration and performance metrics

### ✅ Deployment Tools (Implemented)
- **CloudFormation Templates**: Complete infrastructure as code
- **Installation Scripts**: Automated setup for Amazon Linux 2023
- **Systemd Services**: Production-ready service management
- **Monitoring Setup**: CloudWatch dashboards and alarms
- **Migration Tools**: Convert from OpenAI to Bedrock
- **Validation Scripts**: Comprehensive integration testing

### ✅ Examples and Documentation (Implemented)
- **Basic Examples**: Simple usage patterns
- **Multimodal Examples**: Advanced image and table processing
- **Batch Processing**: High-throughput document processing
- **Performance Comparison**: Bedrock vs OpenAI benchmarks
- **API Reference**: Complete documentation
- **Migration Guide**: Step-by-step conversion process

## Prerequisites

### AWS Account Setup
1. **AWS Account** with billing enabled
2. **AWS Bedrock Access** in your chosen region
3. **Model Access** for required foundation models:
   - Anthropic Claude 3.5 Sonnet
   - Anthropic Claude 3 Haiku
   - Amazon Titan Text Embeddings V2

### Request Model Access
1. Go to AWS Console → Bedrock → Model access
2. Request access to the required models
3. Wait for approval (usually within minutes)

## Quick Deployment

### Option 1: Automated CloudFormation Deployment

```bash
# Clone the repository
git clone https://github.com/HKUDS/RAG-Anything.git
cd RAG-Anything

# Deploy infrastructure
chmod +x deployment/scripts/deploy.sh
./deployment/scripts/deploy.sh --key-pair YOUR_KEY_PAIR_NAME

# Wait for deployment to complete (10-15 minutes)
# SSH to the instance when ready
ssh -i YOUR_KEY_PAIR.pem ec2-user@INSTANCE_PUBLIC_IP
```

### Option 2: Manual Installation

```bash
# On your EC2 instance (Amazon Linux 2023)
curl -O https://raw.githubusercontent.com/HKUDS/RAG-Anything/main/deployment/scripts/install.sh
chmod +x install.sh
./install.sh
```

## Step-by-Step Manual Setup

### 1. Launch EC2 Instance

**Recommended Configuration:**
- **AMI**: Amazon Linux 2023 (latest)
- **Instance Type**: t3.large (minimum) or m5.large (recommended)
- **Storage**: 50GB EBS GP3
- **Security Group**: Allow SSH (22), HTTP (80), HTTPS (443)
- **IAM Role**: With Bedrock access permissions

### 2. Create IAM Role and Policy

Create IAM role with this policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:log-group:/aws/ec2/raganything*"
        }
    ]
}
```

### 3. Install Dependencies

```bash
# Update system
sudo dnf update -y

# Install system dependencies
sudo dnf install -y python3.11 python3.11-pip python3.11-devel git gcc gcc-c++ make wget curl unzip libreoffice

# Create application user
sudo useradd -m -s /bin/bash raganything
sudo mkdir -p /opt/raganything/{app,config,logs,data,cache,scripts}
sudo chown -R raganything:raganything /opt/raganything

# Set up Python environment
sudo -u raganything python3.11 -m venv /opt/raganything/venv
sudo -u raganything /opt/raganything/venv/bin/pip install --upgrade pip setuptools wheel

# Install RAG Anything with Bedrock integration
sudo -u raganything /opt/raganything/venv/bin/pip install boto3 botocore python-dotenv asyncio-throttle tenacity
sudo -u raganything /opt/raganything/venv/bin/pip install 'raganything[all]'
```

### 4. Configure Environment

Create configuration file:

```bash
sudo -u raganything tee /opt/raganything/config/.env << 'EOF'
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
WORKING_DIR=/opt/raganything/data/rag_storage
OUTPUT_DIR=/opt/raganything/data/output
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
LOG_DIR=/opt/raganything/logs
EOF

sudo -u raganything chmod 600 /opt/raganything/config/.env
```

### 5. Test Installation

```bash
# Test Bedrock integration
sudo -u raganything /opt/raganything/venv/bin/python << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/opt/raganything/app')

from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig

async def test():
    config = RAGAnythingConfig(working_dir="/tmp/test_rag")
    bedrock_config = BedrockConfig.from_env()
    
    rag = BedrockRAGAnything(config=config, bedrock_config=bedrock_config)
    
    if await rag.validate_bedrock_access():
        print("✅ Bedrock integration working!")
        
        # Test simple query
        result = await rag.aquery("What is AI?", mode="naive")
        print(f"✅ Query successful: {result[:100]}...")
        return True
    else:
        print("❌ Bedrock access validation failed")
        return False

success = asyncio.run(test())
exit(0 if success else 1)
EOF
```

## Usage Examples

### Basic Usage

```python
import asyncio
from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig

async def main():
    # Configure RAG Anything
    rag_config = RAGAnythingConfig(
        working_dir="./rag_storage",
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
    )
    
    # Configure Bedrock
    bedrock_config = BedrockConfig.from_env()
    
    # Initialize
    rag = BedrockRAGAnything(
        config=rag_config,
        bedrock_config=bedrock_config
    )
    
    # Validate access
    if await rag.validate_bedrock_access():
        print("✅ Bedrock access validated!")
    
    # Process document
    await rag.process_document_complete(
        file_path="document.pdf",
        output_dir="./output"
    )
    
    # Query
    result = await rag.aquery(
        "What are the main topics in the document?",
        mode="hybrid"
    )
    print(result)

asyncio.run(main())
```

### Multimodal Query Example

```python
# Query with external table data
result = await rag.aquery_with_multimodal(
    "Analyze this performance data",
    multimodal_content=[{
        "type": "table",
        "table_data": """Model,Accuracy,Speed
        Claude-3.5-Sonnet,95%,120ms
        Claude-3-Haiku,89%,45ms""",
        "table_caption": "Model Performance"
    }],
    mode="hybrid"
)
```

### Vision Analysis Example

```python
import base64

# Load image
with open("chart.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Query with image
result = await rag.aquery_with_multimodal(
    "What does this chart show?",
    multimodal_content=[{
        "type": "image",
        "img_path": "chart.png",
        "image_caption": ["Performance Chart"]
    }],
    mode="hybrid"
)
```

## Production Deployment

### Set up Systemd Service

```bash
sudo tee /etc/systemd/system/raganything.service << 'EOF'
[Unit]
Description=RAG Anything with AWS Bedrock
After=network.target

[Service]
Type=simple
User=raganything
Group=raganything
WorkingDirectory=/opt/raganything/app
Environment=PATH=/opt/raganything/venv/bin
EnvironmentFile=/opt/raganything/config/.env
ExecStart=/opt/raganything/venv/bin/python -m raganything.server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable raganything
sudo systemctl start raganything
```

### Set up Monitoring

```bash
# Install CloudWatch agent
sudo dnf install -y amazon-cloudwatch-agent

# Configure monitoring
sudo /opt/raganything/app/deployment/scripts/setup-monitoring.sh
```

### Set up Log Rotation

```bash
sudo tee /etc/logrotate.d/raganything << 'EOF'
/opt/raganything/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 raganything raganything
}
EOF
```

## Migration from OpenAI

If you have an existing RAG Anything installation using OpenAI:

```bash
# Run migration tool
python /opt/raganything/app/raganything/migration/migrate_to_bedrock.py \
    --source /path/to/existing/installation \
    --target /opt/raganything \
    --backup /opt/raganything/backup
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Check IAM role
   curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
   
   # Test AWS connectivity
   aws bedrock list-foundation-models --region us-east-1
   ```

2. **Model Access Issues**
   - Verify model access in Bedrock console
   - Check if models are available in your region
   - Ensure IAM policy includes correct model ARNs

3. **Memory Issues**
   ```bash
   # Add swap space
   sudo dd if=/dev/zero of=/swapfile bs=1G count=4
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

4. **Rate Limiting**
   - Reduce `MAX_CONCURRENT_FILES` in configuration
   - Use Claude Haiku for faster, less resource-intensive tasks

### Validation Script

Run comprehensive validation:

```bash
python /opt/raganything/app/scripts/validate_bedrock_integration.py --output validation_report.md
```

### Health Check

```bash
# Check service status
sudo systemctl status raganything

# View logs
sudo journalctl -u raganything -f

# Check application logs
tail -f /opt/raganything/logs/*.log

# Test Bedrock connectivity
aws bedrock list-foundation-models --region us-east-1
```

## Performance Optimization

### Instance Optimization

**Recommended Instance Types:**
- **Light usage**: t3.large (2 vCPU, 8GB RAM)
- **Medium usage**: m5.xlarge (4 vCPU, 16GB RAM)
- **Heavy usage**: m5.2xlarge (8 vCPU, 32GB RAM)

### Configuration Tuning

```bash
# Add to .env for better performance
echo "MAX_CONCURRENT_FILES=4" >> /opt/raganything/config/.env
echo "BEDROCK_RETRY_MAX_ATTEMPTS=5" >> /opt/raganything/config/.env
echo "CONTEXT_WINDOW=2" >> /opt/raganything/config/.env
echo "MAX_CONTEXT_TOKENS=4000" >> /opt/raganything/config/.env
```

## Cost Optimization

### Model Selection
- Use **Claude 3 Haiku** for faster, cheaper responses
- Use **Claude 3.5 Sonnet** for higher quality when needed
- Optimize token usage with appropriate `max_tokens` settings

### Monitoring Costs
```bash
# Set up billing alerts
aws budgets create-budget \
    --account-id YOUR_ACCOUNT_ID \
    --budget '{
        "BudgetName": "RAGAnything-Bedrock-Budget",
        "BudgetLimit": {"Amount": "100", "Unit": "USD"},
        "TimeUnit": "MONTHLY",
        "BudgetType": "COST",
        "CostFilters": {"Service": ["Amazon Bedrock"]}
    }'
```

## Security Best Practices

1. **Use IAM Roles** (not API keys)
2. **Encrypt EBS volumes**
3. **Restrict security group access**
4. **Enable VPC Flow Logs**
5. **Use CloudTrail for audit logging**
6. **Regular security updates**

## Support and Resources

### Documentation
- [API Reference](docs/BEDROCK_API_REFERENCE.md)
- [Migration Guide](raganything/migration/)
- [Examples](examples/)

### Validation and Testing
- [Integration Validator](scripts/validate_bedrock_integration.py)
- [Performance Comparison](examples/bedrock_performance_comparison.py)
- [Batch Processing Demo](examples/bedrock_batch_processing_demo.py)

### Monitoring
- CloudWatch Dashboard: `RAGAnything-Bedrock`
- Custom metrics in `RAGAnything/Bedrock` namespace
- Application logs in `/opt/raganything/logs/`

## Conclusion

Your RAG Anything with AWS Bedrock integration is now ready for production use! The implementation provides:

- ✅ **Complete AWS Bedrock Integration** with Claude and Titan models
- ✅ **Production-Ready Deployment** with monitoring and logging
- ✅ **Comprehensive Documentation** and examples
- ✅ **Migration Tools** from existing installations
- ✅ **Performance Optimization** and cost management
- ✅ **Security Best Practices** with IAM role-based authentication

For additional support or questions, refer to the troubleshooting section or check the comprehensive validation script to ensure everything is working correctly.

**Next Steps:**
1. Test with your documents
2. Configure monitoring and alerting
3. Optimize for your specific use case
4. Scale based on your requirements

🎉 **Congratulations! Your RAG Anything with AWS Bedrock is ready to use!**