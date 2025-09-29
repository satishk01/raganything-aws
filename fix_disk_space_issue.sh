#!/bin/bash

# Fix disk space issues during pip installation
# This script addresses common space issues on Amazon Linux 2023

echo "🔧 Fixing disk space issues for pip installation..."

# Check current disk usage
echo "📊 Current disk usage:"
df -h

echo ""
echo "📊 Checking specific directories:"
df -h /tmp
df -h /var/tmp
df -h /home/ec2-user
df -h /opt

# Check pip cache location
echo ""
echo "📊 Pip cache information:"
pip cache dir 2>/dev/null || echo "Pip cache directory not found"

# Clean up common space-consuming areas
echo ""
echo "🧹 Cleaning up temporary files and caches..."

# Clean pip cache
echo "Cleaning pip cache..."
pip cache purge 2>/dev/null || echo "No pip cache to clean"
sudo -u raganything /opt/raganything/venv/bin/pip cache purge 2>/dev/null || echo "No venv pip cache to clean"

# Clean dnf cache
echo "Cleaning dnf cache..."
sudo dnf clean all

# Clean temporary directories
echo "Cleaning temporary directories..."
sudo rm -rf /tmp/* 2>/dev/null || true
sudo rm -rf /var/tmp/* 2>/dev/null || true

# Clean journal logs if they're taking too much space
echo "Cleaning old journal logs..."
sudo journalctl --vacuum-time=7d

# Clean old log files
echo "Cleaning old log files..."
sudo find /var/log -name "*.log.*" -mtime +7 -delete 2>/dev/null || true

# Check for large files in home directory
echo ""
echo "🔍 Checking for large files in home directory..."
find /home/ec2-user -type f -size +100M 2>/dev/null | head -10 || echo "No large files found"

# Check available space after cleanup
echo ""
echo "📊 Disk usage after cleanup:"
df -h

# Check inode usage (sometimes the issue is inodes, not space)
echo ""
echo "📊 Inode usage:"
df -i

echo ""
echo "💡 Recommendations:"

# Check if /tmp is full
TMP_USAGE=$(df /tmp | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$TMP_USAGE" -gt 80 ]; then
    echo "⚠️  /tmp directory is ${TMP_USAGE}% full"
    echo "   Consider cleaning /tmp or using a different temp directory"
fi

# Check if root filesystem is full
ROOT_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$ROOT_USAGE" -gt 80 ]; then
    echo "⚠️  Root filesystem is ${ROOT_USAGE}% full"
    echo "   Consider expanding the EBS volume or cleaning up files"
fi

echo ""
echo "🔧 Solutions to try:"
echo "1. Use --no-cache-dir flag with pip"
echo "2. Set TMPDIR to a location with more space"
echo "3. Install packages one by one instead of all at once"
echo "4. Expand EBS volume if needed"
echo "5. Use pip install with --no-deps to avoid large dependencies"