# RAG Anything with AWS Bedrock - Complete Deployment and Usage Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [AWS Setup](#aws-setup)
4. [EC2 Instance Setup](#ec2-instance-setup)
5. [Application Installation](#application-installation)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Troubleshooting](#troubleshooting)
9. [Performance Optimization](#performance-optimization)
10. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Overview

This guide provides comprehensive instructions for deploying RAG Anything with AWS Bedrock integration on an EC2 instance running Amazon Linux 2023. The integration replaces OpenAI and Ollama dependencies with AWS-native services:

- **LLM Models**: Anthropic Claude 3.5 Sonnet and Claude 3 Haiku
- **Vision Models**: Anthropic Claude 3.5 Sonnet (multimodal)
- **Embedding Models**: Amazon Titan Text Embeddings V2
- **Authentication**: IAM roles and policies
- **Deployment**: EC2 with Amazon Linux 2023

### Key Benefits
- **Privacy**: All processing happens within your AWS account
- **Performance**: Direct access to AWS Bedrock models
- **Security**: IAM-based authentication with minimal permissions
- **Scalability**: Easy to scale with AWS infrastructure
- **Cost Control**: Pay only for what you use

## Prerequisites

### AWS Account Requirements
- Active AWS account with billing enabled
- Access to AWS Bedrock service in your region
- Permissions to create EC2 instances, IAM roles, and security groups
- AWS CLI configured (optional but recommended)

### Model Access
Before starting, ensure you have access to the required Bedrock models:

1. **Navigate to AWS Bedrock Console**
   - Go to AWS Console → Bedrock → Model access
   - Request access to the following models:
     - Anthropic Claude 3.5 Sonnet
     - Anthropic Claude 3 Haiku  
     - Amazon Titan Text Embeddings V2

2. **Wait for Approval**
   - Model access requests are usually approved within minutes
   - You'll receive email notifications when approved

### Supported AWS Regions
AWS Bedrock is available in the following regions:
- `us-east-1` (N. Virginia) - **Recommended**
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)
- `ap-southeast-1` (Singapore)
- `ap-northeast-1` (Tokyo)

## AWS Setup

### 1. Create IAM Role for EC2

Create an IAM role that your EC2 instance will use to access Bedrock:

**Step 1: Create the Role**
```bash
# Using AWS CLI
aws iam create-role \
    --role-name RAGAnything-BedrockRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'
```

**Step 2: Create and Attach Policy**
```bash
# Create policy document
cat > bedrock-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
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
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel"
            ],
            "Resource": "*"
        }
    ]
}
EOF

# Create and attach policy
aws iam create-policy \
    --policy-name RAGAnything-BedrockPolicy \
    --policy-document file://bedrock-policy.json

aws iam attach-role-policy \
    --role-name RAGAnything-BedrockRole \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/RAGAnything-BedrockPolicy
```

**Step 3: Create Instance Profile**
```bash
aws iam create-instance-profile \
    --instance-profile-name RAGAnything-InstanceProfile

aws iam add-role-to-instance-profile \
    --instance-profile-name RAGAnything-InstanceProfile \
    --role-name RAGAnything-BedrockRole
```

### 2. Create Security Group

```bash
# Create security group
aws ec2 create-security-group \
    --group-name RAGAnything-SG \
    --description "Security group for RAG Anything application"

# Allow SSH access (replace YOUR_IP with your IP address)
aws ec2 authorize-security-group-ingress \
    --group-name RAGAnything-SG \
    --protocol tcp \
    --port 22 \
    --cidr YOUR_IP/32

# Allow HTTP access (if you plan to run a web interface)
aws ec2 authorize-security-group-ingress \
    --group-name RAGAnything-SG \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

# Allow HTTPS access
aws ec2 authorize-security-group-ingress \
    --group-name RAGAnything-SG \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0
```

## EC2 Instance Setup

### 1. Launch EC2 Instance

**Recommended Instance Specifications:**
- **Instance Type**: `t3.large` (minimum) or `m5.large` (recommended)
- **AMI**: Amazon Linux 2023 (latest)
- **Storage**: 50GB EBS GP3 volume
- **Security Group**: RAGAnything-SG (created above)
- **IAM Role**: RAGAnything-InstanceProfile (created above)

**Launch via AWS CLI:**
```bash
# Get the latest Amazon Linux 2023 AMI ID
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-*" "Name=architecture,Values=x86_64" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)

# Launch instance
aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type t3.large \
    --key-name YOUR_KEY_PAIR \
    --security-groups RAGAnything-SG \
    --iam-instance-profile Name=RAGAnything-InstanceProfile \
    --block-device-mappings '[{
        "DeviceName": "/dev/xvda",
        "Ebs": {
            "VolumeSize": 50,
            "VolumeType": "gp3",
            "DeleteOnTermination": true
        }
    }]' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=RAGAnything-Bedrock}]'
```

### 2. Connect to Instance

```bash
# Get instance public IP
INSTANCE_IP=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=RAGAnything-Bedrock" "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

# Connect via SSH
ssh -i YOUR_KEY_PAIR.pem ec2-user@$INSTANCE_IP
```

## Application Installation

### 1. System Setup

```bash
# Update system
sudo dnf update -y

# Install system dependencies
sudo dnf install -y \
    python3.11 \
    python3.11-pip \
    python3.11-devel \
    git \
    gcc \
    gcc-c++ \
    make \
    wget \
    curl \
    unzip

# Install LibreOffice for office document processing
sudo dnf install -y libreoffice

# Create application user
sudo useradd -m -s /bin/bash raganything
sudo mkdir -p /opt/raganything
sudo chown raganything:raganything /opt/raganything
```

### 2. Python Environment Setup

```bash
# Switch to application user
sudo su - raganything

# Create Python virtual environment
python3.11 -m venv /opt/raganything/venv
source /opt/raganything/venv/bin/activate

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel

# Install AWS SDK
pip install boto3 botocore

# Install RAG Anything with all dependencies
pip install 'raganything[all]'

# Install additional dependencies for AWS integration
pip install python-dotenv asyncio-throttle tenacity
```

### 3. Download and Setup Application Code

```bash
# Create application directory structure
mkdir -p /opt/raganything/{app,config,logs,data,cache,scripts}

# Clone the enhanced RAG Anything with Bedrock integration
# (This will be available after implementation)
cd /opt/raganything/app
git clone https://github.com/HKUDS/RAG-Anything.git .

# Install in development mode for easy updates
pip install -e .
```

## Configuration

### 1. Environment Configuration

Create the main configuration file:

```bash
# Create environment file
cat > /opt/raganything/config/.env << 'EOF'
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
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
VERBOSE=false
EOF

# Set proper permissions
chmod 600 /opt/raganything/config/.env
```

### 2. Create Systemd Service

```bash
# Exit from raganything user
exit

# Create systemd service file
sudo cat > /etc/systemd/system/raganything.service << 'EOF'
[Unit]
Description=RAG Anything with AWS Bedrock
After=network.target
Wants=network.target

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
StandardOutput=journal
StandardError=journal
SyslogIdentifier=raganything

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/raganything

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable raganything
```

### 3. Create Log Rotation

```bash
sudo cat > /etc/logrotate.d/raganything << 'EOF'
/opt/raganything/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 raganything raganything
    postrotate
        systemctl reload raganything
    endscript
}
EOF
```

## Usage Examples

### 1. Basic Setup and Testing

Create a test script to verify the installation:

```python
# /opt/raganything/scripts/test_bedrock.py
#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/opt/raganything/app')

from raganything import BedrockRAGAnything, RAGAnythingConfig, BedrockConfig

async def test_bedrock_integration():
    """Test basic Bedrock integration"""
    
    print("🚀 Testing RAG Anything with AWS Bedrock")
    print("=" * 50)
    
    try:
        # Create configurations
        rag_config = RAGAnythingConfig(
            working_dir="/opt/raganything/data/rag_storage",
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )
        
        bedrock_config = BedrockConfig.from_env()
        
        # Initialize RAG Anything with Bedrock
        rag = BedrockRAGAnything(
            config=rag_config,
            bedrock_config=bedrock_config
        )
        
        print("✅ RAG Anything initialized successfully")
        
        # Test basic text query
        print("\n🔍 Testing basic text query...")
        result = await rag.aquery(
            "What is artificial intelligence?",
            mode="naive"  # Use naive mode for simple test
        )
        print(f"✅ Query successful: {result[:100]}...")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bedrock_integration())
    sys.exit(0 if success else 1)
```

Run the test:
```bash
sudo su - raganything
source /opt/raganything/venv/bin/activate
cd /opt/raganything/scripts
python test_bedrock.py
```

### 2. Document Processing Example

```python
# /opt/raganything/scripts/process_document.py
#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/opt/raganything/app')

from raganything import BedrockRAGAnything, RAGAnythingConfig, BedrockConfig

async def process_document_example(file_path: str):
    """Process a document with Bedrock integration"""
    
    print(f"📄 Processing document: {file_path}")
    
    # Initialize RAG Anything
    rag_config = RAGAnythingConfig(
        working_dir="/opt/raganything/data/rag_storage",
        parser="mineru",
        parse_method="auto",
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
    )
    
    bedrock_config = BedrockConfig.from_env()
    
    rag = BedrockRAGAnything(
        config=rag_config,
        bedrock_config=bedrock_config
    )
    
    try:
        # Process document
        await rag.process_document_complete(
            file_path=file_path,
            output_dir="/opt/raganything/data/output",
            parse_method="auto"
        )
        
        print("✅ Document processing completed!")
        
        # Example queries
        queries = [
            "What is the main topic of this document?",
            "Summarize the key findings or conclusions.",
            "What images or tables are mentioned in the document?"
        ]
        
        for query in queries:
            print(f"\n🔍 Query: {query}")
            result = await rag.aquery(query, mode="hybrid")
            print(f"📝 Answer: {result[:200]}...")
            
    except Exception as e:
        print(f"❌ Error processing document: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_document.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    asyncio.run(process_document_example(file_path))
```

### 3. Multimodal Query Example

```python
# /opt/raganything/scripts/multimodal_query.py
#!/usr/bin/env python3

import asyncio
import sys

sys.path.insert(0, '/opt/raganything/app')

from raganything import BedrockRAGAnything, RAGAnythingConfig, BedrockConfig

async def multimodal_query_example():
    """Demonstrate multimodal querying with Bedrock"""
    
    # Initialize RAG Anything
    rag_config = RAGAnythingConfig(
        working_dir="/opt/raganything/data/rag_storage",
    )
    
    bedrock_config = BedrockConfig.from_env()
    
    rag = BedrockRAGAnything(
        config=rag_config,
        bedrock_config=bedrock_config
    )
    
    # Example 1: Query with table data
    print("📊 Multimodal Query with Table Data")
    table_result = await rag.aquery_with_multimodal(
        "Analyze this performance data and compare it with industry standards",
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
    print(f"📝 Result: {table_result[:300]}...")
    
    # Example 2: Query with equation
    print("\n🧮 Multimodal Query with Equation")
    equation_result = await rag.aquery_with_multimodal(
        "Explain this formula and its applications in machine learning",
        multimodal_content=[{
            "type": "equation",
            "latex": "\\text{Accuracy} = \\frac{TP + TN}{TP + TN + FP + FN}",
            "equation_caption": "Classification Accuracy Formula"
        }],
        mode="hybrid"
    )
    print(f"📝 Result: {equation_result[:300]}...")

if __name__ == "__main__":
    asyncio.run(multimodal_query_example())
```

### 4. Batch Processing Example

```python
# /opt/raganything/scripts/batch_process.py
#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/opt/raganything/app')

from raganything import BedrockRAGAnything, RAGAnythingConfig, BedrockConfig

async def batch_process_example(folder_path: str):
    """Process multiple documents in a folder"""
    
    print(f"📁 Batch processing folder: {folder_path}")
    
    # Initialize RAG Anything
    rag_config = RAGAnythingConfig(
        working_dir="/opt/raganything/data/rag_storage",
        max_concurrent_files=2,  # Process 2 files concurrently
    )
    
    bedrock_config = BedrockConfig.from_env()
    
    rag = BedrockRAGAnything(
        config=rag_config,
        bedrock_config=bedrock_config
    )
    
    try:
        # Process all documents in folder
        await rag.process_folder_complete(
            folder_path=folder_path,
            output_dir="/opt/raganything/data/output",
            file_extensions=[".pdf", ".docx", ".pptx", ".txt"],
            recursive=True,
            max_workers=2
        )
        
        print("✅ Batch processing completed!")
        
        # Query the processed documents
        result = await rag.aquery(
            "What are the common themes across all processed documents?",
            mode="global"
        )
        print(f"📝 Summary: {result[:400]}...")
        
    except Exception as e:
        print(f"❌ Error in batch processing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python batch_process.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    if not Path(folder_path).exists():
        print(f"❌ Folder not found: {folder_path}")
        sys.exit(1)
    
    asyncio.run(batch_process_example(folder_path))
```

## Troubleshooting

### Common Issues and Solutions

#### 1. AWS Authentication Issues

**Problem**: `NoCredentialsError` or `AccessDenied` errors

**Solutions**:
```bash
# Check if IAM role is attached to instance
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Verify IAM role permissions
aws sts get-caller-identity

# Check Bedrock model access
aws bedrock list-foundation-models --region us-east-1
```

#### 2. Model Access Issues

**Problem**: `AccessDeniedException` when calling Bedrock models

**Solutions**:
1. Verify model access in Bedrock console
2. Check if models are available in your region
3. Ensure IAM policy includes correct model ARNs

```bash
# Test model access
aws bedrock invoke-model \
    --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
    --body '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":100,"anthropic_version":"bedrock-2023-05-31"}' \
    --cli-binary-format raw-in-base64-out \
    --region us-east-1 \
    output.json
```

#### 3. Memory Issues

**Problem**: Out of memory errors during processing

**Solutions**:
```bash
# Check memory usage
free -h
htop

# Increase swap space
sudo dd if=/dev/zero of=/swapfile bs=1G count=4
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 4. Rate Limiting Issues

**Problem**: `ThrottlingException` errors

**Solutions**:
- Reduce `MAX_CONCURRENT_FILES` in configuration
- Implement longer delays between requests
- Use Claude Haiku for faster, less resource-intensive tasks

#### 5. LibreOffice Issues

**Problem**: Office document processing fails

**Solutions**:
```bash
# Reinstall LibreOffice
sudo dnf remove -y libreoffice*
sudo dnf install -y libreoffice

# Check LibreOffice installation
libreoffice --version

# Test conversion
libreoffice --headless --convert-to pdf test.docx
```

### Debugging Commands

```bash
# Check service status
sudo systemctl status raganything

# View logs
sudo journalctl -u raganything -f

# Check application logs
tail -f /opt/raganything/logs/*.log

# Test AWS connectivity
aws bedrock list-foundation-models --region us-east-1

# Check disk space
df -h

# Monitor resource usage
htop
iostat -x 1
```

## Performance Optimization

### 1. Instance Optimization

**Recommended Instance Types by Use Case**:
- **Light usage**: `t3.large` (2 vCPU, 8GB RAM)
- **Medium usage**: `m5.xlarge` (4 vCPU, 16GB RAM)
- **Heavy usage**: `m5.2xlarge` (8 vCPU, 32GB RAM)
- **GPU workloads**: `g4dn.xlarge` (if using local models)

### 2. Configuration Tuning

```bash
# Optimize for performance
cat >> /opt/raganything/config/.env << 'EOF'

# Performance Settings
MAX_CONCURRENT_FILES=4
BEDROCK_RETRY_MAX_ATTEMPTS=5
BEDROCK_RETRY_BACKOFF_FACTOR=1.5

# Memory Management
CONTEXT_WINDOW=2
MAX_CONTEXT_TOKENS=4000

# Caching
ENABLE_LLM_CACHE=true
CACHE_MAX_SIZE=1000

EOF
```

### 3. Storage Optimization

```bash
# Use faster storage for vector database
sudo mkdir -p /opt/raganything/data/fast_storage
sudo mount -t tmpfs -o size=4G tmpfs /opt/raganything/data/fast_storage

# Make permanent (add to /etc/fstab)
echo 'tmpfs /opt/raganything/data/fast_storage tmpfs size=4G 0 0' | sudo tee -a /etc/fstab
```

### 4. Network Optimization

```bash
# Optimize network settings for AWS API calls
echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 87380 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 16777216' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## Monitoring and Maintenance

### 1. Health Check Script

```bash
# /opt/raganything/scripts/health_check.sh
#!/bin/bash

echo "🏥 RAG Anything Health Check"
echo "=========================="

# Check service status
if systemctl is-active --quiet raganything; then
    echo "✅ Service is running"
else
    echo "❌ Service is not running"
    sudo systemctl status raganything
fi

# Check disk space
DISK_USAGE=$(df /opt/raganything | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️  Disk usage is high: ${DISK_USAGE}%"
else
    echo "✅ Disk usage is normal: ${DISK_USAGE}%"
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEM_USAGE -gt 80 ]; then
    echo "⚠️  Memory usage is high: ${MEM_USAGE}%"
else
    echo "✅ Memory usage is normal: ${MEM_USAGE}%"
fi

# Test AWS connectivity
if aws bedrock list-foundation-models --region us-east-1 >/dev/null 2>&1; then
    echo "✅ AWS Bedrock connectivity is working"
else
    echo "❌ AWS Bedrock connectivity failed"
fi

echo "=========================="
```

### 2. Automated Backup Script

```bash
# /opt/raganything/scripts/backup.sh
#!/bin/bash

BACKUP_DIR="/opt/raganything/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C /opt/raganything config/

# Backup vector database
tar -czf $BACKUP_DIR/rag_storage_$DATE.tar.gz -C /opt/raganything/data rag_storage/

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup completed: $DATE"
```

### 3. Log Monitoring

```bash
# /opt/raganything/scripts/monitor_logs.sh
#!/bin/bash

# Monitor for errors in logs
tail -f /opt/raganything/logs/*.log | grep -E "(ERROR|CRITICAL|Exception)" --color=always
```

### 4. Cron Jobs Setup

```bash
# Add to crontab for raganything user
sudo su - raganything
crontab -e

# Add these lines:
# Health check every 5 minutes
*/5 * * * * /opt/raganything/scripts/health_check.sh >> /opt/raganything/logs/health_check.log 2>&1

# Daily backup at 2 AM
0 2 * * * /opt/raganything/scripts/backup.sh >> /opt/raganything/logs/backup.log 2>&1

# Weekly cleanup at 3 AM on Sundays
0 3 * * 0 find /opt/raganything/logs -name "*.log.*" -mtime +30 -delete
```

## Advanced Features

### 1. Load Balancing with Multiple Instances

For high-availability deployments, you can set up multiple EC2 instances behind an Application Load Balancer:

```bash
# Create target group
aws elbv2 create-target-group \
    --name raganything-targets \
    --protocol HTTP \
    --port 80 \
    --vpc-id YOUR_VPC_ID \
    --health-check-path /health

# Create load balancer
aws elbv2 create-load-balancer \
    --name raganything-alb \
    --subnets subnet-12345 subnet-67890 \
    --security-groups sg-12345
```

### 2. Auto Scaling Configuration

```bash
# Create launch template
aws ec2 create-launch-template \
    --launch-template-name raganything-template \
    --launch-template-data '{
        "ImageId": "ami-12345",
        "InstanceType": "t3.large",
        "IamInstanceProfile": {"Name": "RAGAnything-InstanceProfile"},
        "SecurityGroupIds": ["sg-12345"],
        "UserData": "base64-encoded-startup-script"
    }'

# Create auto scaling group
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name raganything-asg \
    --launch-template LaunchTemplateName=raganything-template,Version=1 \
    --min-size 1 \
    --max-size 5 \
    --desired-capacity 2 \
    --target-group-arns arn:aws:elasticloadbalancing:region:account:targetgroup/raganything-targets/id
```

### 3. CloudWatch Monitoring

```bash
# Create custom metrics
aws logs create-log-group --log-group-name /aws/ec2/raganything

# Install CloudWatch agent
sudo yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
sudo cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/opt/raganything/logs/*.log",
                        "log_group_name": "/aws/ec2/raganything",
                        "log_stream_name": "{instance_id}/application"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "RAGAnything",
        "metrics_collected": {
            "cpu": {
                "measurement": ["cpu_usage_idle", "cpu_usage_iowait"],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": ["used_percent"],
                "metrics_collection_interval": 60,
                "resources": ["*"]
            },
            "mem": {
                "measurement": ["mem_used_percent"],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
sudo systemctl enable amazon-cloudwatch-agent
sudo systemctl start amazon-cloudwatch-agent
```

## Security Best Practices

### 1. Network Security

```bash
# Restrict SSH access to specific IPs
aws ec2 authorize-security-group-ingress \
    --group-id sg-12345 \
    --protocol tcp \
    --port 22 \
    --cidr YOUR_OFFICE_IP/32

# Remove default SSH rule
aws ec2 revoke-security-group-ingress \
    --group-id sg-12345 \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0
```

### 2. Data Encryption

```bash
# Encrypt EBS volumes
aws ec2 modify-instance-attribute \
    --instance-id i-12345 \
    --block-device-mappings '[{
        "DeviceName": "/dev/xvda",
        "Ebs": {"Encrypted": true}
    }]'

# Use encrypted S3 bucket for document storage
aws s3api create-bucket \
    --bucket raganything-documents-encrypted \
    --create-bucket-configuration LocationConstraint=us-east-1

aws s3api put-bucket-encryption \
    --bucket raganything-documents-encrypted \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
```

### 3. Access Logging

```bash
# Enable VPC Flow Logs
aws ec2 create-flow-logs \
    --resource-type VPC \
    --resource-ids vpc-12345 \
    --traffic-type ALL \
    --log-destination-type cloud-watch-logs \
    --log-group-name VPCFlowLogs

# Enable CloudTrail
aws cloudtrail create-trail \
    --name raganything-trail \
    --s3-bucket-name raganything-cloudtrail-logs
```

## Cost Optimization

### 1. Instance Cost Optimization

```bash
# Use Spot Instances for development
aws ec2 request-spot-instances \
    --spot-price "0.05" \
    --instance-count 1 \
    --type "one-time" \
    --launch-specification '{
        "ImageId": "ami-12345",
        "InstanceType": "t3.large",
        "KeyName": "your-key",
        "SecurityGroups": ["RAGAnything-SG"],
        "IamInstanceProfile": {"Name": "RAGAnything-InstanceProfile"}
    }'

# Use Reserved Instances for production
aws ec2 purchase-reserved-instances-offering \
    --reserved-instances-offering-id offering-12345 \
    --instance-count 1
```

### 2. Bedrock Cost Monitoring

```bash
# Set up billing alerts
aws budgets create-budget \
    --account-id YOUR_ACCOUNT_ID \
    --budget '{
        "BudgetName": "RAGAnything-Bedrock-Budget",
        "BudgetLimit": {"Amount": "100", "Unit": "USD"},
        "TimeUnit": "MONTHLY",
        "BudgetType": "COST",
        "CostFilters": {
            "Service": ["Amazon Bedrock"]
        }
    }' \
    --notifications-with-subscribers '[{
        "Notification": {
            "NotificationType": "ACTUAL",
            "ComparisonOperator": "GREATER_THAN",
            "Threshold": 80
        },
        "Subscribers": [{
            "SubscriptionType": "EMAIL",
            "Address": "your-email@example.com"
        }]
    }]'
```

## Conclusion

This comprehensive guide provides everything you need to deploy and operate RAG Anything with AWS Bedrock on EC2. The integration offers:

- **Complete AWS Integration**: Native support for Bedrock models
- **Production Ready**: Systemd services, monitoring, and logging
- **Scalable Architecture**: Support for load balancing and auto scaling
- **Security Focused**: IAM roles, encryption, and access controls
- **Cost Optimized**: Efficient resource usage and cost monitoring

For additional support or questions, refer to the troubleshooting section or check the project documentation.

**Next Steps:**
1. Follow the installation guide step by step
2. Test with sample documents
3. Configure monitoring and alerting
4. Scale based on your usage patterns
5. Implement additional security measures as needed

The implementation tasks in the spec will create all the necessary code components to make this integration work seamlessly with the existing RAG Anything architecture.