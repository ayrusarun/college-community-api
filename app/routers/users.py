from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..core.rbac import get_user_permissions
from ..models.models import User, College
from ..models.schemas import UserResponse, UserProfile
from ..routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    college = db.query(College).filter(College.id == current_user.college_id).first()
    permissions = list(get_user_permissions(current_user, db))
    
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        department=current_user.department,
        class_name=current_user.class_name,
        academic_year=current_user.academic_year,
        college_id=current_user.college_id,
        role=current_user.role.value,  # ✅ Add role
        is_active=current_user.is_active,  # ✅ Add is_active
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        college_name=college.name,
        college_slug=college.slug,
        permissions=sorted(permissions)  # ✅ Add permissions
    )


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only return users from the same college (multi-tenant)
    users = db.query(User).filter(
        User.college_id == current_user.college_id
    ).offset(skip).limit(limit).all()
    
    return users


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id,
        User.college_id == current_user.college_id  # Multi-tenant check
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    college = db.query(College).filter(College.id == user.college_id).first()
    
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        department=user.department,
        class_name=user.class_name,
        academic_year=user.academic_year,
        college_id=user.college_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        college_name=college.name,
        college_slug=college.slug
    )