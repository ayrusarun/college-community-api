from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List
import os
import uuid
import mimetypes
from pathlib import Path

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import File as FileModel, User, College, FileType as FileTypeEnum, IndexingTask
from ..models.schemas import (
    FileUploadResponse, FileResponse, FileUpdate, FileListResponse, 
    FileSearchQuery, FileType
)

router = APIRouter(prefix="/files", tags=["files"])

# Configuration
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp",
    ".mp4", ".avi", ".mov", ".wmv", ".flv",
    ".mp3", ".wav", ".flac", ".aac",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".txt", ".md", ".csv", ".json", ".xml"
}

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_file_type(filename: str, mime_type: str) -> FileTypeEnum:
    """Determine file type based on extension and MIME type"""
    ext = Path(filename).suffix.lower()
    
    if ext in [".pdf", ".doc", ".docx"]:
        return FileTypeEnum.DOCUMENT
    elif ext in [".ppt", ".pptx"]:
        return FileTypeEnum.PRESENTATION
    elif ext in [".xls", ".xlsx", ".csv"]:
        return FileTypeEnum.SPREADSHEET
    elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
        return FileTypeEnum.IMAGE
    elif ext in [".mp4", ".avi", ".mov", ".wmv", ".flv"]:
        return FileTypeEnum.VIDEO
    elif ext in [".mp3", ".wav", ".flac", ".aac"]:
        return FileTypeEnum.AUDIO
    elif ext in [".zip", ".rar", ".7z", ".tar", ".gz"]:
        return FileTypeEnum.ARCHIVE
    elif ext in [".txt", ".md", ".json", ".xml"]:
        return FileTypeEnum.TEXT
    else:
        return FileTypeEnum.OTHER


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving the extension"""
    file_ext = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_ext}"


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file to the system"""
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content to check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Create department-specific subdirectory
    dept_dir = os.path.join(UPLOAD_DIR, current_user.department.replace(" ", "_").lower())
    os.makedirs(dept_dir, exist_ok=True)
    file_path = os.path.join(dept_dir, unique_filename)
    
    # Save file to disk
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Determine MIME type
    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    
    # Create file record in database
    db_file = FileModel(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=get_file_type(file.filename, mime_type),
        mime_type=mime_type,
        description=description,
        department=current_user.department,
        college_id=current_user.college_id,
        uploaded_by=current_user.id,
        upload_metadata={"downloads": 0, "views": 0}
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Create indexing task for AI
    try:
        indexing_task = IndexingTask(
            content_type="file",
            content_id=db_file.id,
            college_id=current_user.college_id,
            status="pending"
        )
        db.add(indexing_task)
        db.commit()
        
        # Add background task for indexing
        from .ai import process_file_indexing
        background_tasks.add_task(
            process_file_indexing,
            db_file.id,
            current_user.college_id
        )
    except Exception as e:
        # Log error but don't fail upload
        print(f"Error creating indexing task for file {db_file.id}: {e}")
    
    # Get additional info for response
    college = db.query(College).filter(College.id == current_user.college_id).first()
    
    return FileUploadResponse(
        id=db_file.id,
        filename=db_file.filename,
        original_filename=db_file.original_filename,
        file_size=db_file.file_size,
        file_type=db_file.file_type,
        mime_type=db_file.mime_type,
        department=db_file.department,
        college_id=db_file.college_id,
        uploaded_by=db_file.uploaded_by,
        upload_metadata=db_file.upload_metadata,
        created_at=db_file.created_at,
        uploader_name=current_user.full_name,
        college_name=college.name if college else "Unknown"
    )


@router.get("/", response_model=FileListResponse)
async def get_files(
    department: Optional[str] = Query(None, description="Filter by department"),
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    search_term: Optional[str] = Query(None, description="Search in filename and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get files with filtering and pagination (college-specific)"""
    
    # Base query - only files from user's college
    query = db.query(FileModel).filter(FileModel.college_id == current_user.college_id)
    
    # Apply filters
    if department:
        query = query.filter(FileModel.department == department)
    
    if file_type:
        # Convert string enum to database enum
        file_type_enum = FileTypeEnum(file_type.value)
        query = query.filter(FileModel.file_type == file_type_enum)
    
    if search_term:
        search_filter = or_(
            FileModel.original_filename.ilike(f"%{search_term}%"),
            FileModel.description.ilike(f"%{search_term}%")
        )
        query = query.filter(search_filter)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    files = query.order_by(FileModel.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Build response with additional info
    file_responses = []
    for file in files:
        uploader = db.query(User).filter(User.id == file.uploaded_by).first()
        college = db.query(College).filter(College.id == file.college_id).first()
        
        file_responses.append(FileResponse(
            id=file.id,
            filename=file.filename,
            original_filename=file.original_filename,
            file_size=file.file_size,
            file_type=file.file_type,
            mime_type=file.mime_type,
            description=file.description,
            department=file.department,
            college_id=file.college_id,
            uploaded_by=file.uploaded_by,
            upload_metadata=file.upload_metadata,
            created_at=file.created_at,
            updated_at=file.updated_at,
            uploader_name=uploader.full_name if uploader else "Unknown",
            college_name=college.name if college else "Unknown"
        ))
    
    return FileListResponse(
        files=file_responses,
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_details(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific file"""
    
    # Get file (must be from user's college)
    file = db.query(FileModel).filter(
        and_(
            FileModel.id == file_id,
            FileModel.college_id == current_user.college_id
        )
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Increment view count
    metadata = file.upload_metadata.copy()
    metadata["views"] = metadata.get("views", 0) + 1
    file.upload_metadata = metadata
    db.commit()
    
    # Get additional info
    uploader = db.query(User).filter(User.id == file.uploaded_by).first()
    college = db.query(College).filter(College.id == file.college_id).first()
    
    return FileResponse(
        id=file.id,
        filename=file.filename,
        original_filename=file.original_filename,
        file_size=file.file_size,
        file_type=file.file_type,
        mime_type=file.mime_type,
        description=file.description,
        department=file.department,
        college_id=file.college_id,
        uploaded_by=file.uploaded_by,
        upload_metadata=file.upload_metadata,
        created_at=file.created_at,
        updated_at=file.updated_at,
        uploader_name=uploader.full_name if uploader else "Unknown",
        college_name=college.name if college else "Unknown"
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a file"""
    
    # Get file (must be from user's college)
    file = db.query(FileModel).filter(
        and_(
            FileModel.id == file_id,
            FileModel.college_id == current_user.college_id
        )
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file exists on disk
    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Increment download count
    metadata = file.upload_metadata.copy()
    metadata["downloads"] = metadata.get("downloads", 0) + 1
    file.upload_metadata = metadata
    db.commit()
    
    return FastAPIFileResponse(
        path=file.file_path,
        filename=file.original_filename,
        media_type=file.mime_type
    )


@router.get("/{file_id}/view")
async def view_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View/serve a file directly (for images, videos, etc.) - authenticated access"""
    
    # Get file (must be from user's college)
    file = db.query(FileModel).filter(
        and_(
            FileModel.id == file_id,
            FileModel.college_id == current_user.college_id
        )
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file exists on disk
    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Increment view count (separate from downloads)
    metadata = file.upload_metadata.copy()
    metadata["views"] = metadata.get("views", 0) + 1
    file.upload_metadata = metadata
    db.commit()
    
    return FastAPIFileResponse(
        path=file.file_path,
        media_type=file.mime_type
    )





@router.put("/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: int,
    file_update: FileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update file metadata (only by the uploader or admin)"""
    
    # Get file
    file = db.query(FileModel).filter(
        and_(
            FileModel.id == file_id,
            FileModel.college_id == current_user.college_id
        )
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions (only uploader can update)
    if file.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this file")
    
    # Update fields
    if file_update.description is not None:
        file.description = file_update.description
    
    db.commit()
    db.refresh(file)
    
    # Get additional info for response
    uploader = db.query(User).filter(User.id == file.uploaded_by).first()
    college = db.query(College).filter(College.id == file.college_id).first()
    
    return FileResponse(
        id=file.id,
        filename=file.filename,
        original_filename=file.original_filename,
        file_size=file.file_size,
        file_type=file.file_type,
        mime_type=file.mime_type,
        description=file.description,
        department=file.department,
        college_id=file.college_id,
        uploaded_by=file.uploaded_by,
        upload_metadata=file.upload_metadata,
        created_at=file.created_at,
        updated_at=file.updated_at,
        uploader_name=uploader.full_name if uploader else "Unknown",
        college_name=college.name if college else "Unknown"
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file (only by the uploader or admin)"""
    
    # Get file
    file = db.query(FileModel).filter(
        and_(
            FileModel.id == file_id,
            FileModel.college_id == current_user.college_id
        )
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions (only uploader can delete)
    if file.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")
    
    # Delete file from disk
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        # Log the error but continue with database deletion
        print(f"Error deleting file from disk: {e}")
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    return {"message": "File deleted successfully"}


@router.get("/departments/list")
async def get_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of departments that have uploaded files in the user's college"""
    
    departments = db.query(FileModel.department).filter(
        FileModel.college_id == current_user.college_id
    ).distinct().all()
    
    return {"departments": [dept[0] for dept in departments]}


@router.get("/stats/summary")
async def get_file_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file statistics for the user's college"""
    
    # Total files in college
    total_files = db.query(FileModel).filter(
        FileModel.college_id == current_user.college_id
    ).count()
    
    # Files by department
    dept_stats = db.query(
        FileModel.department,
        func.count(FileModel.id).label("count")
    ).filter(
        FileModel.college_id == current_user.college_id
    ).group_by(FileModel.department).all()
    
    # Files by type
    type_stats = db.query(
        FileModel.file_type,
        func.count(FileModel.id).label("count")
    ).filter(
        FileModel.college_id == current_user.college_id
    ).group_by(FileModel.file_type).all()
    
    # Total size
    total_size = db.query(
        func.sum(FileModel.file_size)
    ).filter(
        FileModel.college_id == current_user.college_id
    ).scalar() or 0
    
    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "departments": {dept: count for dept, count in dept_stats},
        "file_types": {file_type.value: count for file_type, count in type_stats}
    }


# ==================== PUBLIC POST IMAGE ENDPOINTS ====================
# These endpoints are specifically for post images and don't require authentication
# to make frontend integration easier for social media features

@router.post("/posts/upload-image")
async def upload_post_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload an image for posts (authenticated upload, but public access to view)"""
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check if it's an image
    file_ext = Path(file.filename).suffix.lower()
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    if file_ext not in image_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Only image files allowed. Supported: {', '.join(image_extensions)}"
        )
    
    # Read file content to check size
    content = await file.read()
    max_image_size = 10 * 1024 * 1024  # 10MB for images
    if len(content) > max_image_size:
        raise HTTPException(
            status_code=413, 
            detail=f"Image too large. Maximum size: {max_image_size // (1024*1024)}MB"
        )
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # Create posts-specific directory
    posts_dir = os.path.join(UPLOAD_DIR, "posts")
    os.makedirs(posts_dir, exist_ok=True)
    file_path = os.path.join(posts_dir, unique_filename)
    
    # Save file to disk
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Determine MIME type
    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "image/jpeg"
    
    # Create file record in database with special marking for post images
    db_file = FileModel(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=FileTypeEnum.IMAGE,
        mime_type=mime_type,
        description="Post image",
        department="posts",  # Special department for post images
        college_id=current_user.college_id,
        uploaded_by=current_user.id,
        upload_metadata={"type": "post_image", "public": True, "views": 0}
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Return response with public URL
    public_url = f"/files/posts/image/{unique_filename}"
    
    return {
        "id": db_file.id,
        "filename": unique_filename,
        "original_filename": file.filename,
        "file_size": len(content),
        "mime_type": mime_type,
        "public_url": public_url,
        "full_url": f"http://195.35.20.155:8000{public_url}",  # Adjust base URL as needed
        "message": "Post image uploaded successfully"
    }


@router.get("/posts/image/{filename}")
async def serve_post_image(filename: str):
    """Serve post images publicly (NO authentication required)"""
    
    # Construct file path
    file_path = os.path.join(UPLOAD_DIR, "posts", filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Get MIME type
    mime_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
    
    return FastAPIFileResponse(
        path=file_path,
        media_type=mime_type
    )


@router.delete("/posts/image/{filename}")
async def delete_post_image(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a post image (authenticated - only by uploader)"""
    
    # Find file in database
    file = db.query(FileModel).filter(
        and_(
            FileModel.filename == filename,
            FileModel.department == "posts",
            FileModel.college_id == current_user.college_id
        )
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Check if user is the uploader
    if file.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this image")
    
    # Delete file from disk
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        print(f"Error deleting file from disk: {e}")
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    return {"message": "Post image deleted successfully"}