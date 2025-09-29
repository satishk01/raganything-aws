# Installation Fixes for Amazon Linux 2023

## 🔧 **Fixed Issues**

### 1. **Curl Package Conflict**
- **Problem**: `curl-minimal` conflicts with `curl` package
- **Solution**: Use `--allowerasing` flag to resolve conflicts

### 2. **LibreOffice Not Available**
- **Problem**: LibreOffice not in default Amazon Linux 2023 repositories
- **Solution**: Try EPEL repository or install alternatives

## 📋 **Available Installation Scripts**

### **Option 1: Fixed Installation Script (Recommended)**
```bash
# Make executable and run
chmod +x deployment/scripts/install_amazon_linux_2023_fixed.sh
./deployment/scripts/install_amazon_linux_2023_fixed.sh
```

### **Option 2: Original Fixed Script**
```bash
# Make executable and run
chmod +x deployment/scripts/install_fixed.sh
./deployment/scripts/install_fixed.sh
```

### **Option 3: Manual Fix + Original Script**
```bash
# Fix curl conflict first
chmod +x fix_curl_conflict.sh
./fix_curl_conflict.sh

# Then run original script
./deployment/scripts/install.sh
```

## 🔧 **Manual Fixes**

### **Fix Curl Conflict**
```bash
# Remove conflicting package
sudo dnf remove -y curl-minimal

# Install curl with conflict resolution
sudo dnf install -y --allowerasing curl

# Verify installation
curl --version
```

### **Fix LibreOffice Issue**
```bash
# Run LibreOffice fix script
chmod +x fix_libreoffice_amazon_linux.sh
./fix_libreoffice_amazon_linux.sh
```

**Or manually:**
```bash
# Method 1: EPEL repository
sudo dnf install -y epel-release
sudo dnf install -y libreoffice-core libreoffice-writer libreoffice-calc

# Method 2: CRB repository
sudo dnf config-manager --set-enabled crb
sudo dnf install -y libreoffice

# Method 3: Alternative tools
sudo dnf install -y pandoc
```

## ✅ **Recommended Installation Process**

### **Step 1: Use the Fixed Script**
```bash
# Clone repository
git clone https://github.com/satishk01/raganything-aws.git
cd raganything-aws

# Make script executable
chmod +x deployment/scripts/install_amazon_linux_2023_fixed.sh

# Run installation
./deployment/scripts/install_amazon_linux_2023_fixed.sh
```

### **Step 2: Test Installation**
```bash
# Test Bedrock integration
sudo -u raganything /opt/raganything/scripts/test_bedrock.py

# Check service status
sudo systemctl status raganything

# Run health check
/opt/raganything/scripts/health_check.sh
```

### **Step 3: Start Service**
```bash
# Start the service
/opt/raganything/scripts/start.sh

# Check if running
sudo systemctl status raganything
```

## 🚨 **Troubleshooting**

### **If Curl Issues Persist**
```bash
# Clean package cache
sudo dnf clean all
sudo dnf makecache

# Force remove curl-minimal
sudo rpm -e --nodeps curl-minimal

# Install curl
sudo dnf install -y curl
```

### **If LibreOffice Issues Persist**
```bash
# Install Python alternatives
sudo -u raganything /opt/raganything/venv/bin/pip install \
    python-docx \
    openpyxl \
    python-pptx \
    PyPDF2 \
    pdfplumber

# Or download LibreOffice manually
# https://www.libreoffice.org/download/download/
```

### **If Installation Fails**
```bash
# Check system requirements
cat /etc/os-release
python3.11 --version
dnf --version

# Check available space
df -h

# Check memory
free -h

# Check logs
sudo journalctl -xe
```

## 📊 **What Each Script Does**

### **install_amazon_linux_2023_fixed.sh**
- ✅ Handles curl conflicts automatically
- ✅ Tries multiple LibreOffice installation methods
- ✅ Installs Python document processing alternatives
- ✅ Creates all necessary directories and scripts
- ✅ Sets up systemd service
- ✅ Configures monitoring and logging
- ✅ Provides comprehensive error handling

### **install_fixed.sh**
- ✅ Handles curl conflicts
- ✅ Basic LibreOffice installation attempt
- ✅ Standard RAG Anything setup

### **install.sh**
- ✅ Updated with curl conflict resolution
- ✅ Enhanced LibreOffice handling
- ✅ Standard installation process

## 🎯 **Expected Results**

After successful installation:
- ✅ RAG Anything with Bedrock integration installed
- ✅ All Python dependencies available
- ✅ Document processing capabilities (LibreOffice or alternatives)
- ✅ Systemd service configured and enabled
- ✅ Health monitoring and backup scripts created
- ✅ CloudWatch agent configured (if available)

## 📞 **Support**

If you encounter issues:
1. Check the installation logs
2. Run the health check script
3. Verify AWS Bedrock access
4. Check system resources (disk, memory)
5. Review the troubleshooting section above

The `install_amazon_linux_2023_fixed.sh` script is the most comprehensive and should handle all known issues with Amazon Linux 2023.