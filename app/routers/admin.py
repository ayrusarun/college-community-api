"""
Admin endpoints for managing users, roles, and permissions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user, get_password_hash
from ..core.rbac import RoleChecker, get_user_permissions
from ..models.models import User, Permission, UserCustomPermission, UserRole, College
from ..models.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


# Schemas
class RoleUpdateRequest(BaseModel):
    role: str  # 'admin', 'staff', 'student'


class UserStatusRequest(BaseModel):
    is_active: bool


class PermissionGrant(BaseModel):
    permission_name: str
    granted: bool


class UserPermissionResponse(BaseModel):
    user_id: int
    username: str
    role: str
    is_active: bool
    default_permissions: List[str]
    custom_permissions: List[dict]
    effective_permissions: List[str]


# Endpoints

@router.post("/users", response_model=UserResponse, dependencies=[Depends(RoleChecker(UserRole.ADMIN, UserRole.STAFF))])
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new user
    Requires: admin or staff role
    """
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if college exists and matches current user's college (unless admin creating for another college)
    college = db.query(College).filter(College.id == user.college_id).first()
    if not college:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="College not found"
        )
    
    # Staff can only create users in their own college
    if current_user.role == UserRole.STAFF and user.college_id != current_user.college_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create users in your own college"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        department=user.department,
        class_name=user.class_name,
        academic_year=user.academic_year,
        college_id=user.college_id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/users", dependencies=[Depends(RoleChecker(UserRole.ADMIN, UserRole.STAFF))])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    List all users in the same college
    Requires: admin or staff role
    """
    users = db.query(User).filter(
        User.college_id == current_user.college_id
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "department": user.department,
            "created_at": user.created_at
        }
        for user in users
    ]


@router.put("/users/{user_id}/role", dependencies=[Depends(RoleChecker(UserRole.ADMIN))])
async def update_user_role(
    user_id: int,
    role_data: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a user's role
    Requires: admin role
    """
    # Find the user
    user = db.query(User).filter(
        User.id == user_id,
        User.college_id == current_user.college_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from changing their own role
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Validate role
    try:
        new_role = UserRole(role_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: admin, staff, student"
        )
    
    user.role = new_role
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Role updated successfully",
        "user_id": user.id,
        "username": user.username,
        "new_role": user.role.value
    }


@router.put("/users/{user_id}/status", dependencies=[Depends(RoleChecker(UserRole.ADMIN))])
async def update_user_status(
    user_id: int,
    status_data: UserStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Activate or deactivate a user
    Requires: admin role
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.college_id == current_user.college_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own status"
        )
    
    user.is_active = status_data.is_active
    db.commit()
    db.refresh(user)
    
    return {
        "message": "User status updated successfully",
        "user_id": user.id,
        "username": user.username,
        "is_active": user.is_active
    }


@router.delete("/users/{user_id}", dependencies=[Depends(RoleChecker(UserRole.ADMIN))])
async def delete_user(
    user_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a user permanently
    Requires: admin role
    
    WARNING: This will permanently delete the user and all their associated data.
    Consider deactivating the user instead using PUT /admin/users/{user_id}/status
    
    Use ?force=true to delete a user with existing posts, rewards, or other data.
    Without force=true, users with existing content cannot be deleted.
    """
    from ..models.models import Post, Reward, RewardPoint, File, Alert, Order, AIConversation, Cart, WishlistItem, PointTransaction
    
    user = db.query(User).filter(
        User.id == user_id,
        User.college_id == current_user.college_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Check for existing data
    posts_count = db.query(Post).filter(Post.author_id == user_id).count()
    rewards_given = db.query(Reward).filter(Reward.giver_id == user_id).count()
    rewards_received = db.query(Reward).filter(Reward.receiver_id == user_id).count()
    files_count = db.query(File).filter(File.uploaded_by == user_id).count()
    alerts_created = db.query(Alert).filter(Alert.created_by == user_id).count()
    orders_count = db.query(Order).filter(Order.user_id == user_id).count()
    conversations_count = db.query(AIConversation).filter(AIConversation.user_id == user_id).count()
    
    total_data = posts_count + rewards_given + rewards_received + files_count + alerts_created + orders_count + conversations_count
    
    if total_data > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Cannot delete user with existing data",
                "message": "This user has existing posts, rewards, files, or other data. Use ?force=true to delete anyway, or deactivate the user instead.",
                "user_data": {
                    "posts": posts_count,
                    "rewards_given": rewards_given,
                    "rewards_received": rewards_received,
                    "files": files_count,
                    "alerts_created": alerts_created,
                    "orders": orders_count,
                    "conversations": conversations_count
                },
                "recommendation": f"Use PUT /admin/users/{user_id}/status with is_active=false to deactivate instead of deleting"
            }
        )
    
    username = user.username
    full_name = user.full_name
    
    # Always delete these relationships first (they exist for all users)
    db.query(RewardPoint).filter(RewardPoint.user_id == user_id).delete(synchronize_session=False)
    db.query(PointTransaction).filter(PointTransaction.user_id == user_id).delete(synchronize_session=False)
    db.query(WishlistItem).filter(WishlistItem.user_id == user_id).delete(synchronize_session=False)
    db.query(Cart).filter(Cart.user_id == user_id).delete(synchronize_session=False)
    db.query(UserCustomPermission).filter(UserCustomPermission.user_id == user_id).delete(synchronize_session=False)
    
    # If force=true, delete all content-related data
    if force and total_data > 0:
        # Delete posts
        db.query(Post).filter(Post.author_id == user_id).delete(synchronize_session=False)
        
        # Delete rewards (both given and received)
        db.query(Reward).filter(
            (Reward.giver_id == user_id) | (Reward.receiver_id == user_id)
        ).delete(synchronize_session=False)
        
        # Delete files
        db.query(File).filter(File.uploaded_by == user_id).delete(synchronize_session=False)
        
        # Delete alerts created by user
        db.query(Alert).filter(Alert.created_by == user_id).delete(synchronize_session=False)
        
        # Delete alerts for user
        db.query(Alert).filter(Alert.user_id == user_id).delete(synchronize_session=False)
        
        # Delete orders
        db.query(Order).filter(Order.user_id == user_id).delete(synchronize_session=False)
        
        # Delete AI conversations
        db.query(AIConversation).filter(AIConversation.user_id == user_id).delete(synchronize_session=False)
    
    # Delete the user
    db.delete(user)
    db.commit()
    
    return {
        "message": "User deleted successfully",
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "deleted_data": {
            "posts": posts_count,
            "rewards": rewards_given + rewards_received,
            "files": files_count,
            "alerts": alerts_created,
            "orders": orders_count,
            "conversations": conversations_count
        } if force else None,
        "warning": "This action is permanent and cannot be undone"
    }


@router.get("/users/{user_id}/permissions", dependencies=[Depends(RoleChecker(UserRole.ADMIN, UserRole.STAFF))])
async def get_user_permissions_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed permission information for a user
    Requires: admin or staff role
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.college_id == current_user.college_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get effective permissions
    effective_permissions = get_user_permissions(user, db)
    
    # Get custom permissions
    custom_perms = db.query(UserCustomPermission).filter(
        UserCustomPermission.user_id == user.id
    ).all()
    
    custom_permissions_list = []
    for cp in custom_perms:
        perm = db.query(Permission).filter(Permission.id == cp.permission_id).first()
        if perm:
            custom_permissions_list.append({
                "permission": perm.name,
                "granted": cp.granted,
                "resource": perm.resource,
                "action": perm.action
            })
    
    # Get default role permissions
    from ..core.rbac import ROLE_PERMISSIONS
    default_perms = list(ROLE_PERMISSIONS.get(user.role, set()))
    
    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value,
        "is_active": user.is_active,
        "default_permissions": sorted(default_perms),
        "custom_permissions": custom_permissions_list,
        "effective_permissions": sorted(list(effective_permissions))
    }


@router.post("/users/{user_id}/permissions", dependencies=[Depends(RoleChecker(UserRole.ADMIN))])
async def grant_or_revoke_permission(
    user_id: int,
    permission_data: PermissionGrant,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Grant or revoke a specific permission for a user
    Requires: admin role
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.college_id == current_user.college_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Find the permission
    permission = db.query(Permission).filter(
        Permission.name == permission_data.permission_name
    ).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission '{permission_data.permission_name}' not found"
        )
    
    # Check if custom permission already exists
    custom_perm = db.query(UserCustomPermission).filter(
        UserCustomPermission.user_id == user.id,
        UserCustomPermission.permission_id == permission.id
    ).first()
    
    if custom_perm:
        custom_perm.granted = permission_data.granted
    else:
        custom_perm = UserCustomPermission(
            user_id=user.id,
            permission_id=permission.id,
            granted=permission_data.granted
        )
        db.add(custom_perm)
    
    db.commit()
    
    action = "granted" if permission_data.granted else "revoked"
    return {
        "message": f"Permission {action} successfully",
        "user_id": user.id,
        "username": user.username,
        "permission": permission_data.permission_name,
        "granted": permission_data.granted
    }


@router.delete("/users/{user_id}/permissions/{permission_name}", dependencies=[Depends(RoleChecker(UserRole.ADMIN))])
async def remove_custom_permission(
    user_id: int,
    permission_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a custom permission override (user will fall back to role default)
    Requires: admin role
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.college_id == current_user.college_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    permission = db.query(Permission).filter(
        Permission.name == permission_name
    ).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission '{permission_name}' not found"
        )
    
    custom_perm = db.query(UserCustomPermission).filter(
        UserCustomPermission.user_id == user.id,
        UserCustomPermission.permission_id == permission.id
    ).first()
    
    if not custom_perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom permission not found"
        )
    
    db.delete(custom_perm)
    db.commit()
    
    return {
        "message": "Custom permission removed successfully",
        "user_id": user.id,
        "username": user.username,
        "permission": permission_name
    }


@router.get("/permissions", dependencies=[Depends(RoleChecker(UserRole.ADMIN, UserRole.STAFF))])
async def list_all_permissions(db: Session = Depends(get_db)):
    """
    List all available permissions in the system
    Requires: admin or staff role
    """
    permissions = db.query(Permission).all()
    
    # Group by resource
    by_resource = {}
    for perm in permissions:
        if perm.resource not in by_resource:
            by_resource[perm.resource] = []
        by_resource[perm.resource].append({
            "id": perm.id,
            "name": perm.name,
            "action": perm.action,
            "description": perm.description
        })
    
    return by_resource


@router.get("/roles", dependencies=[Depends(RoleChecker(UserRole.ADMIN, UserRole.STAFF))])
async def list_roles():
    """
    List all available roles and their default permissions
    Requires: admin or staff role
    """
    from ..core.rbac import ROLE_PERMISSIONS
    
    return {
        "roles": [
            {
                "name": role.value,
                "permissions": sorted(list(perms))
            }
            for role, perms in ROLE_PERMISSIONS.items()
        ]
    }
