"""
RBAC (Role-Based Access Control) utilities
Provides decorators and functions for permission checking
"""

from functools import wraps
from typing import List, Set
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.security import get_current_user
from ..core.database import get_db
from ..models.models import User, Permission, RolePermission, UserCustomPermission, UserRole


# Default permissions for each role
ROLE_PERMISSIONS = {
    UserRole.STUDENT: {
        # Posts
        'read:posts', 'write:posts', 'update:posts', 'delete:posts',
        # Alerts
        'read:alerts',
        # Files
        'read:files', 'write:files', 'update:files', 'delete:files',
        # Folders
        'read:folders', 'write:folders', 'update:folders', 'delete:folders',
        # Rewards
        'read:rewards', 'write:rewards',
        # Store
        'read:store', 'write:store',
        # Users
        'read:users',
        # AI
        'read:ai',
    },
    UserRole.STAFF: {
        # Posts
        'read:posts', 'write:posts', 'update:posts', 'delete:posts', 'manage:posts',
        # Alerts
        'read:alerts', 'write:alerts', 'update:alerts', 'delete:alerts', 'manage:alerts',
        # Files
        'read:files', 'write:files', 'update:files', 'delete:files',
        # Folders
        'read:folders', 'write:folders', 'update:folders', 'delete:folders',
        # Rewards
        'read:rewards', 'write:rewards',
        # Store
        'read:store', 'write:store', 'manage:store',
        # Users
        'read:users', 'update:users',
        # AI
        'read:ai',
    },
    UserRole.ADMIN: {
        # Posts
        'read:posts', 'write:posts', 'update:posts', 'delete:posts', 'manage:posts',
        # Alerts
        'read:alerts', 'write:alerts', 'update:alerts', 'delete:alerts', 'manage:alerts',
        # Files
        'read:files', 'write:files', 'update:files', 'delete:files', 'manage:files',
        # Folders
        'read:folders', 'write:folders', 'update:folders', 'delete:folders', 'manage:folders',
        # Rewards
        'read:rewards', 'write:rewards', 'manage:rewards',
        # Store
        'read:store', 'write:store', 'manage:store',
        # Users
        'read:users', 'write:users', 'update:users', 'delete:users', 'manage:users',
        # AI
        'read:ai', 'manage:ai',
    }
}


def get_user_permissions(user: User, db: Session) -> Set[str]:
    """
    Get all permissions for a user based on role and custom permissions
    """
    # Start with role-based permissions
    permissions = set(ROLE_PERMISSIONS.get(user.role, set()))
    
    # Apply custom permissions (overrides)
    custom_perms = db.query(UserCustomPermission).filter(
        UserCustomPermission.user_id == user.id
    ).all()
    
    for custom_perm in custom_perms:
        perm = db.query(Permission).filter(Permission.id == custom_perm.permission_id).first()
        if perm:
            if custom_perm.granted:
                permissions.add(perm.name)
            else:
                permissions.discard(perm.name)
    
    return permissions


def has_permission(user: User, required_permission: str, db: Session) -> bool:
    """
    Check if user has a specific permission
    """
    if not user.is_active:
        return False
    
    user_permissions = get_user_permissions(user, db)
    return required_permission in user_permissions


def has_any_permission(user: User, required_permissions: List[str], db: Session) -> bool:
    """
    Check if user has any of the required permissions
    """
    if not user.is_active:
        return False
    
    user_permissions = get_user_permissions(user, db)
    return any(perm in user_permissions for perm in required_permissions)


def has_all_permissions(user: User, required_permissions: List[str], db: Session) -> bool:
    """
    Check if user has all required permissions
    """
    if not user.is_active:
        return False
    
    user_permissions = get_user_permissions(user, db)
    return all(perm in user_permissions for perm in required_permissions)


def has_role(user: User, required_roles: List[UserRole]) -> bool:
    """
    Check if user has one of the required roles
    """
    if not user.is_active:
        return False
    
    return user.role in required_roles


def require_permission(permission: str):
    """
    Decorator to require a specific permission for an endpoint
    Usage:
        @router.post("/posts")
        @require_permission("write:posts")
        async def create_post(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user and db from kwargs
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing authentication or database dependency"
                )
            
            if not has_permission(current_user, permission, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles: UserRole):
    """
    Decorator to require specific roles for an endpoint
    Usage:
        @router.post("/admin/users")
        @require_role(UserRole.ADMIN, UserRole.STAFF)
        async def create_user(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing authentication dependency"
                )
            
            if not has_role(current_user, list(roles)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join([r.value for r in roles])}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Dependency for permission checking
class PermissionChecker:
    """
    FastAPI dependency for checking permissions
    Usage:
        @router.post("/posts")
        async def create_post(
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db),
            _: None = Depends(PermissionChecker("write:posts"))
        ):
            ...
    """
    def __init__(self, permission: str):
        self.permission = permission
    
    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if not has_permission(current_user, self.permission, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {self.permission}"
            )
        return None


# Dependency for role checking
class RoleChecker:
    """
    FastAPI dependency for checking roles
    Usage:
        @router.post("/admin/settings")
        async def update_settings(
            current_user: User = Depends(get_current_user),
            _: None = Depends(RoleChecker(UserRole.ADMIN))
        ):
            ...
    """
    def __init__(self, *roles: UserRole):
        self.roles = roles
    
    def __call__(self, current_user: User = Depends(get_current_user)):
        if not has_role(current_user, list(self.roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join([r.value for r in self.roles])}"
            )
        return None


# Helper to check if user owns a resource
def check_ownership(user: User, resource_owner_id: int, permission: str = None):
    """
    Check if user owns a resource or has manage permission
    
    Args:
        user: Current user
        resource_owner_id: ID of the resource owner
        permission: Optional manage permission to check (e.g., 'manage:posts')
    
    Returns:
        True if user owns resource or has manage permission
    """
    # Owner can always access
    if user.id == resource_owner_id:
        return True
    
    # Admin/Staff with manage permission can access
    if permission and user.role in [UserRole.ADMIN, UserRole.STAFF]:
        return True
    
    return False


def require_ownership_or_permission(resource_owner_id: int, permission: str = None):
    """
    Check if user is the owner or has the required permission
    Raises HTTPException if neither condition is met
    """
    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if not check_ownership(current_user, resource_owner_id, permission):
            if permission and has_permission(current_user, permission, db):
                return None
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resource"
            )
        return None
    return checker
