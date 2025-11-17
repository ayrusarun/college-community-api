from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, exists
from typing import List

from ..core.database import get_db
from ..core.utils import time_ago
from ..core.rbac import PermissionChecker
from ..models.models import (
    Post, PostLike, PostComment, PostIgnite, User, RewardPoint, PointTransaction
)
from ..models.schemas import (
    CommentCreate, CommentResponse, CommentListResponse,
    LikeResponse, LikeListResponse, LikeToggleResponse,
    IgniteResponse, IgniteToggleResponse, IgniteListResponse
)
from ..routers.auth import get_current_user

router = APIRouter(prefix="/posts", tags=["engagement"])


# ==================== COMMENTS ====================

@router.post("/{post_id}/comments", response_model=CommentResponse)
async def add_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("write:posts"))
):
    """Add a comment to a post"""
    
    # Validate comment length
    if len(comment_data.content.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment cannot be empty"
        )
    
    if len(comment_data.content) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment cannot exceed 500 characters"
        )
    
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
    
    # Create comment
    comment = PostComment(
        post_id=post_id,
        user_id=current_user.id,
        content=comment_data.content.strip()
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        user_name=current_user.full_name,
        user_department=current_user.department,
        time_ago=time_ago(comment.created_at)
    )


@router.get("/{post_id}/comments", response_model=CommentListResponse)
async def get_comments(
    post_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("read:posts"))
):
    """Get comments for a post (paginated, newest first)"""
    
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
    
    # Calculate pagination
    skip = (page - 1) * page_size
    
    # Get total count
    total_count = db.query(func.count(PostComment.id)).filter(
        PostComment.post_id == post_id
    ).scalar()
    
    # Get comments with user info
    comments_query = db.query(
        PostComment, User.full_name, User.department
    ).join(
        User, PostComment.user_id == User.id
    ).filter(
        PostComment.post_id == post_id
    ).order_by(
        desc(PostComment.created_at)
    ).offset(skip).limit(page_size).all()
    
    comments = []
    for comment, user_name, user_dept in comments_query:
        comments.append(CommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            user_id=comment.user_id,
            content=comment.content,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            user_name=user_name,
            user_department=user_dept,
            time_ago=time_ago(comment.created_at)
        ))
    
    return CommentListResponse(
        comments=comments,
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("update:posts"))
):
    """Delete a comment (only by comment author or admin)"""
    
    comment = db.query(PostComment).filter(
        PostComment.id == comment_id,
        PostComment.post_id == post_id
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Check ownership (or admin permission)
    if comment.user_id != current_user.id:
        from ..core.rbac import has_permission
        if not has_permission(current_user, "manage:posts", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments"
            )
    
    db.delete(comment)
    db.commit()
    
    return {"message": "Comment deleted successfully"}


# ==================== LIKES ====================

@router.post("/{post_id}/like", response_model=LikeToggleResponse)
async def toggle_like(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("write:posts"))
):
    """Toggle like on a post (like if not liked, unlike if already liked)"""
    
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
    
    # Check if user already liked
    existing_like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        db.commit()
        db.refresh(post)
        
        return LikeToggleResponse(
            success=True,
            action="unliked",
            like_count=post.like_count
        )
    else:
        # Like
        new_like = PostLike(
            post_id=post_id,
            user_id=current_user.id
        )
        db.add(new_like)
        db.commit()
        db.refresh(post)
        
        return LikeToggleResponse(
            success=True,
            action="liked",
            like_count=post.like_count
        )


@router.get("/{post_id}/likes", response_model=LikeListResponse)
async def get_likes(
    post_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("read:posts"))
):
    """Get users who liked a post"""
    
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
    
    # Calculate pagination
    skip = (page - 1) * page_size
    
    # Get total count
    total_count = db.query(func.count(PostLike.id)).filter(
        PostLike.post_id == post_id
    ).scalar()
    
    # Get likes with user info
    likes_query = db.query(
        PostLike, User.full_name, User.department
    ).join(
        User, PostLike.user_id == User.id
    ).filter(
        PostLike.post_id == post_id
    ).order_by(
        desc(PostLike.created_at)
    ).offset(skip).limit(page_size).all()
    
    likes = []
    for like, user_name, user_dept in likes_query:
        likes.append(LikeResponse(
            id=like.id,
            post_id=like.post_id,
            user_id=like.user_id,
            created_at=like.created_at,
            user_name=user_name,
            user_department=user_dept
        ))
    
    return LikeListResponse(
        likes=likes,
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@router.get("/{post_id}/is-liked")
async def check_if_liked(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if current user has liked a post"""
    
    has_liked = db.query(exists().where(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id
    )).scalar()
    
    return {"post_id": post_id, "has_liked": has_liked}


# ==================== IGNITE ====================

@router.post("/{post_id}/ignite", response_model=IgniteToggleResponse)
async def toggle_ignite(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("write:posts"))
):
    """
    Toggle ignite on a post
    - Ignite: Deduct 1 point from user, add 1 point to post author
    - Un-ignite: Refund 1 point to user, deduct 1 point from post author
    """
    
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
    
    # Cannot ignite own post
    if post.author_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot ignite your own post"
        )
    
    # Check if user already ignited
    existing_ignite = db.query(PostIgnite).filter(
        PostIgnite.post_id == post_id,
        PostIgnite.giver_id == current_user.id
    ).first()
    
    if existing_ignite:
        # Un-ignite (refund)
        try:
            # Get or create user's reward points
            user_points = db.query(RewardPoint).filter(
                RewardPoint.user_id == current_user.id
            ).first()
            
            if not user_points:
                user_points = RewardPoint(user_id=current_user.id, total_points=0)
                db.add(user_points)
            
            # Get or create author's reward points
            author_points = db.query(RewardPoint).filter(
                RewardPoint.user_id == post.author_id
            ).first()
            
            if not author_points:
                author_points = RewardPoint(user_id=post.author_id, total_points=0)
                db.add(author_points)
            
            # Refund points
            user_points.total_points += 1
            author_points.total_points = max(0, author_points.total_points - 1)
            
            # Create transaction records
            user_transaction = PointTransaction(
                user_id=current_user.id,
                transaction_type="REFUNDED",
                points=1,
                balance_after=user_points.total_points,
                description=f"Refund: Removed ignite from post '{post.title[:50]}'",
                reference_type="ignite",
                reference_id=post_id,
                college_id=current_user.college_id
            )
            
            author_transaction = PointTransaction(
                user_id=post.author_id,
                transaction_type="DEDUCTED",
                points=-1,
                balance_after=author_points.total_points,
                description=f"Ignite removed from your post '{post.title[:50]}'",
                reference_type="ignite",
                reference_id=post_id,
                college_id=current_user.college_id
            )
            
            db.add(user_transaction)
            db.add(author_transaction)
            
            # Delete ignite
            db.delete(existing_ignite)
            db.commit()
            db.refresh(post)
            
            return IgniteToggleResponse(
                success=True,
                action="removed",
                ignite_count=post.ignite_count,
                points_transferred=-1
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove ignite: {str(e)}"
            )
    else:
        # Ignite (deduct from user, add to author)
        try:
            # Get or create user's reward points
            user_points = db.query(RewardPoint).filter(
                RewardPoint.user_id == current_user.id
            ).first()
            
            if not user_points:
                user_points = RewardPoint(user_id=current_user.id, total_points=0)
                db.add(user_points)
            
            # Check if user has enough points
            if user_points.total_points < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient points. You need at least 1 point to ignite a post."
                )
            
            # Get or create author's reward points
            author_points = db.query(RewardPoint).filter(
                RewardPoint.user_id == post.author_id
            ).first()
            
            if not author_points:
                author_points = RewardPoint(user_id=post.author_id, total_points=0)
                db.add(author_points)
            
            # Transfer points
            user_points.total_points -= 1
            author_points.total_points += 1
            
            # Create transaction records
            user_transaction = PointTransaction(
                user_id=current_user.id,
                transaction_type="SPENT",
                points=-1,
                balance_after=user_points.total_points,
                description=f"Ignited post '{post.title[:50]}'",
                reference_type="ignite",
                reference_id=post_id,
                college_id=current_user.college_id
            )
            
            author_transaction = PointTransaction(
                user_id=post.author_id,
                transaction_type="EARNED",
                points=1,
                balance_after=author_points.total_points,
                description=f"Received ignite on your post '{post.title[:50]}'",
                reference_type="ignite",
                reference_id=post_id,
                college_id=current_user.college_id
            )
            
            db.add(user_transaction)
            db.add(author_transaction)
            
            # Create ignite
            new_ignite = PostIgnite(
                post_id=post_id,
                giver_id=current_user.id,
                receiver_id=post.author_id
            )
            
            db.add(new_ignite)
            db.commit()
            db.refresh(post)
            
            return IgniteToggleResponse(
                success=True,
                action="ignited",
                ignite_count=post.ignite_count,
                points_transferred=1
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to ignite post: {str(e)}"
            )


@router.get("/{post_id}/ignites", response_model=IgniteListResponse)
async def get_ignites(
    post_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("read:posts"))
):
    """Get users who ignited a post"""
    
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
    
    # Calculate pagination
    skip = (page - 1) * page_size
    
    # Get total count
    total_count = db.query(func.count(PostIgnite.id)).filter(
        PostIgnite.post_id == post_id
    ).scalar()
    
    # Get ignites with user info
    ignites_query = db.query(PostIgnite).filter(
        PostIgnite.post_id == post_id
    ).order_by(
        desc(PostIgnite.created_at)
    ).offset(skip).limit(page_size).all()
    
    ignites = []
    for ignite in ignites_query:
        giver = db.query(User).filter(User.id == ignite.giver_id).first()
        receiver = db.query(User).filter(User.id == ignite.receiver_id).first()
        
        ignites.append(IgniteResponse(
            id=ignite.id,
            post_id=ignite.post_id,
            giver_id=ignite.giver_id,
            receiver_id=ignite.receiver_id,
            created_at=ignite.created_at,
            giver_name=giver.full_name if giver else "Unknown",
            receiver_name=receiver.full_name if receiver else "Unknown"
        ))
    
    return IgniteListResponse(
        ignites=ignites,
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@router.get("/{post_id}/is-ignited")
async def check_if_ignited(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if current user has ignited a post"""
    
    has_ignited = db.query(exists().where(
        PostIgnite.post_id == post_id,
        PostIgnite.giver_id == current_user.id
    )).scalar()
    
    return {"post_id": post_id, "has_ignited": has_ignited}
