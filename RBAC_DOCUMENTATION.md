# RBAC (Role-Based Access Control) Implementation Guide

## Overview

This system implements a comprehensive Role-Based Access Control (RBAC) system with three user roles and granular permissions for all API resources.

## User Roles

### 1. Student (Default)
- **Basic Access**: Can create and manage their own content
- **Read Access**: View posts, alerts, files, rewards, store items
- **Write Access**: Create posts, upload files, redeem rewards, make purchases
- **Restrictions**: Cannot manage others' content or system settings

### 2. Staff
- **Extended Access**: Can moderate content and manage events
- **Manage Permissions**: Posts, alerts, store management
- **User Management**: View and update user information
- **Restrictions**: Cannot manage system users or access admin features

### 3. Admin
- **Full Access**: Complete control over the system
- **User Management**: Create, update, deactivate users, manage roles
- **Permission Management**: Grant/revoke custom permissions
- **System Access**: All resources and administrative functions

## Permission System

### Permission Format
Permissions follow the format: `action:resource`

- **action**: read, write, update, delete, manage
- **resource**: posts, alerts, files, folders, rewards, store, users, ai

### Available Permissions

#### Posts
- `read:posts` - View posts
- `write:posts` - Create posts
- `update:posts` - Edit posts
- `delete:posts` - Delete posts
- `manage:posts` - Moderate/manage all posts

#### Alerts
- `read:alerts` - View alerts
- `write:alerts` - Create alerts
- `update:alerts` - Edit alerts
- `delete:alerts` - Delete alerts
- `manage:alerts` - Manage all alerts

#### Files
- `read:files` - View/download files
- `write:files` - Upload files
- `update:files` - Edit file metadata
- `delete:files` - Delete files
- `manage:files` - Manage all files

#### Folders
- `read:folders` - Browse folders
- `write:folders` - Create folders
- `update:folders` - Move/rename folders
- `delete:folders` - Delete folders
- `manage:folders` - Manage all folders

#### Rewards
- `read:rewards` - View rewards
- `write:rewards` - Redeem rewards
- `manage:rewards` - Create/manage reward system

#### Store
- `read:store` - View store items
- `write:store` - Make purchases/add to wishlist
- `manage:store` - Manage store inventory and orders

#### Users
- `read:users` - View user profiles
- `write:users` - Create users
- `update:users` - Edit user information
- `delete:users` - Delete users
- `manage:users` - Full user management

#### AI
- `read:ai` - Use AI features
- `manage:ai` - Manage AI settings

## Default Role Permissions

### Student Permissions
```
read:posts, write:posts, update:posts, delete:posts
read:alerts
read:files, write:files, update:files, delete:files
read:folders, write:folders, update:folders, delete:folders
read:rewards, write:rewards
read:store, write:store
read:users
read:ai
```

### Staff Permissions
```
All Student permissions, plus:
manage:posts
write:alerts, update:alerts, delete:alerts, manage:alerts
update:users
manage:store
```

### Admin Permissions
```
All Staff permissions, plus:
manage:files, manage:folders
manage:rewards
write:users, delete:users, manage:users
manage:ai
```

## API Endpoints

### Authentication

#### Login
```http
POST /auth/login
```
Returns JWT token with role information.

#### Get Current User
```http
GET /auth/me
```
Returns user profile with role and effective permissions.

### Admin Endpoints

#### List Users
```http
GET /admin/users?skip=0&limit=100
```
**Required Role**: Admin or Staff

**Response**:
```json
[
  {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe",
    "email": "john@example.com",
    "role": "student",
    "is_active": true,
    "department": "Computer Science",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

#### Update User Role
```http
PUT /admin/users/{user_id}/role
```
**Required Role**: Admin

**Request Body**:
```json
{
  "role": "staff"
}
```

**Response**:
```json
{
  "message": "Role updated successfully",
  "user_id": 1,
  "username": "john_doe",
  "new_role": "staff"
}
```

#### Update User Status
```http
PUT /admin/users/{user_id}/status
```
**Required Role**: Admin

**Request Body**:
```json
{
  "is_active": false
}
```

**Response**:
```json
{
  "message": "User status updated successfully",
  "user_id": 1,
  "username": "john_doe",
  "is_active": false
}
```

#### Get User Permissions
```http
GET /admin/users/{user_id}/permissions
```
**Required Role**: Admin or Staff

**Response**:
```json
{
  "user_id": 1,
  "username": "john_doe",
  "role": "student",
  "is_active": true,
  "default_permissions": [
    "read:posts",
    "write:posts",
    "read:files"
  ],
  "custom_permissions": [
    {
      "permission": "manage:posts",
      "granted": true,
      "resource": "posts",
      "action": "manage"
    }
  ],
  "effective_permissions": [
    "read:posts",
    "write:posts",
    "read:files",
    "manage:posts"
  ]
}
```

#### Grant or Revoke Permission
```http
POST /admin/users/{user_id}/permissions
```
**Required Role**: Admin

**Request Body**:
```json
{
  "permission_name": "manage:posts",
  "granted": true
}
```

**Response**:
```json
{
  "message": "Permission granted successfully",
  "user_id": 1,
  "username": "john_doe",
  "permission": "manage:posts",
  "granted": true
}
```

#### Remove Custom Permission
```http
DELETE /admin/users/{user_id}/permissions/{permission_name}
```
**Required Role**: Admin

Removes custom permission override, user falls back to role default.

#### List All Permissions
```http
GET /admin/permissions
```
**Required Role**: Admin or Staff

**Response**:
```json
{
  "posts": [
    {
      "id": 1,
      "name": "read:posts",
      "action": "read",
      "description": "View posts"
    }
  ],
  "files": [...]
}
```

#### List Roles
```http
GET /admin/roles
```
**Required Role**: Admin or Staff

**Response**:
```json
{
  "roles": [
    {
      "name": "student",
      "permissions": ["read:posts", "write:posts", ...]
    },
    {
      "name": "staff",
      "permissions": [...]
    },
    {
      "name": "admin",
      "permissions": [...]
    }
  ]
}
```

## Using RBAC in Your Code

### Method 1: Using Dependencies

```python
from fastapi import APIRouter, Depends
from app.core.rbac import PermissionChecker, RoleChecker
from app.models.models import UserRole

router = APIRouter()

# Require specific permission
@router.post("/posts")
async def create_post(
    _: None = Depends(PermissionChecker("write:posts"))
):
    # Only users with write:posts permission can access
    pass

# Require specific role
@router.get("/admin/settings")
async def get_settings(
    _: None = Depends(RoleChecker(UserRole.ADMIN))
):
    # Only admins can access
    pass

# Require one of multiple roles
@router.get("/staff/dashboard")
async def staff_dashboard(
    _: None = Depends(RoleChecker(UserRole.ADMIN, UserRole.STAFF))
):
    # Admins or staff can access
    pass
```

### Method 2: Manual Permission Checking

```python
from app.core.rbac import has_permission, has_role
from app.models.models import UserRole

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    
    # User can delete own posts or if they have manage:posts
    if post.user_id != current_user.id:
        if not has_permission(current_user, "manage:posts", db):
            raise HTTPException(status_code=403, detail="Permission denied")
    
    # Delete post
    db.delete(post)
    db.commit()
```

### Method 3: Ownership or Permission

```python
from app.core.rbac import check_ownership

@router.put("/posts/{post_id}")
async def update_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    
    # Allow if user owns post OR has manage:posts permission
    if not check_ownership(current_user, post.user_id, "manage:posts"):
        if not has_permission(current_user, "manage:posts", db):
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update post
    # ...
```

## Database Schema

### Users Table (Modified)
```sql
ALTER TABLE users ADD COLUMN role user_role DEFAULT 'student';
ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT true;
```

### Permissions Table
```sql
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT
);
```

### Role Permissions Table
```sql
CREATE TABLE role_permissions (
    id SERIAL PRIMARY KEY,
    role user_role NOT NULL,
    permission_id INTEGER REFERENCES permissions(id),
    college_id INTEGER REFERENCES colleges(id),
    UNIQUE(role, permission_id, college_id)
);
```

### User Custom Permissions Table
```sql
CREATE TABLE user_custom_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    permission_id INTEGER REFERENCES permissions(id),
    granted BOOLEAN NOT NULL,
    UNIQUE(user_id, permission_id)
);
```

## Migration

Run the RBAC migration:

```bash
# Inside Docker container
docker-compose exec web python db_setup.py --migrate

# Or run directly in database
docker-compose exec db psql -U postgres -d college_community -f /app/migrations/20241116_120000_add_rbac_system.sql
```

## Testing RBAC

### 1. Create Test Users with Different Roles

```bash
# Login and get token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# Check current user info
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Test Permission Checking

```bash
# Try to access admin endpoint as student (should fail)
curl http://localhost:8000/admin/users \
  -H "Authorization: Bearer $STUDENT_TOKEN"

# Access same endpoint as admin (should succeed)
curl http://localhost:8000/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 3. Test Custom Permissions

```bash
# Grant manage:posts to a student
curl -X POST http://localhost:8000/admin/users/123/permissions \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"permission_name":"manage:posts","granted":true}'

# Verify student now has manage:posts
curl http://localhost:8000/admin/users/123/permissions \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Best Practices

1. **Default to Least Privilege**: Start users as students, promote as needed
2. **Use Custom Permissions Sparingly**: Prefer role changes over many custom permissions
3. **Check Ownership First**: For user-generated content, check ownership before permissions
4. **Log Permission Changes**: Track all role and permission modifications
5. **Regular Audits**: Review user roles and custom permissions periodically
6. **Multi-Tenant Isolation**: All permission checks respect college_id boundaries

## Common Scenarios

### Scenario 1: Student Becomes Class Representative
```bash
# Grant manage:alerts permission to student
POST /admin/users/123/permissions
{
  "permission_name": "manage:alerts",
  "granted": true
}
```

### Scenario 2: Staff Member Leaves
```bash
# Deactivate user instead of deleting
PUT /admin/users/456/status
{
  "is_active": false
}
```

### Scenario 3: Promote Student to Staff
```bash
# Change role (automatically gets staff permissions)
PUT /admin/users/789/role
{
  "role": "staff"
}
```

### Scenario 4: Temporary Admin Access
```bash
# Grant specific admin permissions
POST /admin/users/234/permissions
{
  "permission_name": "manage:users",
  "granted": true
}

# Later revoke
DELETE /admin/users/234/permissions/manage:users
```

## Troubleshooting

### User Can't Access Endpoint
1. Check if user is active: `GET /auth/me`
2. Verify required permission: `GET /admin/users/{user_id}/permissions`
3. Check endpoint permission requirement in code
4. Ensure college_id matches for multi-tenant isolation

### Permission Not Working
1. Verify permission exists: `GET /admin/permissions`
2. Check permission name spelling (case-sensitive)
3. Confirm custom permission not overriding role default
4. Check database migration was applied

### Role Change Not Reflected
1. User must log out and log back in (new JWT token needed)
2. JWT tokens include role at creation time
3. Check token expiry time in settings

## Security Considerations

1. **JWT Tokens**: Include role, regenerate on role change
2. **College Isolation**: All queries filter by college_id
3. **Active Status**: Inactive users rejected at login
4. **Self-Modification**: Users cannot change their own role or status
5. **Permission Hierarchy**: Admin > Staff > Student
6. **Audit Trail**: Consider logging all admin actions

## Future Enhancements

1. **Dynamic Permissions**: Load from database instead of hardcoded
2. **Permission Groups**: Create permission sets for common roles
3. **Temporary Permissions**: Time-limited access grants
4. **Permission History**: Track when permissions were granted/revoked
5. **Resource-Level Permissions**: Per-folder or per-post permissions
6. **API Rate Limiting**: Different limits per role

## Related Documentation

- [API Documentation](api-documentation.md)
- [Database Migrations](DATABASE_MIGRATIONS.md)
- [Security Guide](SECURITY.md)
- [Admin Panel Integration](flutter-guide.md)
