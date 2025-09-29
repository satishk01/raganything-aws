# Complete RAG Anything AWS Bedrock Deployment Guide

## 🚀 Step-by-Step Deployment on Amazon Linux 2023 EC2

This guide provides detailed copy-paste commands to deploy RAG Anything with AWS Bedrock integration on Amazon Linux 2023 EC2 instance. All files are available in the GitHub repository: https://github.com/satishk01/raganything-aws.git

## 📋 Prerequisites

### 1. AWS Account Setup
- AWS account with billing enabled
- Access to AWS Bedrock service
- EC2 key pair created
- IAM permissions for EC2, Bedrock, and CloudFormation

### 2. Request Bedrock Model Access
Before starting, request access to required models in AWS Bedrock console:

1. Go to AWS Console → Bedrock → Model access
2. Request access to:
   - **anthropic.claude-3-5-sonnet-20241022-v2:0**
   - **anthropic.claude-3-haiku-20240307-v1:0**
   - **amazon.titan-embed-text-v2:0**
3. Wait for approval (usually within minutes)

## 🎯 Option 1: Automated CloudFormation Deployment (Recommended)

### Step 1: Launch EC2 Instance with CloudFormation

```bash
# Clone the repository
git clone https://github.com/satishk01/raganything-aws.git
cd raganything-aws

# Make deployment script executable
chmod +x deployment/scripts/deploy.sh

# Deploy with your key pair (replace YOUR_KEY_PAIR_NAME)
./deployment/scripts/deploy.sh --key-pair YOUR_KEY_PAIR_NAME --region us-east-1

# For production deployment with larger instance
./deployment/scripts/deploy.sh \
    --key-pair YOUR_KEY_PAIR_NAME \
    --instance-type m5.large \
    --environment production \
    --region us-east-1
```

### Step 2: Connect to Your Instance

After deployment completes, you'll see output like:
```
Instance ID: i-1234567890abcdef0
Public IP: 54.123.45.67
SSH Command: ssh -i YOUR_KEY_PAIR.pem ec2-user@54.123.45.67
```

Connect to your instance:
```bash
# Replace with your actual key file and IP
ssh -i YOUR_KEY_PAIR.pem ec2-user@54.123.45.67
```

### Step 3: Monitor Installation Progress

```bash
# Check cloud-init installation progress
sudo tail -f /var/log/cloud-init-output.log

# Wait for installation to complete (10-15 minutes)
# Look for "Installation complete! 🎉" message
```

### Step 4: Test the Installation

```bash
# Test Bedrock integration
sudo -u raganything /opt/raganything/scripts/test_bedrock.py

# Check service status
sudo systemctl status raganything

# Start the service if not running
sudo systemctl start raganything
```

## 🛠️ Option 2: Manual Installation (Step-by-Step)

If you prefer manual installation or the automated deployment fails, follow these steps:

### Step 1: Launch EC2 Instance Manually

1. **Launch EC2 Instance**:
   - AMI: Amazon Linux 2023 (latest)
   - Instance Type: t3.large (minimum) or m5.large (recommended)
   - Storage: 50GB EBS GP3
   - Security Group: Allow SSH (22), HTTP (80), HTTPS (443)
   - Key Pair: Your existing key pair

2. **Attach IAM Role** with this policy:

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

### Step 2: Connect and Install

```bash
# Connect to your instance
ssh -i YOUR_KEY_PAIR.pem ec2-user@YOUR_INSTANCE_IP

# Clone the repository
git clone https://github.com/satishk01/raganything-aws.git
cd raganything-aws

# Make installation script executable
chmod +x deployment/scripts/install.sh

# Run installation script
./deployment/scripts/install.sh
```

### Step 3: Configure Environment

```bash
# Edit configuration file
sudo -u raganything nano /opt/raganything/config/.env

# Update these key settings:
# AWS_REGION=us-east-1  # Your preferred region
# BEDROCK_CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
# BEDROCK_CLAUDE_HAIKU_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
# BEDROCK_TITAN_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
```

### Step 4: Test Installation

```bash
# Test Bedrock integration
sudo -u raganything /opt/raganything/scripts/test_bedrock.py

# If test passes, start the service
sudo systemctl start raganything
sudo systemctl enable raganything

# Check service status
sudo systemctl status raganything
```

## 🧪 Testing All Functionality

### Test 1: Basic Bedrock Connection

```bash
# Run basic connection test
sudo -u raganything /opt/raganything/scripts/test_bedrock.py
```

Expected output:
```
🚀 Testing RAG Anything with AWS Bedrock
==================================================
✅ RAG Anything initialized successfully
🔍 Validating Bedrock access...
✅ Bedrock access validation successful
🔍 Testing basic text query...
✅ Query successful: Artificial intelligence (AI) refers to the simulation of human intelligence...
🎉 All tests passed!
```

### Test 2: Document Processing

```bash
# Switch to raganything user
sudo su - raganything
source /opt/raganything/venv/bin/activate

# Create test document
cat > /tmp/test_document.txt << 'EOF'
# Test Document

This is a test document for RAG Anything with AWS Bedrock.

## Key Features
- Document processing with MinerU
- Claude 3.5 Sonnet for high-quality responses
- Amazon Titan embeddings for retrieval
- Multimodal support for images and tables

## Conclusion
This system provides enterprise-grade RAG capabilities using AWS Bedrock.
EOF

# Test document processing
python << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/opt/raganything/app')

from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig

async def test_document_processing():
    # Configure
    rag_config = RAGAnythingConfig(
        working_dir="/opt/raganything/data/rag_storage"
    )
    bedrock_config = BedrockConfig.from_env()
    
    # Initialize
    rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
    
    # Process document
    print("📄 Processing test document...")
    await rag.process_document_complete("/tmp/test_document.txt")
    print("✅ Document processed successfully!")
    
    # Query document
    print("🔍 Querying document...")
    result = await rag.aquery("What are the key features mentioned?", mode="hybrid")
    print(f"📝 Answer: {result}")
    
    return True

asyncio.run(test_document_processing())
EOF

# Exit back to ec2-user
exit
```

### Test 3: Multimodal Processing

```bash
# Test multimodal capabilities
sudo -u raganything python << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/opt/raganything/app')

from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig

async def test_multimodal():
    rag_config = RAGAnythingConfig(working_dir="/opt/raganything/data/rag_storage")
    bedrock_config = BedrockConfig.from_env()
    rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
    
    # Test with table data
    print("📊 Testing multimodal query with table...")
    result = await rag.aquery_with_multimodal(
        "Analyze this performance data",
        multimodal_content=[{
            "type": "table",
            "table_data": """Model,Accuracy,Speed,Memory
Claude-3.5-Sonnet,95.2%,120ms,2GB
Claude-3-Haiku,89.1%,45ms,1GB
GPT-4,93.8%,200ms,3GB""",
            "table_caption": "AI Model Performance Comparison"
        }],
        mode="hybrid"
    )
    print(f"📝 Analysis: {result[:200]}...")
    print("✅ Multimodal test successful!")

asyncio.run(test_multimodal())
EOF
```

### Test 4: Batch Processing

```bash
# Create multiple test documents
sudo -u raganything mkdir -p /opt/raganything/data/test_docs

sudo -u raganything cat > /opt/raganything/data/test_docs/doc1.txt << 'EOF'
# Document 1: Machine Learning Basics

Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.

## Types of Machine Learning
- Supervised Learning
- Unsupervised Learning  
- Reinforcement Learning
EOF

sudo -u raganything cat > /opt/raganything/data/test_docs/doc2.txt << 'EOF'
# Document 2: Deep Learning

Deep learning uses neural networks with multiple layers to model complex patterns in data.

## Applications
- Computer Vision
- Natural Language Processing
- Speech Recognition
EOF

# Test batch processing
sudo -u raganything python << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/opt/raganything/app')

from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig

async def test_batch_processing():
    rag_config = RAGAnythingConfig(working_dir="/opt/raganything/data/rag_storage")
    bedrock_config = BedrockConfig.from_env()
    rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
    
    # Process multiple documents
    print("📁 Processing multiple documents...")
    await rag.process_folder_complete(
        folder_path="/opt/raganything/data/test_docs",
        output_dir="/opt/raganything/data/output",
        file_extensions=[".txt"],
        recursive=False
    )
    print("✅ Batch processing completed!")
    
    # Query across all documents
    result = await rag.aquery(
        "What are the main differences between machine learning and deep learning?",
        mode="global"
    )
    print(f"📝 Answer: {result[:300]}...")

asyncio.run(test_batch_processing())
EOF
```

### Test 5: Performance Validation

```bash
# Run comprehensive validation
sudo -u raganything python /opt/raganything/app/scripts/validate_bedrock_integration.py

# Run performance comparison
sudo -u raganything python /opt/raganything/app/examples/bedrock_performance_comparison.py
```

## 🔧 Service Management

### Start/Stop/Restart Service

```bash
# Start service
sudo systemctl start raganything

# Stop service
sudo systemctl stop raganything

# Restart service
sudo systemctl restart raganything

# Check status
sudo systemctl status raganything

# Enable auto-start on boot
sudo systemctl enable raganything

# View logs
sudo journalctl -u raganything -f
```

### Health Monitoring

```bash
# Run health check
/opt/raganything/scripts/health_check.sh

# Check application logs
sudo tail -f /opt/raganything/logs/*.log

# Monitor system resources
htop

# Check disk usage
df -h /opt/raganything
```

## 📊 Usage Examples

### Example 1: Process PDF Document

```bash
# Upload a PDF to the instance (from your local machine)
scp -i YOUR_KEY_PAIR.pem document.pdf ec2-user@YOUR_INSTANCE_IP:/tmp/

# Process the PDF
sudo -u raganything python << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/opt/raganything/app')

from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig

async def process_pdf():
    rag_config = RAGAnythingConfig(
        working_dir="/opt/raganything/data/rag_storage",
        enable_image_processing=True,
        enable_table_processing=True
    )
    bedrock_config = BedrockConfig.from_env()
    rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
    
    # Process PDF
    await rag.process_document_complete("/tmp/document.pdf")
    
    # Query the document
    result = await rag.aquery("Summarize the main points of this document", mode="hybrid")
    print(result)

asyncio.run(process_pdf())
EOF
```

### Example 2: Interactive Query Session

```bash
# Start interactive Python session
sudo -u raganything python << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/opt/raganything/app')

from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig

async def interactive_session():
    rag_config = RAGAnythingConfig(working_dir="/opt/raganything/data/rag_storage")
    bedrock_config = BedrockConfig.from_env()
    rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
    
    queries = [
        "What documents have been processed?",
        "What are the main topics across all documents?",
        "Find information about machine learning algorithms",
        "What images or tables are mentioned in the documents?"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: {query}")
        result = await rag.aquery(query, mode="hybrid")
        print(f"📝 Answer: {result[:200]}...")

asyncio.run(interactive_session())
EOF
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Bedrock Access Denied

```bash
# Check IAM role permissions
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Check model access in Bedrock console
aws bedrock get-foundation-model --model-identifier anthropic.claude-3-5-sonnet-20241022-v2:0 --region us-east-1
```

#### 2. Service Won't Start

```bash
# Check service logs
sudo journalctl -u raganything -n 50

# Check configuration
sudo -u raganything cat /opt/raganything/config/.env

# Test configuration
sudo -u raganything python -c "
import sys
sys.path.insert(0, '/opt/raganything/app')
from raganything.bedrock import BedrockConfig
config = BedrockConfig.from_env()
print('Configuration loaded successfully')
"
```

#### 3. Memory Issues

```bash
# Check memory usage
free -h

# Add swap space if needed
sudo dd if=/dev/zero of=/swapfile bs=1G count=4
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 4. Installation Issues

```bash
# Reinstall dependencies
sudo -u raganything /opt/raganything/venv/bin/pip install --force-reinstall 'raganything[all]'

# Check Python path
sudo -u raganything python -c "import sys; print('\n'.join(sys.path))"

# Reinstall from source
cd /opt/raganything/app
sudo -u raganything /opt/raganything/venv/bin/pip install -e .
```

## 🔒 Security Best Practices

### 1. Update Security Group

```bash
# Restrict SSH access to your IP only
aws ec2 authorize-security-group-ingress \
    --group-id YOUR_SECURITY_GROUP_ID \
    --protocol tcp \
    --port 22 \
    --cidr YOUR_IP/32

# Remove default SSH rule
aws ec2 revoke-security-group-ingress \
    --group-id YOUR_SECURITY_GROUP_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0
```

### 2. Enable CloudTrail Logging

```bash
# Create CloudTrail for audit logging
aws cloudtrail create-trail \
    --name raganything-audit \
    --s3-bucket-name your-cloudtrail-bucket
```

### 3. Regular Updates

```bash
# Update system packages
sudo dnf update -y

# Update Python packages
sudo -u raganything /opt/raganything/venv/bin/pip install --upgrade pip
sudo -u raganything /opt/raganything/venv/bin/pip list --outdated
```

## 📈 Performance Optimization

### 1. Instance Optimization

```bash
# For heavy workloads, upgrade instance type
# Stop instance, change type to m5.xlarge or m5.2xlarge

# Optimize network settings
echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 2. Configuration Tuning

```bash
# Edit configuration for better performance
sudo -u raganything nano /opt/raganything/config/.env

# Update these settings:
# MAX_CONCURRENT_FILES=4
# BEDROCK_RETRY_MAX_ATTEMPTS=5
# CONTEXT_WINDOW=2
# MAX_CONTEXT_TOKENS=4000
# ENABLE_LLM_CACHE=true
```

## 🎉 Success Verification

If all tests pass, you should see:

1. ✅ **Bedrock Connection**: Models accessible and responding
2. ✅ **Document Processing**: Files parsed and indexed successfully  
3. ✅ **Multimodal Support**: Tables, images, and equations processed
4. ✅ **Query System**: Accurate responses from processed documents
5. ✅ **Service Running**: Systemd service active and stable
6. ✅ **Monitoring**: Health checks and logs working

## 📞 Support

If you encounter issues:

1. **Check Logs**: `sudo journalctl -u raganything -f`
2. **Run Health Check**: `/opt/raganything/scripts/health_check.sh`
3. **Validate Configuration**: Run test scripts
4. **Review Documentation**: Check API reference and troubleshooting guides

## 🎯 Next Steps

After successful deployment:

1. **Upload Your Documents**: Process your actual documents
2. **Customize Configuration**: Tune settings for your use case
3. **Set Up Monitoring**: Configure CloudWatch dashboards
4. **Scale Infrastructure**: Add load balancing if needed
5. **Backup Data**: Set up regular backups of your RAG storage

---

**🎉 Congratulations! Your RAG Anything with AWS Bedrock is now fully deployed and ready for production use!** 