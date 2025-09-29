#!/bin/bash
set -e

# RAG Anything Monitoring Setup Script
# Sets up comprehensive monitoring for RAG Anything with AWS Bedrock

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION=${AWS_REGION:-us-east-1}
LOG_GROUP_NAME="/aws/ec2/raganything"
DASHBOARD_NAME="RAGAnything-Bedrock"

# Logging functions
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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root for system monitoring setup"
fi

log "🔍 Setting up monitoring for RAG Anything with AWS Bedrock..."

# Install monitoring tools
log "Installing monitoring tools..."
dnf install -y htop iotop nethogs sysstat

# Create CloudWatch log group if it doesn't exist
log "Creating CloudWatch log group..."
aws logs create-log-group --log-group-name "$LOG_GROUP_NAME" --region "$REGION" 2>/dev/null || true

# Set up CloudWatch agent configuration
log "Configuring CloudWatch agent..."
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "cwagent"
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/opt/raganything/logs/raganything.log",
                        "log_group_name": "/aws/ec2/raganything",
                        "log_stream_name": "{instance_id}/application",
                        "timezone": "UTC",
                        "timestamp_format": "%Y-%m-%d %H:%M:%S"
                    },
                    {
                        "file_path": "/var/log/messages",
                        "log_group_name": "/aws/ec2/raganything",
                        "log_stream_name": "{instance_id}/system",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/opt/raganything/logs/health_check.log",
                        "log_group_name": "/aws/ec2/raganything",
                        "log_stream_name": "{instance_id}/health",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "RAGAnything",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60,
                "resources": ["*"],
                "totalcpu": true
            },
            "disk": {
                "measurement": [
                    "used_percent",
                    "inodes_free"
                ],
                "metrics_collection_interval": 60,
                "resources": ["*"]
            },
            "diskio": {
                "measurement": [
                    "io_time",
                    "read_bytes",
                    "write_bytes",
                    "reads",
                    "writes"
                ],
                "metrics_collection_interval": 60,
                "resources": ["*"]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent",
                    "mem_available_percent"
                ],
                "metrics_collection_interval": 60
            },
            "netstat": {
                "measurement": [
                    "tcp_established",
                    "tcp_time_wait"
                ],
                "metrics_collection_interval": 60
            },
            "processes": {
                "measurement": [
                    "running",
                    "sleeping",
                    "dead"
                ]
            }
        }
    }
}
EOF

# Restart CloudWatch agent
log "Restarting CloudWatch agent..."
systemctl restart amazon-cloudwatch-agent
systemctl enable amazon-cloudwatch-agent

# Create custom monitoring script
log "Creating custom monitoring script..."
cat > /opt/raganything/scripts/monitor.py << 'EOF'
#!/usr/bin/env python3
"""
Custom monitoring script for RAG Anything with AWS Bedrock
"""

import json
import time
import psutil
import boto3
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/raganything/logs/monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class RAGAnythingMonitor:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = 'RAGAnything/Custom'
        
    def collect_system_metrics(self):
        """Collect system metrics"""
        metrics = {}
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics['CPUUtilization'] = cpu_percent
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics['MemoryUtilization'] = memory.percent
        metrics['MemoryAvailable'] = memory.available / (1024**3)  # GB
        
        # Disk metrics
        disk = psutil.disk_usage('/opt/raganything')
        metrics['DiskUtilization'] = (disk.used / disk.total) * 100
        metrics['DiskFree'] = disk.free / (1024**3)  # GB
        
        # Network metrics
        network = psutil.net_io_counters()
        metrics['NetworkBytesIn'] = network.bytes_recv
        metrics['NetworkBytesOut'] = network.bytes_sent
        
        return metrics
    
    def collect_application_metrics(self):
        """Collect application-specific metrics"""
        metrics = {}
        
        # Check if RAG Anything service is running
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'raganything' in ' '.join(proc.info['cmdline'] or []):
                    process = psutil.Process(proc.info['pid'])
                    metrics['ProcessCPU'] = process.cpu_percent()
                    metrics['ProcessMemory'] = process.memory_info().rss / (1024**2)  # MB
                    metrics['ServiceStatus'] = 1
                    break
            else:
                metrics['ServiceStatus'] = 0
        except Exception as e:
            logger.error(f"Error collecting process metrics: {e}")
            metrics['ServiceStatus'] = 0
        
        # Check log file sizes
        log_dir = Path('/opt/raganything/logs')
        if log_dir.exists():
            total_log_size = sum(f.stat().st_size for f in log_dir.glob('*.log'))
            metrics['LogFileSize'] = total_log_size / (1024**2)  # MB
        
        # Check data directory size
        data_dir = Path('/opt/raganything/data')
        if data_dir.exists():
            total_data_size = sum(f.stat().st_size for f in data_dir.rglob('*') if f.is_file())
            metrics['DataDirectorySize'] = total_data_size / (1024**3)  # GB
        
        return metrics
    
    def send_metrics_to_cloudwatch(self, metrics):
        """Send metrics to CloudWatch"""
        try:
            metric_data = []
            
            for metric_name, value in metrics.items():
                metric_data.append({
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow()
                })
            
            # Send in batches of 20 (CloudWatch limit)
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i:i+20]
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
            
            logger.info(f"Sent {len(metric_data)} metrics to CloudWatch")
            
        except Exception as e:
            logger.error(f"Error sending metrics to CloudWatch: {e}")
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        logger.info("Starting monitoring cycle")
        
        # Collect metrics
        system_metrics = self.collect_system_metrics()
        app_metrics = self.collect_application_metrics()
        
        # Combine metrics
        all_metrics = {**system_metrics, **app_metrics}
        
        # Log metrics locally
        logger.info(f"Collected metrics: {json.dumps(all_metrics, indent=2)}")
        
        # Send to CloudWatch
        self.send_metrics_to_cloudwatch(all_metrics)
        
        logger.info("Monitoring cycle completed")

def main():
    monitor = RAGAnythingMonitor()
    
    while True:
        try:
            monitor.run_monitoring_cycle()
            time.sleep(300)  # Run every 5 minutes
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    main()
EOF

chmod +x /opt/raganything/scripts/monitor.py

# Install Python dependencies for monitoring
log "Installing Python dependencies for monitoring..."
/opt/raganything/venv/bin/pip install psutil boto3

# Create monitoring service
log "Creating monitoring service..."
cat > /etc/systemd/system/raganything-monitor.service << 'EOF'
[Unit]
Description=RAG Anything Custom Monitor
After=network.target raganything.service
Wants=raganything.service

[Service]
Type=simple
User=raganything
Group=raganything
WorkingDirectory=/opt/raganything
Environment=PATH=/opt/raganything/venv/bin
EnvironmentFile=/opt/raganything/config/.env
ExecStart=/opt/raganything/venv/bin/python /opt/raganything/scripts/monitor.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable raganything-monitor

# Create CloudWatch dashboard
log "Creating CloudWatch dashboard..."
cat > /tmp/dashboard.json << EOF
{
    "widgets": [
        {
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "RAGAnything/Custom", "CPUUtilization" ],
                    [ ".", "MemoryUtilization" ]
                ],
                "period": 300,
                "stat": "Average",
                "region": "$REGION",
                "title": "System Utilization"
            }
        },
        {
            "type": "metric",
            "x": 12,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "RAGAnything/Custom", "ServiceStatus" ]
                ],
                "period": 300,
                "stat": "Average",
                "region": "$REGION",
                "title": "Service Status"
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 6,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "RAGAnything/Custom", "DiskUtilization" ],
                    [ ".", "DiskFree" ]
                ],
                "period": 300,
                "stat": "Average",
                "region": "$REGION",
                "title": "Disk Usage"
            }
        },
        {
            "type": "metric",
            "x": 12,
            "y": 6,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "RAGAnything/Custom", "ProcessCPU" ],
                    [ ".", "ProcessMemory" ]
                ],
                "period": 300,
                "stat": "Average",
                "region": "$REGION",
                "title": "Application Metrics"
            }
        },
        {
            "type": "log",
            "x": 0,
            "y": 12,
            "width": 24,
            "height": 6,
            "properties": {
                "query": "SOURCE '$LOG_GROUP_NAME'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100",
                "region": "$REGION",
                "title": "Recent Errors"
            }
        }
    ]
}
EOF

aws cloudwatch put-dashboard \
    --dashboard-name "$DASHBOARD_NAME" \
    --dashboard-body file:///tmp/dashboard.json \
    --region "$REGION"

rm /tmp/dashboard.json

# Create alerting rules
log "Creating CloudWatch alarms..."

# High CPU alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "RAGAnything-HighCPU" \
    --alarm-description "RAG Anything high CPU utilization" \
    --metric-name CPUUtilization \
    --namespace RAGAnything/Custom \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --region "$REGION"

# High memory alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "RAGAnything-HighMemory" \
    --alarm-description "RAG Anything high memory utilization" \
    --metric-name MemoryUtilization \
    --namespace RAGAnything/Custom \
    --statistic Average \
    --period 300 \
    --threshold 85 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --region "$REGION"

# Service down alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "RAGAnything-ServiceDown" \
    --alarm-description "RAG Anything service is down" \
    --metric-name ServiceStatus \
    --namespace RAGAnything/Custom \
    --statistic Average \
    --period 300 \
    --threshold 1 \
    --comparison-operator LessThanThreshold \
    --evaluation-periods 1 \
    --region "$REGION"

# High disk usage alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "RAGAnything-HighDisk" \
    --alarm-description "RAG Anything high disk utilization" \
    --metric-name DiskUtilization \
    --namespace RAGAnything/Custom \
    --statistic Average \
    --period 300 \
    --threshold 90 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --region "$REGION"

# Set up log rotation for monitoring logs
log "Setting up log rotation for monitoring..."
cat > /etc/logrotate.d/raganything-monitor << 'EOF'
/opt/raganything/logs/monitor.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 raganything raganything
    postrotate
        systemctl reload raganything-monitor
    endscript
}
EOF

# Create monitoring status script
log "Creating monitoring status script..."
cat > /opt/raganything/scripts/monitoring_status.sh << 'EOF'
#!/bin/bash

echo "📊 RAG Anything Monitoring Status"
echo "================================="

# Check CloudWatch agent
if systemctl is-active --quiet amazon-cloudwatch-agent; then
    echo "✅ CloudWatch Agent: Running"
else
    echo "❌ CloudWatch Agent: Not running"
fi

# Check custom monitor
if systemctl is-active --quiet raganything-monitor; then
    echo "✅ Custom Monitor: Running"
else
    echo "❌ Custom Monitor: Not running"
fi

# Check recent metrics
echo
echo "📈 Recent Metrics (last 5 minutes):"
aws cloudwatch get-metric-statistics \
    --namespace RAGAnything/Custom \
    --metric-name CPUUtilization \
    --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average \
    --query 'Datapoints[0].Average' \
    --output text 2>/dev/null | xargs -I {} echo "  CPU: {}%"

aws cloudwatch get-metric-statistics \
    --namespace RAGAnything/Custom \
    --metric-name MemoryUtilization \
    --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average \
    --query 'Datapoints[0].Average' \
    --output text 2>/dev/null | xargs -I {} echo "  Memory: {}%"

# Check alarms
echo
echo "🚨 Active Alarms:"
aws cloudwatch describe-alarms \
    --alarm-names "RAGAnything-HighCPU" "RAGAnything-HighMemory" "RAGAnything-ServiceDown" "RAGAnything-HighDisk" \
    --state-value ALARM \
    --query 'MetricAlarms[].AlarmName' \
    --output text 2>/dev/null || echo "  No active alarms"

echo
echo "🔗 CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#dashboards:name=$DASHBOARD_NAME"
EOF

chmod +x /opt/raganything/scripts/monitoring_status.sh
chown raganything:raganything /opt/raganything/scripts/monitoring_status.sh

log "✅ Monitoring setup completed successfully!"
echo
echo "📋 Monitoring Components Installed:"
echo "  - CloudWatch Agent with custom configuration"
echo "  - Custom monitoring service (raganything-monitor)"
echo "  - CloudWatch Dashboard: $DASHBOARD_NAME"
echo "  - CloudWatch Alarms for CPU, Memory, Disk, and Service status"
echo "  - Log aggregation to CloudWatch Logs"
echo
echo "🔧 Useful Commands:"
echo "  - Check monitoring status: /opt/raganything/scripts/monitoring_status.sh"
echo "  - View custom monitor logs: journalctl -u raganything-monitor -f"
echo "  - View CloudWatch agent logs: journalctl -u amazon-cloudwatch-agent -f"
echo "  - Start custom monitor: systemctl start raganything-monitor"
echo
echo "🌐 Access your dashboard at:"
echo "  https://console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=$DASHBOARD_NAME"