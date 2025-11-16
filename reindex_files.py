#!/usr/bin/env python3
"""
Script to re-index all PDF files in the system
This ensures PDFs are properly indexed with the improved text extraction
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import File as FileModel, College, User, IndexingTask
from app.services.ai_service import get_ai_service
from sqlalchemy import and_, or_
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reindex_all_files():
    """Re-index all files, especially PDFs"""
    db = SessionLocal()
    
    try:
        # Get AI service
        ai_service = get_ai_service()
        
        # Get all files, prioritizing PDFs
        files = db.query(FileModel).filter(
            or_(
                FileModel.mime_type == 'application/pdf',
                FileModel.file_path.like('%.pdf'),
                FileModel.is_indexed.in_(['pending', 'failed', None])
            )
        ).all()
        
        logger.info(f"Found {len(files)} files to index")
        
        success_count = 0
        failed_count = 0
        
        for file in files:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing file {file.id}: {file.original_filename}")
                logger.info(f"Type: {file.mime_type}")
                logger.info(f"Path: {file.file_path}")
                
                # Check if file exists
                if not os.path.exists(file.file_path):
                    logger.error(f"File not found on disk: {file.file_path}")
                    file.is_indexed = "failed"
                    failed_count += 1
                    continue
                
                # Get college and uploader info
                college = db.query(College).filter(College.id == file.college_id).first()
                uploader = db.query(User).filter(User.id == file.uploaded_by).first()
                
                # Index the file
                success = ai_service.index_file(
                    file_id=file.id,
                    file_path=file.file_path,
                    original_filename=file.original_filename,
                    mime_type=file.mime_type,
                    description=file.description or "",
                    department=file.department,
                    college_name=college.name if college else "Unknown",
                    uploader_name=uploader.full_name if uploader else "Unknown"
                )
                
                if success:
                    file.is_indexed = "indexed"
                    success_count += 1
                    logger.info(f"✅ Successfully indexed: {file.original_filename}")
                else:
                    file.is_indexed = "failed"
                    failed_count += 1
                    logger.error(f"❌ Failed to index: {file.original_filename}")
                
                # Create or update indexing task
                task = db.query(IndexingTask).filter(
                    and_(
                        IndexingTask.content_type == "file",
                        IndexingTask.content_id == file.id
                    )
                ).first()
                
                if not task:
                    task = IndexingTask(
                        content_type="file",
                        content_id=file.id,
                        college_id=file.college_id,
                        status="completed" if success else "failed"
                    )
                    db.add(task)
                else:
                    task.status = "completed" if success else "failed"
                
                db.commit()
                
            except Exception as e:
                logger.error(f"Error processing file {file.id}: {e}", exc_info=True)
                file.is_indexed = "failed"
                failed_count += 1
                db.commit()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Indexing complete!")
        logger.info(f"✅ Success: {success_count}")
        logger.info(f"❌ Failed: {failed_count}")
        logger.info(f"📊 Total: {len(files)}")
        
        # Show vector DB stats
        stats = ai_service.get_index_stats()
        logger.info(f"\nVector Database Stats:")
        logger.info(f"Total documents: {stats['total_documents']}")
        logger.info(f"Database size: {stats['total_size_mb']:.2f} MB")
        
    except Exception as e:
        logger.error(f"Fatal error in reindexing: {e}", exc_info=True)
    finally:
        db.close()


def reindex_specific_file(file_id: int):
    """Re-index a specific file by ID"""
    db = SessionLocal()
    
    try:
        # Get AI service
        ai_service = get_ai_service()
        
        # Get the file
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        
        if not file:
            logger.error(f"File {file_id} not found")
            return
        
        logger.info(f"Re-indexing file {file_id}: {file.original_filename}")
        
        # Check if file exists
        if not os.path.exists(file.file_path):
            logger.error(f"File not found on disk: {file.file_path}")
            return
        
        # Get college and uploader info
        college = db.query(College).filter(College.id == file.college_id).first()
        uploader = db.query(User).filter(User.id == file.uploaded_by).first()
        
        # Index the file
        success = ai_service.index_file(
            file_id=file.id,
            file_path=file.file_path,
            original_filename=file.original_filename,
            mime_type=file.mime_type,
            description=file.description or "",
            department=file.department,
            college_name=college.name if college else "Unknown",
            uploader_name=uploader.full_name if uploader else "Unknown"
        )
        
        if success:
            file.is_indexed = "indexed"
            logger.info(f"✅ Successfully re-indexed: {file.original_filename}")
        else:
            file.is_indexed = "failed"
            logger.error(f"❌ Failed to re-index: {file.original_filename}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error re-indexing file {file_id}: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Re-index specific file by ID
        try:
            file_id = int(sys.argv[1])
            logger.info(f"Re-indexing specific file: {file_id}")
            reindex_specific_file(file_id)
        except ValueError:
            logger.error("Invalid file ID. Usage: python reindex_files.py [file_id]")
    else:
        # Re-index all files
        logger.info("Re-indexing all files")
        reindex_all_files()
