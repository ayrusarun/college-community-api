from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, case
from typing import List
from datetime import datetime

from ..core.database import get_db
from ..core.utils import time_ago
from ..core.rbac import PermissionChecker, has_permission
from ..models.models import Post, User, PostType, IndexingTask, Alert
from ..models.schemas import PostCreate, PostResponse, PostUpdate, PostMetadataUpdate, PostAlertCreate, AlertResponse
from ..routers.auth import get_current_user
from ..services.moderation import moderation_service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostResponse)
async def create_post(
    post: PostCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("write:posts"))  # ✅ RBAC Protection
):
    # Check content moderation
    is_inappropriate, reason = await moderation_service.check_content(
        title=post.title,
        content=post.content,
        image_url=post.image_url
    )
    
    if is_inappropriate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inappropriate content found. " + reason
        )
    
    db_post = Post(
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        post_type=post.post_type,
        author_id=current_user.id,
        college_id=current_user.college_id,
        post_metadata={"likes": 0, "comments": 0, "shares": 0}
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    # Create indexing task for AI
    try:
        indexing_task = IndexingTask(
            content_type="post",
            content_id=db_post.id,
            college_id=current_user.college_id,
            status="pending"
        )
        db.add(indexing_task)
        db.commit()
        
        # Add background task for indexing
        from .ai import process_post_indexing
        background_tasks.add_task(
            process_post_indexing,
            db_post.id,
            current_user.college_id
        )
    except Exception as e:
        # Log error but don't fail post creation
        print(f"Error creating indexing task for post {db_post.id}: {e}")
    
    # Return with author name and department
    return PostResponse(
        id=db_post.id,
        title=db_post.title,
        content=db_post.content,
        image_url=db_post.image_url,
        post_type=db_post.post_type,
        author_id=db_post.author_id,
        college_id=db_post.college_id,
        post_metadata=db_post.post_metadata,
        created_at=db_post.created_at,
        updated_at=db_post.updated_at,
        author_name=current_user.full_name,
        author_department=current_user.department,
        time_ago=time_ago(db_post.created_at)
    )


@router.get("/", response_model=List[PostResponse])
async def get_posts(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("read:posts"))  # ✅ RBAC Protection
):
    # Define priority order for post types
    priority_order = case(
        (Post.post_type == PostType.IMPORTANT, 1),
        (Post.post_type == PostType.ANNOUNCEMENT, 2),
        (Post.post_type == PostType.EVENTS, 3),
        (Post.post_type == PostType.INFO, 4),
        (Post.post_type == PostType.GENERAL, 5),
        else_=6
    )
    
    # Get posts from the same college, ordered by priority then by creation date (newest first)
    posts = db.query(Post, User.full_name, User.department).join(
        User, Post.author_id == User.id
    ).filter(
        Post.college_id == current_user.college_id
    ).order_by(
        priority_order,
        desc(Post.created_at)
    ).offset(skip).limit(limit).all()
    
    # Convert to response format
    post_responses = []
    for post, author_name, author_department in posts:
        post_responses.append(PostResponse(
            id=post.id,
            title=post.title,
            content=post.content,
            image_url=post.image_url,
            post_type=post.post_type,
            author_id=post.author_id,
            college_id=post.college_id,
            post_metadata=post.post_metadata or {"likes": 0, "comments": 0, "shares": 0},
            created_at=post.created_at,
            updated_at=post.updated_at,
            author_name=author_name,
            author_department=author_department,
            time_ago=time_ago(post.created_at)
        ))
    
    return post_responses


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("read:posts"))  # ✅ RBAC Protection
):
    post_query = db.query(Post, User.full_name, User.department).join(
        User, Post.author_id == User.id
    ).filter(
        Post.id == post_id,
        Post.college_id == current_user.college_id  # Multi-tenant check
    ).first()
    
    if not post_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    post, author_name, author_department = post_query
    
    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        post_type=post.post_type,
        author_id=post.author_id,
        college_id=post.college_id,
        post_metadata=post.post_metadata or {"likes": 0, "comments": 0, "shares": 0},
        created_at=post.created_at,
        updated_at=post.updated_at,
        author_name=author_name,
        author_department=author_department,
        time_ago=time_ago(post.created_at)
    )


@router.get("/type/{post_type}", response_model=List[PostResponse])
async def get_posts_by_type(
    post_type: PostType,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("read:posts"))  # ✅ RBAC Protection
):
    posts = db.query(Post, User.full_name, User.department).join(
        User, Post.author_id == User.id
    ).filter(
        Post.college_id == current_user.college_id,
        Post.post_type == post_type
    ).order_by(
        desc(Post.created_at)
    ).offset(skip).limit(limit).all()
    
    # Convert to response format
    post_responses = []
    for post, author_name, author_department in posts:
        post_responses.append(PostResponse(
            id=post.id,
            title=post.title,
            content=post.content,
            image_url=post.image_url,
            post_type=post.post_type,
            author_id=post.author_id,
            college_id=post.college_id,
            post_metadata=post.post_metadata or {"likes": 0, "comments": 0, "shares": 0},
            created_at=post.created_at,
            updated_at=post.updated_at,
            author_name=author_name,
            author_department=author_department,
            time_ago=time_ago(post.created_at)
        ))
    
    return post_responses


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_update: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("update:posts"))  # ✅ RBAC Protection
):
    # Get the post and verify ownership OR manage permission
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.college_id == current_user.college_id
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Check ownership or manage permission
    if post.author_id != current_user.id:
        if not has_permission(current_user, "manage:posts", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own posts"
            )
    
    # Prepare updated content for moderation check
    updated_title = post_update.title if post_update.title is not None else post.title
    updated_content = post_update.content if post_update.content is not None else post.content
    updated_image_url = post_update.image_url if post_update.image_url is not None else post.image_url
    
    # Check content moderation for updated content
    is_inappropriate, reason = await moderation_service.check_content(
        title=updated_title,
        content=updated_content,
        image_url=updated_image_url
    )
    
    if is_inappropriate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inappropriate content found. " + reason
        )
    
    # Update fields if provided
    if post_update.title is not None:
        post.title = post_update.title
    if post_update.content is not None:
        post.content = post_update.content
    if post_update.image_url is not None:
        post.image_url = post_update.image_url
    if post_update.post_type is not None:
        post.post_type = post_update.post_type
    
    db.commit()
    db.refresh(post)
    
    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        post_type=post.post_type,
        author_id=post.author_id,
        college_id=post.college_id,
        post_metadata=post.post_metadata or {"likes": 0, "comments": 0, "shares": 0},
        created_at=post.created_at,
        updated_at=post.updated_at,
        author_name=current_user.full_name,
        author_department=current_user.department,
        time_ago=time_ago(post.created_at)
    )


@router.patch("/{post_id}/metadata", response_model=PostResponse)
async def update_post_metadata(
    post_id: int,
    metadata_update: PostMetadataUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("update:posts"))  # ✅ RBAC Protection
):
    # Get the post (any user can like/comment, not just the author)
    post_query = db.query(Post, User.full_name, User.department).join(
        User, Post.author_id == User.id
    ).filter(
        Post.id == post_id,
        Post.college_id == current_user.college_id
    ).first()
    
    if not post_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    post, author_name, author_department = post_query
    
    # Update metadata
    current_metadata = post.post_metadata or {"likes": 0, "comments": 0, "shares": 0}
    
    if metadata_update.likes is not None:
        current_metadata["likes"] = metadata_update.likes
    if metadata_update.comments is not None:
        current_metadata["comments"] = metadata_update.comments
    if metadata_update.shares is not None:
        current_metadata["shares"] = metadata_update.shares
    
    post.post_metadata = current_metadata
    db.commit()
    db.refresh(post)
    
    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        post_type=post.post_type,
        author_id=post.author_id,
        college_id=post.college_id,
        post_metadata=post.post_metadata,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author_name=author_name,
        author_department=author_department,
        time_ago=time_ago(post.created_at)
    )


@router.post("/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("update:posts"))  # ✅ RBAC Protection
):
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.college_id == current_user.college_id
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Increment likes
    current_metadata = post.post_metadata or {"likes": 0, "comments": 0, "shares": 0}
    current_metadata["likes"] = current_metadata.get("likes", 0) + 1
    post.post_metadata = current_metadata
    
    db.commit()
    
    return {"message": "Post liked successfully", "likes": current_metadata["likes"]}


@router.post("/{post_id}/alert", response_model=AlertResponse)
async def create_post_alert(
    post_id: int,
    alert_data: PostAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("write:alerts"))  # ✅ RBAC Protection
):
    """Create an alert for a specific post"""
    
    # Verify post exists and is in same college
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.college_id == current_user.college_id
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Verify target user exists and is in same college
    target_user = db.query(User).filter(
        User.id == alert_data.user_id,
        User.college_id == current_user.college_id
    ).first()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found in your college"
        )
    
    # Create alert
    alert = Alert(
        user_id=alert_data.user_id,
        title=alert_data.title,
        message=alert_data.message,
        alert_type=alert_data.alert_type,
        expires_at=alert_data.expires_at,
        post_id=post_id,
        college_id=current_user.college_id,
        created_by=current_user.id
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # Calculate time ago
    def calculate_time_ago(created_at: datetime) -> str:
        now = datetime.utcnow()
        diff = now - created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    
    # Check if expired
    def is_alert_expired(expires_at) -> bool:
        if expires_at is None:
            return False
        return datetime.utcnow() > expires_at
    
    # Build response
    alert_dict = {
        "id": alert.id,
        "user_id": alert.user_id,
        "title": alert.title,
        "message": alert.message,
        "alert_type": alert.alert_type,
        "is_enabled": alert.is_enabled,
        "is_read": alert.is_read,
        "expires_at": alert.expires_at,
        "post_id": alert.post_id,
        "college_id": alert.college_id,
        "created_by": alert.created_by,
        "created_at": alert.created_at,
        "updated_at": alert.updated_at,
        "creator_name": current_user.full_name,
        "post_title": post.title,
        "time_ago": calculate_time_ago(alert.created_at),
        "is_expired": is_alert_expired(alert.expires_at)
    }
    
    return AlertResponse(**alert_dict)