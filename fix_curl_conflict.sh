#!/bin/bash

# Fix curl conflicts on Amazon Linux 2023
# Run this script if you encounter curl package conflicts

echo "🔧 Fixing curl package conflicts on Amazon Linux 2023..."

# Method 1: Remove curl-minimal and install curl
echo "Method 1: Removing curl-minimal and installing curl..."
sudo dnf remove -y curl-minimal
sudo dnf install -y curl

# Check if curl is working
if command -v curl &> /dev/null; then
    echo "✅ Method 1 successful: $(curl --version | head -n1)"
    exit 0
fi

# Method 2: Use --allowerasing flag
echo "Method 2: Using --allowerasing flag..."
sudo dnf install -y --allowerasing curl

# Check if curl is working
if command -v curl &> /dev/null; then
    echo "✅ Method 2 successful: $(curl --version | head -n1)"
    exit 0
fi

# Method 3: Use dnf swap
echo "Method 3: Using dnf swap..."
sudo dnf swap -y curl-minimal curl

# Check if curl is working
if command -v curl &> /dev/null; then
    echo "✅ Method 3 successful: $(curl --version | head -n1)"
    exit 0
fi

# Method 4: Force reinstall
echo "Method 4: Force reinstall..."
sudo dnf reinstall -y curl

# Check if curl is working
if command -v curl &> /dev/null; then
    echo "✅ Method 4 successful: $(curl --version | head -n1)"
    exit 0
fi

echo "❌ All methods failed. Please try manual resolution:"
echo "1. sudo dnf clean all"
echo "2. sudo dnf makecache"
echo "3. sudo dnf distro-sync"
echo "4. sudo dnf install --allowerasing curl"