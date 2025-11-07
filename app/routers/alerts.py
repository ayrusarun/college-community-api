from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import Optional, List
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import Alert, User, Post
from ..models.schemas import (
    AlertCreate, AlertResponse, AlertUpdate, AlertListResponse,
    UserResponse
)


router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
    responses={404: {"description": "Not found"}},
)


def calculate_time_ago(created_at: datetime) -> str:
    """Calculate human-readable time difference"""
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


def is_alert_expired(expires_at: Optional[datetime]) -> bool:
    """Check if alert has expired"""
    if expires_at is None:
        return False
    return datetime.utcnow() > expires_at


@router.get("/", response_model=AlertListResponse)
async def get_user_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    show_read: bool = Query(True, description="Include read alerts"),
    show_disabled: bool = Query(False, description="Include disabled alerts"),
    show_expired: bool = Query(False, description="Include expired alerts"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alerts for the current user with pagination and filtering"""
    
    # Build query filters
    filters = [Alert.user_id == current_user.id, Alert.college_id == current_user.college_id]
    
    # Filter by read status
    if not show_read:
        filters.append(Alert.is_read == False)
    
    # Filter by enabled status
    if not show_disabled:
        filters.append(Alert.is_enabled == True)
    
    # Filter by expiry
    if not show_expired:
        filters.append(or_(Alert.expires_at.is_(None), Alert.expires_at > datetime.utcnow()))
    
    # Filter by alert type
    if alert_type:
        filters.append(Alert.alert_type == alert_type)
    
    # Get total count
    total_count = db.query(Alert).filter(and_(*filters)).count()
    
    # Get paginated results
    alerts_query = (
        db.query(Alert, User.full_name.label("creator_name"), Post.title.label("post_title"))
        .join(User, Alert.created_by == User.id)
        .outerjoin(Post, Alert.post_id == Post.id)
        .filter(and_(*filters))
        .order_by(desc(Alert.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    
    alert_results = alerts_query.all()
    
    # Transform results
    alerts = []
    for alert, creator_name, post_title in alert_results:
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
            "creator_name": creator_name,
            "post_title": post_title,
            "time_ago": calculate_time_ago(alert.created_at),
            "is_expired": is_alert_expired(alert.expires_at)
        }
        alerts.append(AlertResponse(**alert_dict))
    
    # Get unread count
    unread_filters = [
        Alert.user_id == current_user.id,
        Alert.college_id == current_user.college_id,
        Alert.is_read == False,
        Alert.is_enabled == True
    ]
    if not show_expired:
        unread_filters.append(or_(Alert.expires_at.is_(None), Alert.expires_at > datetime.utcnow()))
    
    unread_count = db.query(Alert).filter(and_(*unread_filters)).count()
    
    return AlertListResponse(
        alerts=alerts,
        total_count=total_count,
        unread_count=unread_count,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new alert for a specific user"""
    
    # Verify target user exists and is in same college
    target_user = db.query(User).filter(
        User.id == alert_data.user_id,
        User.college_id == current_user.college_id
    ).first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found in your college")
    
    # Verify post exists if post_id is provided
    if alert_data.post_id:
        post = db.query(Post).filter(
            Post.id == alert_data.post_id,
            Post.college_id == current_user.college_id
        ).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
    
    # Create alert
    alert = Alert(
        user_id=alert_data.user_id,
        title=alert_data.title,
        message=alert_data.message,
        alert_type=alert_data.alert_type,
        expires_at=alert_data.expires_at,
        post_id=alert_data.post_id,
        college_id=current_user.college_id,
        created_by=current_user.id
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # Get creator name and post title for response
    creator_name = current_user.full_name
    post_title = None
    if alert.post_id:
        post = db.query(Post).filter(Post.id == alert.post_id).first()
        post_title = post.title if post else None
    
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
        "creator_name": creator_name,
        "post_title": post_title,
        "time_ago": calculate_time_ago(alert.created_at),
        "is_expired": is_alert_expired(alert.expires_at)
    }
    
    return AlertResponse(**alert_dict)


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an alert (enable/disable, mark as read, etc.)"""
    
    # Get alert - user can only modify their own alerts
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id,
        Alert.college_id == current_user.college_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Update fields
    update_data = alert_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)
    
    alert.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    
    # Get creator name and post title for response
    creator = db.query(User).filter(User.id == alert.created_by).first()
    creator_name = creator.full_name if creator else "Unknown"
    
    post_title = None
    if alert.post_id:
        post = db.query(Post).filter(Post.id == alert.post_id).first()
        post_title = post.title if post else None
    
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
        "creator_name": creator_name,
        "post_title": post_title,
        "time_ago": calculate_time_ago(alert.created_at),
        "is_expired": is_alert_expired(alert.expires_at)
    }
    
    return AlertResponse(**alert_dict)


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    
    # Get alert - user can only delete their own alerts
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id,
        Alert.college_id == current_user.college_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(alert)
    db.commit()
    
    return {"message": "Alert deleted successfully"}


@router.post("/mark-all-read")
async def mark_all_alerts_read(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all alerts as read for the current user"""
    
    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.college_id == current_user.college_id,
        Alert.is_read == False
    ).all()
    
    for alert in alerts:
        alert.is_read = True
        alert.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Marked {len(alerts)} alerts as read"}


@router.get("/unread-count")
async def get_unread_count(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unread alerts for the current user"""
    
    count = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.college_id == current_user.college_id,
        Alert.is_read == False,
        Alert.is_enabled == True,
        or_(Alert.expires_at.is_(None), Alert.expires_at > datetime.utcnow())
    ).count()
    
    return {"unread_count": count}