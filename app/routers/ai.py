from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import (
    User, College, File as FileModel, Post, AIConversation, 
    IndexingTask, RewardPoint, Reward
)
from ..services.ai_service import get_ai_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


# Pydantic models for request/response
class AIQuery(BaseModel):
    question: str
    context_filter: Optional[str] = None  # "files", "posts", "all"


class AIResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    conversation_id: int


class IndexRequest(BaseModel):
    content_type: str  # "file", "post", "all"
    content_ids: Optional[List[int]] = None  # If None, index all


class IndexResponse(BaseModel):
    message: str
    tasks_created: int


class SearchResult(BaseModel):
    doc_id: str
    similarity: float
    metadata: Dict[str, Any]


class KnowledgeSearchQuery(BaseModel):
    query: str
    content_type: Optional[str] = None  # "file", "post", "college_info"
    limit: int = 5


@router.post("/ask", response_model=AIResponse)
async def ask_ai(
    query: AIQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask the AI assistant a question about college content.
    The AI has access to files, posts, and other college information.
    """
    try:
        # Get AI service
        ai_service = get_ai_service()
        
        # Get college information
        college = db.query(College).filter(College.id == current_user.college_id).first()
        if not college:
            raise HTTPException(status_code=404, detail="College not found")
        
        # Search knowledge base for relevant context
        content_filter = query.context_filter
        context_docs = ai_service.search_knowledge_base(
            query.question,
            college_filter=college.name,
            content_type=content_filter,
            top_k=8
        )
        
        # Generate AI response
        ai_response = ai_service.generate_ai_response(
            query.question,
            context_docs,
            college.name
        )
        
        # Save conversation to database
        conversation = AIConversation(
            user_id=current_user.id,
            college_id=current_user.college_id,
            query=query.question,
            response=ai_response,
            context_docs=[doc["metadata"] for doc in context_docs]
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # Format sources for response
        sources = []
        for doc in context_docs:
            metadata = doc["metadata"]
            source = {
                "type": metadata["type"],
                "similarity": doc["similarity"],
                "title": metadata.get("title") or metadata.get("filename", "Unknown"),
                "id": metadata["id"]
            }
            
            if metadata["type"] == "file":
                source.update({
                    "department": metadata.get("department"),
                    "filename": metadata.get("filename")
                })
            elif metadata["type"] == "post":
                source.update({
                    "post_type": metadata.get("post_type"),
                    "author": metadata.get("author")
                })
            
            sources.append(source)
        
        return AIResponse(
            answer=ai_response,
            sources=sources,
            conversation_id=conversation.id
        )
    
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/search", response_model=List[SearchResult])
async def search_knowledge(
    search_query: KnowledgeSearchQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Direct search in the knowledge base without AI response generation.
    Returns raw search results with similarity scores.
    """
    try:
        # Get AI service
        ai_service = get_ai_service()
        
        # Get college information
        college = db.query(College).filter(College.id == current_user.college_id).first()
        if not college:
            raise HTTPException(status_code=404, detail="College not found")
        
        # Search knowledge base
        results = ai_service.search_knowledge_base(
            search_query.query,
            college_filter=college.name,
            content_type=search_query.content_type,
            top_k=search_query.limit
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(SearchResult(
                doc_id=result["doc_id"],
                similarity=result["similarity"],
                metadata=result["metadata"]
            ))
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error in knowledge search: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/index", response_model=IndexResponse)
async def create_indexing_tasks(
    index_request: IndexRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create indexing tasks for files, posts, or all content.
    Content will be processed in the background.
    """
    try:
        tasks_created = 0
        
        if index_request.content_type in ["file", "all"]:
            # Get files to index
            file_query = db.query(FileModel).filter(
                FileModel.college_id == current_user.college_id
            )
            
            if index_request.content_ids:
                file_query = file_query.filter(FileModel.id.in_(index_request.content_ids))
            else:
                # Only index files that aren't already indexed or failed
                file_query = file_query.filter(
                    or_(
                        FileModel.is_indexed == "pending",
                        FileModel.is_indexed == "failed"
                    )
                )
            
            files = file_query.all()
            
            for file in files:
                # Create indexing task
                task = IndexingTask(
                    content_type="file",
                    content_id=file.id,
                    college_id=current_user.college_id,
                    status="pending"
                )
                db.add(task)
                tasks_created += 1
                
                # Add background task
                background_tasks.add_task(
                    process_file_indexing,
                    file.id,
                    current_user.college_id
                )
        
        if index_request.content_type in ["post", "all"]:
            # Get posts to index
            post_query = db.query(Post).filter(
                Post.college_id == current_user.college_id
            )
            
            if index_request.content_ids:
                post_query = post_query.filter(Post.id.in_(index_request.content_ids))
            
            posts = post_query.all()
            
            for post in posts:
                # Check if already has indexing task
                existing_task = db.query(IndexingTask).filter(
                    and_(
                        IndexingTask.content_type == "post",
                        IndexingTask.content_id == post.id,
                        IndexingTask.status.in_(["pending", "processing", "completed"])
                    )
                ).first()
                
                if not existing_task:
                    task = IndexingTask(
                        content_type="post",
                        content_id=post.id,
                        college_id=current_user.college_id,
                        status="pending"
                    )
                    db.add(task)
                    tasks_created += 1
                    
                    # Add background task
                    background_tasks.add_task(
                        process_post_indexing,
                        post.id,
                        current_user.college_id
                    )
        
        # Index college information
        if index_request.content_type == "all":
            background_tasks.add_task(
                process_college_indexing,
                current_user.college_id
            )
            tasks_created += 1
        
        db.commit()
        
        return IndexResponse(
            message=f"Created {tasks_created} indexing tasks",
            tasks_created=tasks_created
        )
    
    except Exception as e:
        logger.error(f"Error creating indexing tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")


@router.get("/conversations")
async def get_conversations(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's recent AI conversations"""
    conversations = db.query(AIConversation).filter(
        AIConversation.user_id == current_user.id
    ).order_by(AIConversation.created_at.desc()).limit(limit).all()
    
    return {
        "conversations": [
            {
                "id": conv.id,
                "query": conv.query,
                "response": conv.response,
                "sources_count": len(conv.context_docs) if conv.context_docs else 0,
                "created_at": conv.created_at
            }
            for conv in conversations
        ]
    }


@router.get("/stats")
async def get_ai_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI system statistics for the college"""
    try:
        # Get AI service stats
        ai_service = get_ai_service()
        vector_stats = ai_service.get_index_stats()
        
        # Get indexing stats from database
        indexed_files = db.query(FileModel).filter(
            and_(
                FileModel.college_id == current_user.college_id,
                FileModel.is_indexed == "indexed"
            )
        ).count()
        
        pending_files = db.query(FileModel).filter(
            and_(
                FileModel.college_id == current_user.college_id,
                FileModel.is_indexed == "pending"
            )
        ).count()
        
        failed_files = db.query(FileModel).filter(
            and_(
                FileModel.college_id == current_user.college_id,
                FileModel.is_indexed == "failed"
            )
        ).count()
        
        # Get conversation stats
        total_conversations = db.query(AIConversation).filter(
            AIConversation.college_id == current_user.college_id
        ).count()
        
        user_conversations = db.query(AIConversation).filter(
            AIConversation.user_id == current_user.id
        ).count()
        
        return {
            "vector_database": vector_stats,
            "indexing": {
                "indexed_files": indexed_files,
                "pending_files": pending_files,
                "failed_files": failed_files
            },
            "conversations": {
                "total_college_conversations": total_conversations,
                "user_conversations": user_conversations
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting AI stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


# Background task functions
async def process_file_indexing(file_id: int, college_id: int):
    """Background task to index a file"""
    try:
        # Get database session
        from ..core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Get file
            file = db.query(FileModel).filter(FileModel.id == file_id).first()
            if not file:
                logger.error(f"File {file_id} not found for indexing")
                return
            
            # Get additional info
            college = db.query(College).filter(College.id == college_id).first()
            uploader = db.query(User).filter(User.id == file.uploaded_by).first()
            
            # Get AI service and index file
            ai_service = get_ai_service()
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
            
            # Update file status
            file.is_indexed = "indexed" if success else "failed"
            
            # Update task status
            task = db.query(IndexingTask).filter(
                and_(
                    IndexingTask.content_type == "file",
                    IndexingTask.content_id == file_id,
                    IndexingTask.status == "pending"
                )
            ).first()
            
            if task:
                task.status = "completed" if success else "failed"
                if not success:
                    task.error_message = "Failed to generate embedding or extract text"
                task.processed_at = func.now()
            
            db.commit()
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in background file indexing {file_id}: {e}")


async def process_post_indexing(post_id: int, college_id: int):
    """Background task to index a post"""
    try:
        # Get database session
        from ..core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Get post
            post = db.query(Post).filter(Post.id == post_id).first()
            if not post:
                logger.error(f"Post {post_id} not found for indexing")
                return
            
            # Get additional info
            college = db.query(College).filter(College.id == college_id).first()
            author = db.query(User).filter(User.id == post.author_id).first()
            
            # Get AI service and index post
            ai_service = get_ai_service()
            success = ai_service.index_post(
                post_id=post.id,
                title=post.title,
                content=post.content,
                post_type=post.post_type.value,
                department=author.department if author else "Unknown",
                college_name=college.name if college else "Unknown",
                author_name=author.full_name if author else "Unknown"
            )
            
            # Update task status
            task = db.query(IndexingTask).filter(
                and_(
                    IndexingTask.content_type == "post",
                    IndexingTask.content_id == post_id,
                    IndexingTask.status == "pending"
                )
            ).first()
            
            if task:
                task.status = "completed" if success else "failed"
                if not success:
                    task.error_message = "Failed to generate embedding"
                task.processed_at = func.now()
            
            db.commit()
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in background post indexing {post_id}: {e}")


async def process_college_indexing(college_id: int):
    """Background task to index college information"""
    try:
        # Get database session
        from ..core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Get college info
            college = db.query(College).filter(College.id == college_id).first()
            if not college:
                return
            
            # Get departments
            departments = db.query(FileModel.department).filter(
                FileModel.college_id == college_id
            ).distinct().all()
            dept_list = [dept[0] for dept in departments]
            
            # Get stats
            stats = {
                "total_files": db.query(FileModel).filter(FileModel.college_id == college_id).count(),
                "total_posts": db.query(Post).filter(Post.college_id == college_id).count(),
                "total_users": db.query(User).filter(User.college_id == college_id).count(),
                "total_rewards": db.query(Reward).filter(Reward.college_id == college_id).count()
            }
            
            # Index college info
            ai_service = get_ai_service()
            ai_service.index_college_info(
                college_id=college.id,
                college_name=college.name,
                departments=dept_list,
                stats=stats
            )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in background college indexing {college_id}: {e}")