#!/bin/bash

# Fix LibreOffice installation on Amazon Linux 2023
# Run this script if LibreOffice installation fails

echo "🔧 Fixing LibreOffice installation on Amazon Linux 2023..."

# Method 1: Try EPEL repository
echo "Method 1: Installing from EPEL repository..."
if sudo dnf install -y epel-release; then
    echo "✅ EPEL repository enabled"
    
    if sudo dnf install -y libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress; then
        echo "✅ LibreOffice installed successfully from EPEL"
        libreoffice --version
        exit 0
    else
        echo "❌ LibreOffice installation from EPEL failed"
    fi
else
    echo "❌ EPEL repository not available"
fi

# Method 2: Try CRB repository
echo "Method 2: Enabling CRB repository..."
if sudo dnf config-manager --set-enabled crb; then
    echo "✅ CRB repository enabled"
    
    if sudo dnf install -y libreoffice; then
        echo "✅ LibreOffice installed successfully from CRB"
        libreoffice --version
        exit 0
    else
        echo "❌ LibreOffice installation from CRB failed"
    fi
else
    echo "❌ CRB repository not available"
fi

# Method 3: Install Flatpak and LibreOffice via Flatpak
echo "Method 3: Installing via Flatpak..."
if sudo dnf install -y flatpak; then
    sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    
    if sudo flatpak install -y flathub org.libreoffice.LibreOffice; then
        echo "✅ LibreOffice installed successfully via Flatpak"
        echo "Note: Use 'flatpak run org.libreoffice.LibreOffice' to run LibreOffice"
        exit 0
    else
        echo "❌ LibreOffice installation via Flatpak failed"
    fi
else
    echo "❌ Flatpak installation failed"
fi

# Method 4: Install alternative document processing tools
echo "Method 4: Installing alternative document processing tools..."
sudo dnf install -y pandoc || echo "❌ Pandoc installation failed"

# Install Python document processing libraries
if [ -f "/opt/raganything/venv/bin/pip" ]; then
    echo "Installing Python document processing libraries..."
    sudo -u raganything /opt/raganything/venv/bin/pip install \
        python-docx \
        openpyxl \
        python-pptx \
        PyPDF2 \
        pdfplumber \
        Pillow
    
    echo "✅ Python document processing libraries installed"
else
    echo "❌ RAG Anything virtual environment not found"
fi

echo ""
echo "📋 LibreOffice Installation Summary:"
echo "If LibreOffice is still not available, you can:"
echo "1. Download LibreOffice manually from: https://www.libreoffice.org/download/download/"
echo "2. Use the installed Python libraries for basic document processing"
echo "3. Use pandoc for document conversion"
echo ""
echo "🔍 Check what's available:"
echo "  - LibreOffice: $(command -v libreoffice && echo 'Available' || echo 'Not available')"
echo "  - Pandoc: $(command -v pandoc && echo 'Available' || echo 'Not available')"
echo "  - Flatpak LibreOffice: $(flatpak list | grep -q libreoffice && echo 'Available' || echo 'Not available')"