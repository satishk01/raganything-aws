#!/bin/bash

# Quick fix for pip disk space issues
echo "🔧 Quick fix for pip disk space issues..."

# Check current space
echo "📊 Current disk usage:"
df -h

# Clean pip cache
echo "🧹 Cleaning pip cache..."
pip cache purge 2>/dev/null || true
sudo -u raganything /opt/raganything/venv/bin/pip cache purge 2>/dev/null || true

# Clean system caches
echo "🧹 Cleaning system caches..."
sudo dnf clean all
sudo rm -rf /tmp/* 2>/dev/null || true
sudo rm -rf /var/tmp/* 2>/dev/null || true

# Clean journal logs
echo "🧹 Cleaning old logs..."
sudo journalctl --vacuum-time=3d

# Check space after cleanup
echo "📊 Space after cleanup:"
df -h

echo ""
echo "💡 Solutions for pip installation:"
echo "1. Use --no-cache-dir flag:"
echo "   pip install package --no-cache-dir"
echo ""
echo "2. Set temporary directory to a location with more space:"
echo "   export TMPDIR=/opt/raganything/tmp"
echo "   mkdir -p /opt/raganything/tmp"
echo ""
echo "3. Install packages one by one instead of all at once"
echo ""
echo "4. Use the CPU-only installation script:"
echo "   ./deployment/scripts/install_no_gpu.sh"
echo ""
echo "5. Expand EBS volume if needed:"
echo "   - Go to AWS Console → EC2 → Volumes"
echo "   - Select your volume and modify size"
echo "   - Run: sudo growpart /dev/xvda 1 && sudo resize2fs /dev/xvda1"

# Create a temporary directory with more space
echo ""
echo "🔧 Creating temporary directory for pip..."
sudo mkdir -p /opt/raganything/tmp
sudo chown -R raganything:raganything /opt/raganything/tmp
export TMPDIR=/opt/raganything/tmp

echo "✅ Temporary fixes applied!"
echo "Now try running pip with --no-cache-dir flag or use the CPU-only installation script."