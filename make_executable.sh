#!/bin/bash

# Make all scripts executable (only if they exist)
echo "🔧 Making scripts executable..."

if [ -f "deploy_amazon_linux_2023.sh" ]; then
    chmod +x deploy_amazon_linux_2023.sh
    echo "✅ deploy_amazon_linux_2023.sh is now executable"
else
    echo "⚠️  deploy_amazon_linux_2023.sh not found"
fi

if [ -f "test_complete_rag.py" ]; then
    chmod +x test_complete_rag.py
    echo "✅ test_complete_rag.py is now executable"
else
    echo "⚠️  test_complete_rag.py not found"
fi

if [ -f "amazon_linux_setup.sh" ]; then
    chmod +x amazon_linux_setup.sh
    echo "✅ amazon_linux_setup.sh is now executable"
else
    echo "⚠️  amazon_linux_setup.sh not found"
fi

if [ -f "test_bedrock_setup.py" ]; then
    chmod +x test_bedrock_setup.py
    echo "✅ test_bedrock_setup.py is now executable"
else
    echo "⚠️  test_bedrock_setup.py not found"
fi

echo ""
echo "📁 Available files in current directory:"
ls -la *.sh *.py 2>/dev/null || echo "   No .sh or .py files found"

echo ""
echo "🚀 To deploy on Amazon Linux 2023, run:"
echo "   ./deploy_amazon_linux_2023.sh"
echo ""
echo "📖 For detailed instructions, see:"
echo "   cat AMAZON_LINUX_2023_SETUP.md"