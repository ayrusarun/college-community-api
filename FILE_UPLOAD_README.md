# File Upload API Documentation

## Overview
The File Upload API provides comprehensive file management capabilities for the College Community platform, allowing users to upload, store, organize, and retrieve files by department and college.

## Features

### ✅ Current Implementation
- **File Upload**: Upload files with multiple format support
- **File Storage**: Organized by department and college
- **File Retrieval**: Get file lists with filtering and pagination
- **File Download**: Download files with proper MIME types
- **File Management**: Update descriptions, delete files
- **Security**: College-isolated access, user authentication
- **Statistics**: File usage analytics and department summaries

### 🚀 Upcoming Features
- **Vector Database Integration**: Store file content in vector database
- **AI Search**: Semantic search across file contents
- **ChatGPT Integration**: Generate answers from file content
- **File Content Extraction**: Extract text from PDFs, DOCs, etc.

## API Endpoints

### Authentication Required
All file endpoints require authentication via Bearer token.

### Upload File
```
POST /files/upload
```
**Form Data:**
- `file`: File to upload (required)
- `description`: Optional file description

**Supported File Types:**
- Documents: PDF, DOC, DOCX
- Presentations: PPT, PPTX
- Spreadsheets: XLS, XLSX, CSV
- Images: JPG, JPEG, PNG, GIF, BMP
- Videos: MP4, AVI, MOV, WMV, FLV
- Audio: MP3, WAV, FLAC, AAC
- Archives: ZIP, RAR, 7Z, TAR, GZ
- Text: TXT, MD, JSON, XML

**Limits:**
- Maximum file size: 50MB
- Files are organized by user's department
- College-specific storage isolation

**Response:**
```json
{
  "id": 1,
  "filename": "uuid-generated-name.pdf",
  "original_filename": "study_notes.pdf",
  "file_size": 1048576,
  "file_type": "DOCUMENT",
  "mime_type": "application/pdf",
  "department": "Computer Science & Engineering",
  "college_id": 1,
  "uploaded_by": 5,
  "upload_metadata": {
    "downloads": 0,
    "views": 0
  },
  "created_at": "2024-01-15T10:30:00",
  "uploader_name": "John Doe",
  "college_name": "IIT Madras"
}
```

### Get Files List
```
GET /files/
```
**Query Parameters:**
- `department`: Filter by department (optional)
- `file_type`: Filter by file type (optional)
- `search_term`: Search in filename and description (optional)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "files": [...],
  "total_count": 45,
  "page": 1,
  "page_size": 20
}
```

### Get File Details
```
GET /files/{file_id}
```
**Response:** Single file object with incremented view count

### Download File
```
GET /files/{file_id}/download
```
**Response:** File download with proper Content-Type and filename
- Increments download counter
- Returns original filename
- Proper MIME type for browser handling

### Update File
```
PUT /files/{file_id}
```
**Body:**
```json
{
  "description": "Updated file description"
}
```
**Note:** Only the file uploader can update their files

### Delete File
```
DELETE /files/{file_id}
```
**Note:** Only the file uploader can delete their files
- Removes file from disk
- Removes database record

### Get Departments List
```
GET /files/departments/list
```
**Response:**
```json
{
  "departments": [
    "Computer Science & Engineering",
    "Mechanical Engineering",
    "Electronics & Communication"
  ]
}
```

### Get File Statistics
```
GET /files/stats/summary
```
**Response:**
```json
{
  "total_files": 150,
  "total_size_bytes": 157286400,
  "total_size_mb": 150.0,
  "departments": {
    "Computer Science & Engineering": 45,
    "Mechanical Engineering": 32,
    "Electronics & Communication": 28
  },
  "file_types": {
    "DOCUMENT": 89,
    "PRESENTATION": 25,
    "IMAGE": 20,
    "SPREADSHEET": 16
  }
}
```

## File Organization Structure

```
uploads/
├── computer_science_&_engineering/
│   ├── uuid1.pdf
│   ├── uuid2.docx
│   └── uuid3.pptx
├── mechanical_engineering/
│   ├── uuid4.pdf
│   └── uuid5.xlsx
└── electronics_&_communication/
    ├── uuid6.jpg
    └── uuid7.zip
```

## Security Features

### College Isolation
- Users can only access files from their college
- File uploads are automatically associated with user's college
- Cross-college file access is prevented

### User Permissions
- Users can upload files to their department
- Only file uploaders can update/delete their files
- All users in the college can view and download files

### File Validation
- Extension whitelist enforcement
- File size limits
- MIME type validation
- Unique filename generation to prevent conflicts

## Database Schema

### Files Table
```sql
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,           -- UUID-based unique filename
    original_filename VARCHAR(255) NOT NULL, -- User's original filename
    file_path VARCHAR(500) NOT NULL,         -- Full path on disk
    file_size INTEGER NOT NULL,              -- Size in bytes
    file_type VARCHAR(20) NOT NULL,          -- Enum: DOCUMENT, IMAGE, etc.
    mime_type VARCHAR(100) NOT NULL,         -- Content-Type
    description TEXT,                        -- Optional description
    department VARCHAR(100) NOT NULL,        -- User's department
    college_id INTEGER NOT NULL,             -- College association
    uploaded_by INTEGER NOT NULL,            -- User who uploaded
    upload_metadata JSON DEFAULT '{"downloads": 0, "views": 0}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (college_id) REFERENCES colleges(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);
```

### Indexes
- `department`: Fast filtering by department
- `college_id`: College isolation queries
- `created_at`: Chronological sorting
- `file_type`: File type filtering

## Testing

### Running Tests
```bash
# Make sure API server is running
python -m uvicorn app.main:app --reload

# Run file upload tests
chmod +x test_files.sh
./test_files.sh
```

### Test Coverage
- File upload validation
- Authentication checks
- File listing and filtering
- File download functionality
- File update and deletion
- Statistics and analytics

## Setup Instructions

### 1. Install Dependencies
```bash
pip install aiofiles
```

### 2. Run Database Migration
```bash
python migrate_add_files.py
```

### 3. Create Upload Directory
```bash
mkdir -p uploads
```

### 4. Update Environment
Ensure proper permissions for file upload directory:
```bash
chmod 755 uploads
```

## Error Handling

### Common Errors
- `400 Bad Request`: Invalid file type or missing file
- `413 Payload Too Large`: File exceeds 50MB limit
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions (update/delete)
- `404 Not Found`: File not found or access denied
- `500 Internal Server Error`: File system or database error

### Error Response Format
```json
{
  "detail": "File type not allowed. Allowed extensions: .pdf, .doc, ..."
}
```

## Next Steps: AI Integration

The file upload system is designed to support upcoming AI features:

1. **Vector Database**: Store file content as embeddings
2. **Content Extraction**: Extract text from various file formats
3. **Semantic Search**: Find relevant files using natural language
4. **AI Answers**: Generate contextual responses using ChatGPT and file content

This foundation provides the necessary infrastructure for advanced AI-powered document search and retrieval capabilities.