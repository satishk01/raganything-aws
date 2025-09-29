#!/bin/bash
set -e

# RAG Anything with AWS Bedrock Installation Script for Amazon Linux 2023
# This script sets up the complete environment for running RAG Anything with Bedrock

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as ec2-user."
fi

# Check if running on Amazon Linux 2023
if ! grep -q "Amazon Linux" /etc/os-release; then
    error "This script is designed for Amazon Linux 2023"
fi

log "Starting RAG Anything with AWS Bedrock installation..."

# Update system
log "Updating system packages..."
sudo dnf update -y

# Install system dependencies
log "Installing system dependencies..."
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
    unzip \
    htop \
    tree \
    vim

# Install LibreOffice for office document processing
log "Installing LibreOffice..."
sudo dnf install -y libreoffice

# Create application user if it doesn't exist
if ! id "raganything" &>/dev/null; then
    log "Creating raganything user..."
    sudo useradd -m -s /bin/bash raganything
fi

# Create directory structure
log "Creating directory structure..."
sudo mkdir -p /opt/raganything/{app,config,logs,data,cache,scripts,backups}
sudo chown -R raganything:raganything /opt/raganything

# Set up Python virtual environment
log "Setting up Python virtual environment..."
sudo -u raganything python3.11 -m venv /opt/raganything/venv

# Upgrade pip and install build tools
log "Upgrading pip and installing build tools..."
sudo -u raganything /opt/raganything/venv/bin/pip install --upgrade pip setuptools wheel

# Install AWS SDK
log "Installing AWS SDK..."
sudo -u raganything /opt/raganything/venv/bin/pip install boto3 botocore

# Install additional dependencies
log "Installing additional Python dependencies..."
sudo -u raganything /opt/raganything/venv/bin/pip install \
    python-dotenv \
    asyncio-throttle \
    tenacity \
    aiofiles \
    uvloop

# Install RAG Anything with all dependencies
log "Installing RAG Anything..."
sudo -u raganything /opt/raganything/venv/bin/pip install 'raganything[all]'

# Clone the enhanced RAG Anything repository (if available)
log "Setting up application code..."
if [ -d "/opt/raganything/app/.git" ]; then
    log "Updating existing repository..."
    sudo -u raganything git -C /opt/raganything/app pull
else
    log "Cloning RAG Anything repository..."
    sudo -u raganything git clone https://github.com/HKUDS/RAG-Anything.git /opt/raganything/app
fi

# Install application in development mode
log "Installing application in development mode..."
sudo -u raganything /opt/raganything/venv/bin/pip install -e /opt/raganything/app

# Copy configuration template
log "Setting up configuration..."
if [ ! -f "/opt/raganything/config/.env" ]; then
    sudo -u raganything cp /opt/raganything/app/deployment/config/environment.template /opt/raganything/config/.env
    sudo -u raganything chmod 600 /opt/raganything/config/.env
    log "Configuration template copied to /opt/raganything/config/.env"
    warn "Please edit /opt/raganything/config/.env to customize your settings"
else
    log "Configuration file already exists, skipping template copy"
fi

# Set up systemd service
log "Setting up systemd service..."
sudo cp /opt/raganything/app/deployment/systemd/raganything.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raganything

# Set up log rotation
log "Setting up log rotation..."
sudo tee /etc/logrotate.d/raganything > /dev/null << 'EOF'
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

# Create health check script
log "Creating health check script..."
sudo -u raganything tee /opt/raganything/scripts/health_check.sh > /dev/null << 'EOF'
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
if aws bedrock list-foundation-models --region $(aws configure get region 2>/dev/null || echo "us-east-1") >/dev/null 2>&1; then
    echo "✅ AWS Bedrock connectivity is working"
else
    echo "❌ AWS Bedrock connectivity failed"
fi

echo "=========================="
EOF

chmod +x /opt/raganything/scripts/health_check.sh

# Create backup script
log "Creating backup script..."
sudo -u raganything tee /opt/raganything/scripts/backup.sh > /dev/null << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/raganything/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C /opt/raganything config/

# Backup vector database
if [ -d "/opt/raganything/data/rag_storage" ]; then
    tar -czf $BACKUP_DIR/rag_storage_$DATE.tar.gz -C /opt/raganything/data rag_storage/
fi

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup completed: $DATE"
EOF

chmod +x /opt/raganything/scripts/backup.sh

# Create test script
log "Creating test script..."
sudo -u raganything tee /opt/raganything/scripts/test_bedrock.py > /dev/null << 'EOF'
#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/opt/raganything/app')

try:
    from raganything.bedrock_rag import BedrockRAGAnything
    from raganything import RAGAnythingConfig
    from raganything.bedrock import BedrockConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure RAG Anything with Bedrock integration is properly installed")
    sys.exit(1)

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
        
        # Validate Bedrock access
        print("\n🔍 Validating Bedrock access...")
        if await rag.validate_bedrock_access():
            print("✅ Bedrock access validation successful")
        else:
            print("❌ Bedrock access validation failed")
            return False
        
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
EOF

chmod +x /opt/raganything/scripts/test_bedrock.py

# Install CloudWatch agent if not already installed
if ! command -v /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl &> /dev/null; then
    log "Installing CloudWatch agent..."
    sudo dnf install -y amazon-cloudwatch-agent
fi

# Create CloudWatch agent configuration
log "Creating CloudWatch agent configuration..."
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json > /dev/null << 'EOF'
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
log "Starting CloudWatch agent..."
sudo systemctl enable amazon-cloudwatch-agent
sudo systemctl start amazon-cloudwatch-agent

# Set up cron jobs for maintenance
log "Setting up cron jobs..."
sudo -u raganything crontab -l 2>/dev/null | { cat; echo "# RAG Anything maintenance jobs"; echo "*/5 * * * * /opt/raganything/scripts/health_check.sh >> /opt/raganything/logs/health_check.log 2>&1"; echo "0 2 * * * /opt/raganything/scripts/backup.sh >> /opt/raganything/logs/backup.log 2>&1"; echo "0 3 * * 0 find /opt/raganything/logs -name '*.log.*' -mtime +30 -delete"; } | sudo -u raganything crontab -

# Create startup script
log "Creating startup script..."
sudo tee /opt/raganything/scripts/start.sh > /dev/null << 'EOF'
#!/bin/bash

echo "🚀 Starting RAG Anything with AWS Bedrock..."

# Load environment variables
source /opt/raganything/config/.env

# Start the service
sudo systemctl start raganything

# Check status
sleep 5
if systemctl is-active --quiet raganything; then
    echo "✅ RAG Anything service started successfully"
    echo "📊 Service status:"
    sudo systemctl status raganything --no-pager -l
else
    echo "❌ Failed to start RAG Anything service"
    echo "📋 Service logs:"
    sudo journalctl -u raganything --no-pager -l
    exit 1
fi
EOF

chmod +x /opt/raganything/scripts/start.sh

# Create stop script
log "Creating stop script..."
sudo tee /opt/raganything/scripts/stop.sh > /dev/null << 'EOF'
#!/bin/bash

echo "🛑 Stopping RAG Anything service..."

sudo systemctl stop raganything

if ! systemctl is-active --quiet raganything; then
    echo "✅ RAG Anything service stopped successfully"
else
    echo "❌ Failed to stop RAG Anything service"
    exit 1
fi
EOF

chmod +x /opt/raganything/scripts/stop.sh

# Set proper permissions
log "Setting proper permissions..."
sudo chown -R raganything:raganything /opt/raganything
sudo chmod -R 755 /opt/raganything/scripts
sudo chmod 600 /opt/raganything/config/.env

log "✅ Installation completed successfully!"
echo
echo "📋 Next steps:"
echo "1. Edit /opt/raganything/config/.env to customize your configuration"
echo "2. Test the installation: sudo -u raganything /opt/raganything/scripts/test_bedrock.py"
echo "3. Start the service: /opt/raganything/scripts/start.sh"
echo "4. Check health: /opt/raganything/scripts/health_check.sh"
echo
echo "📁 Important directories:"
echo "  - Application: /opt/raganything/app"
echo "  - Configuration: /opt/raganything/config"
echo "  - Logs: /opt/raganything/logs"
echo "  - Data: /opt/raganything/data"
echo "  - Scripts: /opt/raganything/scripts"
echo
echo "🔧 Useful commands:"
echo "  - View logs: sudo journalctl -u raganything -f"
echo "  - Service status: sudo systemctl status raganything"
echo "  - Restart service: sudo systemctl restart raganything"
echo
log "Installation complete! 🎉"