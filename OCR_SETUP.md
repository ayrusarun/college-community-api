# OCR Setup for Image-based PDF Processing

## Overview

The system now supports extracting text from image-based PDFs (scanned documents, PDFs with images containing text) using Optical Character Recognition (OCR).

## How It Works

1. **Text PDFs**: For PDFs with actual text content, `PyPDF2` extracts text directly (fast)
2. **Image-based PDFs**: If no text is found, the system automatically tries OCR using:
   - `pdf2image`: Converts PDF pages to images
   - `pytesseract`: Performs OCR on the images
   - `Pillow`: Image processing library

## System Requirements

### 1. Install System Dependencies

#### macOS
```bash
# Install Tesseract OCR engine
brew install tesseract

# Install poppler (required by pdf2image)
brew install poppler
```

#### Ubuntu/Debian Linux
```bash
# Install Tesseract OCR engine
sudo apt-get update
sudo apt-get install -y tesseract-ocr

# Install poppler utilities
sudo apt-get install -y poppler-utils
```

#### Docker (Production)
Add to your Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `pytesseract==0.3.10` - Python wrapper for Tesseract
- `pdf2image==1.16.3` - PDF to image conversion
- `Pillow==10.1.0` - Image processing

## Verification

### Check Tesseract Installation
```bash
tesseract --version
```

You should see output like:
```
tesseract 5.x.x
```

### Check Poppler Installation
```bash
pdftoppm -v
```

### Test OCR in Python
```python
import pytesseract
from pdf2image import convert_from_path

# This should not raise any errors if properly installed
print("OCR libraries available!")
```

## Usage

The OCR functionality is **automatic**. When a PDF is uploaded:

1. System first tries to extract text using `PyPDF2`
2. If no text is found (empty or minimal text), it automatically tries OCR
3. OCR converts each PDF page to an image and extracts text
4. Extracted text is then vectorized for AI search

## Performance Considerations

### Speed
- **Text PDFs**: Very fast (< 1 second)
- **Image PDFs with OCR**: Slower (5-30 seconds per page depending on quality and size)

### Recommendations
1. **DPI Setting**: Currently set to 300 DPI (good balance of quality/speed)
2. **Background Processing**: OCR runs as a background task, doesn't block the upload
3. **Large Documents**: For PDFs with many pages, consider:
   - Processing first N pages only
   - Lower DPI (200) for faster processing
   - Batch processing with queue

## Monitoring

### Check Indexing Status

```bash
# Test the AI stats endpoint
curl -X GET "http://localhost:8000/ai/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### View Logs

The system logs OCR activity:
```
INFO: Extracting text from PDF with 5 pages: /path/to/file.pdf
WARNING: No text extracted from PDF using PyPDF2: /path/to/file.pdf
INFO: Attempting OCR extraction for image-based PDF: /path/to/file.pdf
INFO: Converting PDF to images for OCR: /path/to/file.pdf
INFO: Processing 5 pages with OCR
INFO: Performing OCR on page 1/5
INFO: OCR extraction completed. Extracted 1234 characters from 5 pages
INFO: Successfully indexed file 42: scanned_document.pdf
```

## Troubleshooting

### Issue: "pytesseract.TesseractNotFoundError"
**Solution**: Tesseract is not installed or not in PATH
```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr
```

### Issue: "PDFInfoNotInstalledError"
**Solution**: Poppler is not installed
```bash
# macOS
brew install poppler

# Ubuntu
sudo apt-get install poppler-utils
```

### Issue: OCR produces gibberish
**Solution**: 
- Ensure PDF image quality is good (not too compressed)
- Try different DPI settings (200-400)
- Check if the document is in English (default language)

### Issue: OCR is too slow
**Solution**:
- Reduce DPI from 300 to 200
- Process fewer pages
- Consider implementing page limits for very large documents

## Language Support

By default, OCR uses English (`lang='eng'`). To add more languages:

### Install Additional Languages
```bash
# macOS
brew install tesseract-lang

# Ubuntu - example for Hindi
sudo apt-get install tesseract-ocr-hin
```

### Modify Code (if needed)
In `ai_service.py`, line with `pytesseract.image_to_string`:
```python
# For Hindi
page_text = pytesseract.image_to_string(image, lang='hin')

# For multiple languages
page_text = pytesseract.image_to_string(image, lang='eng+hin')
```

## Docker Deployment

Add to your `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Rest of your Dockerfile...
```

## Testing

### Upload an Image-based PDF

1. Create or download a scanned PDF (image-based)
2. Upload via the API:
```bash
curl -X POST "http://localhost:8000/files/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@scanned_document.pdf" \
  -F "description=Test OCR document"
```

3. Check the logs for OCR activity
4. Query the AI to verify the content was indexed:
```bash
curl -X POST "http://localhost:8000/ai/ask" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What information is in the scanned document?",
    "context_filter": "files"
  }'
```

## Cost Considerations

OCR is computationally intensive:
- **CPU**: Higher usage during OCR processing
- **Memory**: Images can use significant RAM
- **Storage**: Temporary image files (auto-cleaned)
- **Time**: Background tasks take longer

Consider implementing:
- Rate limiting for file uploads
- Queue system for large batch processing
- Caching of OCR results
- File size limits for OCR-enabled uploads

## Future Enhancements

Potential improvements:
1. **Parallel page processing**: Process multiple pages simultaneously
2. **Image preprocessing**: Enhance image quality before OCR
3. **Confidence scores**: Track OCR accuracy
4. **Manual retry**: Allow users to retry failed OCR
5. **Multi-language detection**: Auto-detect document language
6. **Table extraction**: Extract structured data from tables
7. **Handwriting recognition**: Support handwritten documents

## Summary

✅ **Automatic fallback**: Text extraction → OCR if needed  
✅ **No user intervention**: Works transparently  
✅ **Background processing**: Doesn't block uploads  
✅ **Logging**: Full visibility into OCR operations  
✅ **Production ready**: Works in Docker containers  

For questions or issues, check the logs or contact the development team.
