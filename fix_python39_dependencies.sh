#!/bin/bash

# Quick fix for Python 3.9 dependency issues
# Addresses MinerU compatibility and version conflicts

echo "🔧 Fixing Python 3.9 dependency issues..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected. Activating..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ No virtual environment found. Please run the setup script first."
        exit 1
    fi
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == "3.9" ]]; then
    echo "🔧 Applying Python 3.9 compatibility fixes..."
    
    # Remove problematic packages
    echo "Removing incompatible packages..."
    pip uninstall -y mineru || true
    
    # Install Python 3.9 compatible alternatives
    echo "Installing Python 3.9 compatible document processors..."
    pip install --no-cache-dir \
        "PyPDF2>=3.0.0,<4.0" \
        "pdfplumber>=0.7.0,<1.0" \
        "python-docx>=0.8.11,<1.0" \
        "openpyxl>=3.0.9,<4.0" \
        "python-pptx>=0.6.21,<1.0"
    
    # Update requirements.txt to be Python 3.9 compatible
    if [ -f "requirements.txt" ]; then
        echo "Backing up and updating requirements.txt..."
        cp requirements.txt requirements.txt.backup
        
        # Create Python 3.9 compatible requirements
        cat > requirements.txt << 'EOF'
huggingface_hub>=0.16.0,<1.0
lightrag-hku>=1.0.0,<2.0
# Document processing (Python 3.9 compatible)
PyPDF2>=3.0.0,<4.0
pdfplumber>=0.7.0,<1.0
python-docx>=0.8.11,<1.0
openpyxl>=3.0.9,<4.0
python-pptx>=0.6.21,<1.0
tqdm>=4.60.0,<5.0
# AWS Bedrock integration
boto3>=1.34.0,<2.0
botocore>=1.34.0,<2.0
python-dotenv>=1.0.0,<2.0
asyncio-throttle>=1.0.0,<2.0
tenacity>=8.0.0,<9.0
# Optional dependencies
Pillow>=9.0.0,<11.0
reportlab>=3.6.0,<5.0
EOF
        echo "✅ Requirements.txt updated for Python 3.9"
    fi
    
    # Reinstall the package
    echo "Reinstalling RAG Anything with Python 3.9 compatible dependencies..."
    pip install -e . --no-cache-dir --force-reinstall
    
    # Update .env for Python 3.9 compatibility
    if [ -f ".env" ]; then
        echo "Updating .env for Python 3.9 compatibility..."
        
        # Add Python 3.9 specific settings
        if ! grep -q "PARSER=pypdf2" .env; then
            sed -i 's/PARSER=mineru/PARSER=pypdf2/' .env || echo "PARSER=pypdf2" >> .env
        fi
        
        if ! grep -q "ENABLE_TABLE_PROCESSING=false" .env; then
            sed -i 's/ENABLE_TABLE_PROCESSING=true/ENABLE_TABLE_PROCESSING=false/' .env || echo "ENABLE_TABLE_PROCESSING=false" >> .env
        fi
        
        if ! grep -q "ENABLE_EQUATION_PROCESSING=false" .env; then
            sed -i 's/ENABLE_EQUATION_PROCESSING=true/ENABLE_EQUATION_PROCESSING=false/' .env || echo "ENABLE_EQUATION_PROCESSING=false" >> .env
        fi
        
        # Add Python 3.9 marker
        if ! grep -q "PYTHON_VERSION=3.9" .env; then
            echo "PYTHON_VERSION=3.9" >> .env
            echo "USE_LEGACY_PARSERS=true" >> .env
        fi
        
        echo "✅ .env updated for Python 3.9"
    fi
    
else
    echo "⚠️  Python version is $PYTHON_VERSION, not 3.9. This fix is specifically for Python 3.9."
    echo "Consider using the comprehensive_rag_setup.sh script instead."
fi

# Test the installation
echo "🧪 Testing the fixed installation..."
python -c "
import sys
print(f'Python version: {sys.version}')

try:
    from raganything import RAGAnythingConfig
    from raganything.bedrock import BedrockConfig
    from raganything.bedrock_rag import BedrockRAGAnything
    print('✅ All imports successful!')
    
    # Test configuration
    rag_config = RAGAnythingConfig(
        working_dir='./test_storage',
        parser='pypdf2',
        parse_method='auto'
    )
    bedrock_config = BedrockConfig.from_env()
    print('✅ Configuration test successful!')
    
except Exception as e:
    print(f'❌ Test failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Python 3.9 compatibility fix completed successfully!"
    echo ""
    echo "📋 What was fixed:"
    echo "   - Removed MinerU (requires Python 3.10+)"
    echo "   - Installed PyPDF2 and other Python 3.9 compatible parsers"
    echo "   - Updated requirements.txt for compatibility"
    echo "   - Modified .env for Python 3.9 optimizations"
    echo "   - Disabled advanced features that require newer Python"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Test: python test_python39_rag.py (if available)"
    echo "   2. Try: python examples/bedrock_basic_example.py"
    echo ""
    echo "⚠️  Note: Some advanced document processing features are limited on Python 3.9"
else
    echo "❌ Fix failed. You may need to run the full Python 3.9 setup script:"
    echo "   chmod +x python39_compatible_setup.sh"
    echo "   ./python39_compatible_setup.sh"
fi