from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List, Dict
import os
import uuid
import mimetypes
from pathlib import Path

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import File as FileModel, User, College, FileType as FileTypeEnum, IndexingTask
from ..models.schemas import (
    FileUploadResponse, FileResponse, FileUpdate, FileListResponse, 
    FileSearchQuery, FileType, FolderCreate, FolderItem, FolderContentsResponse
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


def normalize_folder_path(path: str) -> str:
    """Normalize folder path to ensure it starts with / and doesn't end with / (except root)"""
    if not path:
        return "/"
    
    # Remove leading/trailing whitespace
    path = path.strip()
    
    # Ensure it starts with /
    if not path.startswith("/"):
        path = "/" + path
    
    # Remove trailing / except for root
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    
    # Remove any double slashes
    while "//" in path:
        path = path.replace("//", "/")
    
    return path


def get_parent_path(folder_path: str) -> Optional[str]:
    """Get parent folder path from a given path"""
    folder_path = normalize_folder_path(folder_path)
    if folder_path == "/":
        return None
    
    parts = folder_path.rsplit("/", 1)
    if len(parts) == 1:
        return "/"
    
    parent = parts[0]
    return parent if parent else "/"


def create_breadcrumbs(folder_path: str) -> List[Dict[str, str]]:
    """Create breadcrumb navigation from folder path"""
    breadcrumbs = [{"name": "Home", "path": "/"}]
    
    if folder_path == "/":
        return breadcrumbs
    
    folder_path = normalize_folder_path(folder_path)
    parts = folder_path.strip("/").split("/")
    current_path = ""
    
    for part in parts:
        current_path += "/" + part
        breadcrumbs.append({"name": part, "path": normalize_folder_path(current_path)})
    
    return breadcrumbs


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
    folder_path: Optional[str] = Form("/"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file to the system with optional folder path"""
    
    # Normalize folder path
    folder_path = normalize_folder_path(folder_path or "/")
    
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
        folder_path=folder_path,
        is_folder=False,
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
        folder_path=db_file.folder_path,
        is_folder=db_file.is_folder,
        uploader_name=current_user.full_name,
        college_name=college.name if college else "Unknown"
    )


# ==================== FOLDER MANAGEMENT ====================

@router.post("/folders/create")
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new folder"""
    
    # Normalize parent path
    parent_path = normalize_folder_path(folder_data.parent_path)
    
    # Create the new folder path
    folder_name = folder_data.name.strip()
    if not folder_name or "/" in folder_name:
        raise HTTPException(status_code=400, detail="Invalid folder name")
    
    new_folder_path = normalize_folder_path(f"{parent_path}/{folder_name}")
    
    # Check if folder already exists
    existing_folder = db.query(FileModel).filter(
        and_(
            FileModel.folder_path == new_folder_path,
            FileModel.is_folder == True,
            FileModel.college_id == current_user.college_id,
            FileModel.department == current_user.department
        )
    ).first()
    
    if existing_folder:
        raise HTTPException(status_code=400, detail="Folder already exists")
    
    # Create folder entry in database
    folder = FileModel(
        filename=folder_name,
        original_filename=folder_name,
        file_path="",  # Folders don't have physical paths
        file_size=0,
        file_type=FileTypeEnum.OTHER,
        mime_type="application/x-directory",
        description=folder_data.description,
        folder_path=new_folder_path,
        is_folder=True,
        department=current_user.department,
        college_id=current_user.college_id,
        uploaded_by=current_user.id,
        upload_metadata={"file_count": 0}
    )
    
    db.add(folder)
    db.commit()
    db.refresh(folder)
    
    return {
        "id": folder.id,
        "name": folder_name,
        "path": new_folder_path,
        "message": "Folder created successfully"
    }


@router.get("/folders/browse")
async def browse_folder(
    folder_path: str = Query("/", description="Folder path to browse"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FolderContentsResponse:
    """Browse folder contents with hierarchical structure"""
    
    # Normalize the folder path
    folder_path = normalize_folder_path(folder_path)
    
    # Get all folders at this level
    folders = db.query(FileModel).filter(
        and_(
            FileModel.college_id == current_user.college_id,
            FileModel.is_folder == True,
            FileModel.folder_path.like(f"{folder_path}%") if folder_path != "/" else True
        )
    ).all()
    
    # Filter to get only direct children folders
    direct_folders = []
    for folder in folders:
        # For root, check if folder path has only one level
        if folder_path == "/":
            # Count slashes - should be exactly 1 for direct children of root
            if folder.folder_path.count("/") == 1 and folder.folder_path != "/":
                direct_folders.append(folder)
        else:
            # For non-root, check if it starts with current path and is one level deep
            if folder.folder_path.startswith(folder_path + "/"):
                # Remove the current path and check for only one level
                relative_path = folder.folder_path[len(folder_path)+1:]
                if "/" not in relative_path:
                    direct_folders.append(folder)
    
    # Get all files in this exact folder
    files_query = db.query(FileModel).filter(
        and_(
            FileModel.college_id == current_user.college_id,
            FileModel.folder_path == folder_path,
            FileModel.is_folder == False
        )
    ).order_by(FileModel.created_at.desc())
    
    files = files_query.all()
    
    # Build folder items response
    folder_items = []
    for folder in direct_folders:
        # Count files in this folder (recursive)
        file_count = db.query(FileModel).filter(
            and_(
                FileModel.college_id == current_user.college_id,
                FileModel.folder_path.like(f"{folder.folder_path}%"),
                FileModel.is_folder == False
            )
        ).count()
        
        uploader = db.query(User).filter(User.id == folder.uploaded_by).first()
        
        folder_items.append(FolderItem(
            id=folder.id,
            name=folder.filename,
            path=folder.folder_path,
            is_folder=True,
            file_type=None,
            file_size=0,
            file_count=file_count,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
            uploader_name=uploader.full_name if uploader else "Unknown",
            description=folder.description
        ))
    
    # Build file items response
    file_items = []
    for file in files:
        uploader = db.query(User).filter(User.id == file.uploaded_by).first()
        
        file_items.append(FolderItem(
            id=file.id,
            name=file.original_filename,
            path=file.folder_path,
            is_folder=False,
            file_type=file.file_type,
            file_size=file.file_size,
            file_count=0,
            created_at=file.created_at,
            updated_at=file.updated_at,
            uploader_name=uploader.full_name if uploader else "Unknown",
            description=file.description
        ))
    
    # Get parent path
    parent_path = get_parent_path(folder_path)
    
    # Create breadcrumbs
    breadcrumbs = create_breadcrumbs(folder_path)
    
    return FolderContentsResponse(
        current_path=folder_path,
        parent_path=parent_path,
        folders=folder_items,
        files=file_items,
        total_items=len(folder_items) + len(file_items),
        breadcrumbs=breadcrumbs
    )


@router.delete("/folders/delete")
async def delete_folder(
    folder_path: str = Query(..., description="Folder path to delete"),
    recursive: bool = Query(False, description="Delete folder and all contents"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a folder (optionally with all contents)"""
    
    folder_path = normalize_folder_path(folder_path)
    
    if folder_path == "/":
        raise HTTPException(status_code=400, detail="Cannot delete root folder")
    
    # Find the folder
    folder = db.query(FileModel).filter(
        and_(
            FileModel.folder_path == folder_path,
            FileModel.is_folder == True,
            FileModel.college_id == current_user.college_id
        )
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Check if user is the creator
    if folder.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this folder")
    
    # Count files in folder
    files_in_folder = db.query(FileModel).filter(
        and_(
            FileModel.college_id == current_user.college_id,
            FileModel.folder_path.like(f"{folder_path}%"),
            FileModel.is_folder == False
        )
    ).count()
    
    # Count subfolders
    subfolders = db.query(FileModel).filter(
        and_(
            FileModel.college_id == current_user.college_id,
            FileModel.folder_path.like(f"{folder_path}/%"),
            FileModel.is_folder == True
        )
    ).count()
    
    if (files_in_folder > 0 or subfolders > 0) and not recursive:
        raise HTTPException(
            status_code=400, 
            detail=f"Folder is not empty ({files_in_folder} files, {subfolders} subfolders). Use recursive=true to delete all contents"
        )
    
    if recursive:
        # Delete all files in folder and subfolders
        files_to_delete = db.query(FileModel).filter(
            and_(
                FileModel.college_id == current_user.college_id,
                FileModel.folder_path.like(f"{folder_path}%"),
                FileModel.is_folder == False
            )
        ).all()
        
        # Delete physical files
        for file in files_to_delete:
            try:
                if file.file_path and os.path.exists(file.file_path):
                    os.remove(file.file_path)
            except Exception as e:
                print(f"Error deleting file {file.file_path}: {e}")
        
        # Delete all subfolders
        db.query(FileModel).filter(
            and_(
                FileModel.college_id == current_user.college_id,
                FileModel.folder_path.like(f"{folder_path}/%"),
                FileModel.is_folder == True
            )
        ).delete(synchronize_session=False)
        
        # Delete all files records
        db.query(FileModel).filter(
            and_(
                FileModel.college_id == current_user.college_id,
                FileModel.folder_path.like(f"{folder_path}%"),
                FileModel.is_folder == False
            )
        ).delete(synchronize_session=False)
    
    # Delete the folder itself
    db.delete(folder)
    db.commit()
    
    return {
        "message": "Folder deleted successfully",
        "deleted_files": files_in_folder if recursive else 0,
        "deleted_folders": subfolders + 1 if recursive else 1
    }


@router.put("/folders/move")
async def move_folder(
    source_path: str = Query(..., description="Source folder path"),
    destination_path: str = Query(..., description="Destination parent folder path"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Move a folder to a different location"""
    
    source_path = normalize_folder_path(source_path)
    destination_path = normalize_folder_path(destination_path)
    
    if source_path == "/":
        raise HTTPException(status_code=400, detail="Cannot move root folder")
    
    # Find source folder
    folder = db.query(FileModel).filter(
        and_(
            FileModel.folder_path == source_path,
            FileModel.is_folder == True,
            FileModel.college_id == current_user.college_id
        )
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Source folder not found")
    
    # Check permissions
    if folder.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to move this folder")
    
    # Create new path
    folder_name = source_path.rsplit("/", 1)[-1]
    new_path = normalize_folder_path(f"{destination_path}/{folder_name}")
    
    # Check if destination already exists
    existing = db.query(FileModel).filter(
        and_(
            FileModel.folder_path == new_path,
            FileModel.is_folder == True,
            FileModel.college_id == current_user.college_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Destination folder already exists")
    
    # Update folder path
    old_path = folder.folder_path
    folder.folder_path = new_path
    
    # Update all files and subfolders in this folder
    files_and_folders = db.query(FileModel).filter(
        and_(
            FileModel.college_id == current_user.college_id,
            FileModel.folder_path.like(f"{old_path}%")
        )
    ).all()
    
    for item in files_and_folders:
        item.folder_path = item.folder_path.replace(old_path, new_path, 1)
    
    db.commit()
    
    return {
        "message": "Folder moved successfully",
        "old_path": old_path,
        "new_path": new_path,
        "items_updated": len(files_and_folders)
    }


@router.get("/", response_model=FileListResponse)
async def get_files(
    department: Optional[str] = Query(None, description="Filter by department"),
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    search_term: Optional[str] = Query(None, description="Search in filename and description"),
    folder_path: Optional[str] = Query(None, description="Filter by folder path"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get files with filtering and pagination (college-specific)"""
    
    # Base query - only files from user's college (exclude folders)
    query = db.query(FileModel).filter(
        and_(
            FileModel.college_id == current_user.college_id,
            FileModel.is_folder == False
        )
    )
    
    # Apply filters
    if department:
        query = query.filter(FileModel.department == department)
    
    if file_type:
        # Convert string enum to database enum
        file_type_enum = FileTypeEnum(file_type.value)
        query = query.filter(FileModel.file_type == file_type_enum)
    
    if folder_path:
        # Normalize and filter by folder path
        folder_path = normalize_folder_path(folder_path)
        query = query.filter(FileModel.folder_path == folder_path)
    
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
            folder_path=file.folder_path,
            is_folder=file.is_folder,
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
    folder_path: Optional[str] = Form("/posts"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload an image for posts (authenticated upload, but public access to view)"""
    
    # Normalize folder path
    folder_path = normalize_folder_path(folder_path or "/posts")
    
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
        folder_path=folder_path,
        is_folder=False,
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
        "folder_path": folder_path,
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