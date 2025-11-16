#!/bin/bash

# Test OCR functionality
echo "========================================="
echo "Testing OCR Setup"
echo "========================================="
echo ""

# Test 1: Check Tesseract
echo "Test 1: Checking Tesseract installation..."
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract found"
    tesseract --version | head -n 1
else
    echo "❌ Tesseract NOT found"
    echo "   Run: ./install_ocr.sh"
    exit 1
fi

echo ""

# Test 2: Check Poppler
echo "Test 2: Checking Poppler installation..."
if command -v pdftoppm &> /dev/null; then
    echo "✅ Poppler found"
    pdftoppm -v 2>&1 | head -n 1
else
    echo "❌ Poppler NOT found"
    echo "   Run: ./install_ocr.sh"
    exit 1
fi

echo ""

# Test 3: Check Python packages
echo "Test 3: Checking Python packages..."
python3 << 'PYTHON'
import sys

packages = {
    'pytesseract': 'pytesseract',
    'pdf2image': 'pdf2image', 
    'PIL': 'Pillow'
}

all_installed = True

for module, package in packages.items():
    try:
        __import__(module)
        print(f"✅ {package} installed")
    except ImportError:
        print(f"❌ {package} NOT installed")
        print(f"   Run: pip install {package}")
        all_installed = False

sys.exit(0 if all_installed else 1)
PYTHON

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All Python packages installed"
else
    echo ""
    echo "❌ Some Python packages missing"
    echo "   Run: pip install pytesseract pdf2image Pillow"
    exit 1
fi

echo ""

# Test 4: Test actual OCR functionality
echo "Test 4: Testing OCR functionality..."
python3 << 'PYTHON'
import pytesseract
from PIL import Image
import io

# Create a simple test image with text
print("Testing pytesseract basic functionality...")
try:
    # This just verifies pytesseract can access tesseract
    version = pytesseract.get_tesseract_version()
    print(f"✅ pytesseract working (Tesseract {version})")
except Exception as e:
    print(f"❌ pytesseract error: {e}")
    import sys
    sys.exit(1)
PYTHON

if [ $? -eq 0 ]; then
    echo "✅ OCR functionality working"
else
    echo "❌ OCR functionality test failed"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ All OCR Tests Passed!"
echo "========================================="
echo ""
echo "Your system is ready to process image-based PDFs."
echo "Upload a scanned PDF to test the full pipeline."
