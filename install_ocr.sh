#!/bin/bash

# OCR Installation Script for College Community API
# Installs Tesseract and Poppler for image-based PDF processing

set -e

echo "========================================="
echo "OCR Setup for College Community API"
echo "========================================="
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# Install based on OS
if [ "$OS" == "macos" ]; then
    echo "📦 Installing dependencies via Homebrew..."
    
    # Check if brew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is not installed. Please install it from https://brew.sh/"
        exit 1
    fi
    
    echo "Installing Tesseract OCR..."
    brew install tesseract || echo "Tesseract might already be installed"
    
    echo "Installing Poppler..."
    brew install poppler || echo "Poppler might already be installed"
    
elif [ "$OS" == "linux" ]; then
    echo "📦 Installing dependencies via apt-get..."
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        SUDO="sudo"
    else
        SUDO=""
    fi
    
    echo "Updating package list..."
    $SUDO apt-get update
    
    echo "Installing Tesseract OCR..."
    $SUDO apt-get install -y tesseract-ocr tesseract-ocr-eng
    
    echo "Installing Poppler utilities..."
    $SUDO apt-get install -y poppler-utils
fi

echo ""
echo "========================================="
echo "Verifying Installation"
echo "========================================="
echo ""

# Verify Tesseract
echo "Checking Tesseract..."
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract installed successfully"
    tesseract --version | head -n 1
else
    echo "❌ Tesseract not found in PATH"
    exit 1
fi

echo ""

# Verify Poppler
echo "Checking Poppler..."
if command -v pdftoppm &> /dev/null; then
    echo "✅ Poppler installed successfully"
    pdftoppm -v 2>&1 | head -n 1
else
    echo "❌ Poppler not found in PATH"
    exit 1
fi

echo ""

# Install Python packages
echo "========================================="
echo "Installing Python Dependencies"
echo "========================================="
echo ""

if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
    PIP_CMD=$(command -v pip3 || command -v pip)
    echo "Using pip: $PIP_CMD"
    
    echo "Installing Python OCR packages..."
    $PIP_CMD install pytesseract pdf2image Pillow
    
    echo ""
    echo "✅ Python packages installed"
else
    echo "⚠️  pip not found. Please install Python packages manually:"
    echo "   pip install pytesseract pdf2image Pillow"
fi

echo ""
echo "========================================="
echo "✅ Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Restart your application server"
echo "2. Upload an image-based PDF to test OCR"
echo "3. Check logs for OCR processing messages"
echo ""
echo "For more information, see OCR_SETUP.md"
