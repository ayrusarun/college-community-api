# Folder Structure Feature Documentation

## Overview

The College Community API now supports hierarchical folder structures for file organization. Users can create folders, upload files to specific folders, browse folder contents, and manage their file organization efficiently.

## Database Changes

### New Columns in `files` Table

- **`folder_path`** (VARCHAR 1000): Virtual path representing the folder location (e.g., `/Documents/2024`)
- **`is_folder`** (BOOLEAN): Flag to distinguish between files and folders
- **`parent_folder_id`** (INTEGER): Optional reference to parent folder for hierarchical navigation

### Indexes

- `idx_files_folder_path`: Composite index on (folder_path, college_id) for fast folder queries
- `idx_files_parent_folder`: Index on parent_folder_id for hierarchical queries

## API Endpoints

### 1. Create Folder

**Endpoint:** `POST /files/folders/create`

**Description:** Create a new folder in the specified location

**Request Body:**
```json
{
  "name": "My Documents",
  "parent_path": "/",
  "description": "Personal documents folder"
}
```

**Response:**
```json
{
  "id": 123,
  "name": "My Documents",
  "path": "/My Documents",
  "message": "Folder created successfully"
}
```

**Notes:**
- Folder names cannot contain `/` character
- Folders are created at the department level (user's department)
- Duplicate folder names in the same location are not allowed

---

### 2. Browse Folder Contents

**Endpoint:** `GET /files/folders/browse?folder_path=/path/to/folder`

**Description:** Get all folders and files in a specific folder with navigation breadcrumbs

**Query Parameters:**
- `folder_path` (optional, default: "/"): Path of folder to browse

**Response:**
```json
{
  "current_path": "/Documents",
  "parent_path": "/",
  "folders": [
    {
      "id": 456,
      "name": "2024",
      "path": "/Documents/2024",
      "is_folder": true,
      "file_type": null,
      "file_size": 0,
      "file_count": 15,
      "created_at": "2024-11-16T10:00:00Z",
      "updated_at": "2024-11-16T10:00:00Z",
      "uploader_name": "John Doe",
      "description": "Documents from 2024"
    }
  ],
  "files": [
    {
      "id": 789,
      "name": "report.pdf",
      "path": "/Documents",
      "is_folder": false,
      "file_type": "DOCUMENT",
      "file_size": 1024000,
      "file_count": 0,
      "created_at": "2024-11-16T09:00:00Z",
      "updated_at": "2024-11-16T09:00:00Z",
      "uploader_name": "Jane Smith",
      "description": "Annual report"
    }
  ],
  "total_items": 2,
  "breadcrumbs": [
    {"name": "Home", "path": "/"},
    {"name": "Documents", "path": "/Documents"}
  ]
}
```

**Features:**
- Returns only direct children (one level deep)
- File count in folders is recursive (includes subfolders)
- Breadcrumbs for easy navigation
- Parent path for "up" navigation

---

### 3. Upload File with Folder Path

**Endpoint:** `POST /files/upload`

**Description:** Upload a file to a specific folder

**Form Data:**
- `file` (required): File to upload
- `description` (optional): File description
- `folder_path` (optional, default: "/"): Destination folder path

**Example using cURL:**
```bash
curl -X POST "http://your-api/files/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "folder_path=/Documents/2024" \
  -F "description=Important document"
```

**Response:**
```json
{
  "id": 101,
  "filename": "abc-123-def.pdf",
  "original_filename": "document.pdf",
  "file_size": 2048000,
  "file_type": "DOCUMENT",
  "mime_type": "application/pdf",
  "department": "Computer Science",
  "college_id": 1,
  "uploaded_by": 5,
  "upload_metadata": {"downloads": 0, "views": 0},
  "created_at": "2024-11-16T12:00:00Z",
  "folder_path": "/Documents/2024",
  "is_folder": false,
  "uploader_name": "John Doe",
  "college_name": "MIT"
}
```

---

### 4. Upload Post Image with Folder

**Endpoint:** `POST /files/posts/upload-image`

**Description:** Upload an image for posts with optional folder organization

**Form Data:**
- `file` (required): Image file
- `folder_path` (optional, default: "/posts"): Destination folder

**Response:**
```json
{
  "id": 202,
  "filename": "xyz-456-abc.jpg",
  "original_filename": "photo.jpg",
  "file_size": 512000,
  "mime_type": "image/jpeg",
  "folder_path": "/posts/events",
  "public_url": "/files/posts/image/xyz-456-abc.jpg",
  "full_url": "http://195.35.20.155:8000/files/posts/image/xyz-456-abc.jpg",
  "message": "Post image uploaded successfully"
}
```

---

### 5. Get Files with Folder Filter

**Endpoint:** `GET /files/?folder_path=/path&page=1&page_size=20`

**Description:** Get files with optional folder path filtering

**Query Parameters:**
- `folder_path` (optional): Filter files in specific folder
- `department` (optional): Filter by department
- `file_type` (optional): Filter by file type
- `search_term` (optional): Search in filename/description
- `page` (default: 1): Page number
- `page_size` (default: 20): Items per page

**Response:**
```json
{
  "files": [...],
  "total_count": 45,
  "page": 1,
  "page_size": 20
}
```

---

### 6. Delete Folder

**Endpoint:** `DELETE /files/folders/delete?folder_path=/path&recursive=false`

**Description:** Delete a folder (optionally with all contents)

**Query Parameters:**
- `folder_path` (required): Path of folder to delete
- `recursive` (optional, default: false): Delete folder and all contents

**Response:**
```json
{
  "message": "Folder deleted successfully",
  "deleted_files": 15,
  "deleted_folders": 3
}
```

**Notes:**
- Only folder creator can delete it
- Root folder "/" cannot be deleted
- Non-empty folders require `recursive=true`

---

### 7. Move Folder

**Endpoint:** `PUT /files/folders/move?source_path=/old/path&destination_path=/new/parent`

**Description:** Move a folder to a different location

**Query Parameters:**
- `source_path` (required): Current folder path
- `destination_path` (required): New parent folder path

**Response:**
```json
{
  "message": "Folder moved successfully",
  "old_path": "/Documents/Old",
  "new_path": "/Archives/Old",
  "items_updated": 25
}
```

**Notes:**
- Only folder creator can move it
- All files and subfolders are updated automatically
- Destination cannot already have a folder with the same name

---

## Frontend Integration Examples

### Creating a Folder

```javascript
async function createFolder(name, parentPath = '/') {
  const response = await fetch('/files/folders/create', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: name,
      parent_path: parentPath,
      description: 'Optional description'
    })
  });
  return await response.json();
}
```

### Browsing Folder

```javascript
async function browseFolder(folderPath = '/') {
  const response = await fetch(
    `/files/folders/browse?folder_path=${encodeURIComponent(folderPath)}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return await response.json();
}
```

### Uploading File to Folder

```javascript
async function uploadFileToFolder(file, folderPath = '/') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('folder_path', folderPath);
  formData.append('description', 'File description');
  
  const response = await fetch('/files/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  return await response.json();
}
```

### Rendering Breadcrumbs

```javascript
function renderBreadcrumbs(breadcrumbs) {
  return breadcrumbs.map((crumb, index) => {
    if (index === breadcrumbs.length - 1) {
      return `<span class="current">${crumb.name}</span>`;
    }
    return `<a href="#" onclick="browseFolder('${crumb.path}')">${crumb.name}</a> / `;
  }).join('');
}
```

---

## Migration Guide

### Step 1: Run Migration Script

```bash
python migrate_add_folders.py
```

This will:
- Add new columns to the `files` table
- Create indexes for performance
- Update existing files to root folder
- Create default folders for each college

### Step 2: Verify Migration

```bash
# Check if columns exist
psql -d college_community -c "\d files"

# Check existing folders
psql -d college_community -c "SELECT id, filename, folder_path, is_folder FROM files WHERE is_folder = TRUE;"
```

### Step 3: Update Application

The migration is backward compatible. Existing file upload/download functionality continues to work:
- Files without explicit `folder_path` default to "/"
- Existing files are assigned to root folder
- All existing endpoints continue to work

---

## Best Practices

### 1. Folder Naming

- Use clear, descriptive names
- Avoid special characters except spaces and hyphens
- Keep folder names under 50 characters
- Use consistent naming conventions (e.g., YYYY-MM for dates)

### 2. Folder Organization

```
/
├── Documents/
│   ├── 2024/
│   ├── 2023/
│   └── Archives/
├── Images/
│   ├── Events/
│   ├── Announcements/
│   └── Profile/
├── Videos/
│   └── Tutorials/
└── Resources/
    ├── Textbooks/
    └── Notes/
```

### 3. Access Control

- Folders inherit department-level access
- Only folder creator can delete/move folders
- All users in department can view folders
- Files maintain their own permissions

### 4. Performance Tips

- Use pagination when listing files
- Avoid deeply nested folders (3-4 levels max)
- Use search instead of browsing for large directories
- Cache folder structures on client side

---

## Common Use Cases

### 1. Department File Organization

```
/Syllabus/
/Assignments/
/Lectures/
/Resources/
/Student_Work/
```

### 2. Event Management

```
/Events/
├── 2024/
│   ├── Tech_Fest/
│   ├── Sports_Day/
│   └── Cultural_Night/
└── 2023/
```

### 3. Academic Year Structure

```
/Academic_Year_2024/
├── Semester_1/
│   ├── Assignments/
│   ├── Exams/
│   └── Notes/
└── Semester_2/
```

---

## Troubleshooting

### Folder Not Found

**Issue:** GET request returns 404 for existing folder
**Solution:** Ensure folder_path is properly normalized (starts with /, no trailing /)

### Duplicate Folder Error

**Issue:** Cannot create folder with same name
**Solution:** Check if folder exists in same location, or use different name

### Permission Denied

**Issue:** Cannot delete/move folder
**Solution:** Only the folder creator can perform these operations

### Empty Folder List

**Issue:** Browse returns no folders
**Solution:** Check if folders exist for the user's college_id and department

---

## Future Enhancements

- [ ] Folder sharing between departments
- [ ] Folder templates for quick setup
- [ ] Bulk file operations (move multiple files)
- [ ] Folder size quotas and limits
- [ ] Trash/recycle bin for deleted folders
- [ ] Folder activity logs
- [ ] Public folder links
- [ ] Folder permissions (read-only, etc.)

---

## Support

For issues or questions, please:
1. Check this documentation
2. Review API error messages
3. Check database migration logs
4. Contact the development team

---

**Last Updated:** November 16, 2024  
**Version:** 1.0.0  
**Author:** Development Team
