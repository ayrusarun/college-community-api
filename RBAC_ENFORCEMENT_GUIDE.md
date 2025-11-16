# RBAC Enforcement Guide

## The Problem

Currently, even though we have the RBAC system in place, **most endpoints are not protected**. This means:

❌ A student with a valid token can access `/admin/users` endpoints
❌ A student can call `/admin/users/{id}/role` to change roles
❌ No permission checking happens automatically

## The Solution: Three Approaches

### Approach 1: Using Dependencies (RECOMMENDED)

This is the **easiest and cleanest** approach. Add the permission checker as a dependency:

```python
from app.core.rbac import PermissionChecker, RoleChecker
from app.models.models import UserRole

# Before (NOT PROTECTED):
@router.post("/posts")
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Anyone with a token can access!
    pass

# After (PROTECTED):
@router.post("/posts")
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("write:posts"))  # ✅ Protection added
):
    # Only users with write:posts permission can access
    pass
```

### Approach 2: Using Role-Based Dependencies

For admin-only endpoints:

```python
# Admin only
@router.put("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: RoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(RoleChecker(UserRole.ADMIN))  # ✅ Only admins
):
    pass

# Admin or Staff
@router.get("/admin/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(RoleChecker(UserRole.ADMIN, UserRole.STAFF))  # ✅ Admin or Staff
):
    pass
```

### Approach 3: Route-Level Dependencies

Apply protection to **all endpoints in a router** at once:

```python
from app.core.rbac import RoleChecker
from app.models.models import UserRole

# Protect entire router
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(RoleChecker(UserRole.ADMIN))]  # ✅ All endpoints require admin
)

# All endpoints in this router automatically require admin role
@router.get("/users")
async def list_users(...):
    pass

@router.put("/users/{id}/role")
async def update_role(...):
    pass
```

## What Happens Without Protection?

Let me demonstrate with a real example:

### Scenario: Student Accessing Admin Endpoint

```bash
# Student logs in
STUDENT_TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"password"}' \
  | jq -r '.access_token')

# Without protection, student CAN access admin endpoint!
curl http://localhost:8000/admin/users \
  -H "Authorization: Bearer $STUDENT_TOKEN"
# ❌ Returns user list (SECURITY BREACH!)

# With protection:
# ✅ Returns 403 Forbidden: "Access denied. Required roles: admin"
```

## How to Protect All Existing Endpoints

### Posts Router Example

**Before:**
```python
@router.post("/posts", response_model=PostResponse)
async def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Not protected!
```

**After:**
```python
@router.post("/posts", response_model=PostResponse)
async def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("write:posts"))
):
    # ✅ Protected!
```

### Files Router Example

```python
@router.post("/files/upload")
async def upload_file(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("write:files"))  # ✅ Add this
):
    pass

@router.get("/files")
async def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("read:files"))  # ✅ Add this
):
    pass

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("delete:files"))  # ✅ Add this
):
    # Also check ownership
    file = db.query(File).filter(File.id == file_id).first()
    if file.user_id != current_user.id:
        if not has_permission(current_user, "manage:files", db):
            raise HTTPException(status_code=403)
    # Delete file...
```

## Quick Migration Checklist

### ✅ Endpoints That Need Protection

- [ ] **Posts**: read, write, update, delete
- [ ] **Alerts**: read, write, update, delete, manage
- [ ] **Files**: read, write, update, delete
- [ ] **Folders**: read, write, update, delete
- [ ] **Rewards**: read, write, manage
- [ ] **Store**: read, write, manage
- [ ] **Users**: read, update, manage
- [ ] **AI**: read, manage

### Required Permissions by Endpoint

```python
# Posts
GET    /posts                -> read:posts
POST   /posts                -> write:posts
PUT    /posts/{id}           -> update:posts (or ownership)
DELETE /posts/{id}           -> delete:posts (or ownership)

# Alerts
GET    /alerts               -> read:alerts
POST   /alerts               -> write:alerts (staff+)
PUT    /alerts/{id}          -> update:alerts (staff+)
DELETE /alerts/{id}          -> delete:alerts (staff+)

# Files
GET    /files                -> read:files
POST   /files/upload         -> write:files
PUT    /files/{id}           -> update:files (or ownership)
DELETE /files/{id}           -> delete:files (or ownership)

# Folders
GET    /folders/browse       -> read:folders
POST   /folders/create       -> write:folders
PUT    /folders/move         -> update:folders
DELETE /folders/delete       -> delete:folders

# Rewards
GET    /rewards              -> read:rewards
POST   /rewards/redeem       -> write:rewards
POST   /rewards/create       -> manage:rewards (staff+)

# Store
GET    /store/items          -> read:store
POST   /store/purchase       -> write:store
POST   /store/items          -> manage:store (staff+)

# Admin (all require admin role)
ALL    /admin/*              -> admin role
```

## Testing Protection

### Test Script

```bash
#!/bin/bash

# Get tokens for different roles
STUDENT_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"password"}' \
  | jq -r '.access_token')

ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

echo "Testing Student Access to Admin Endpoint..."
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
  http://localhost:8000/admin/users \
  -H "Authorization: Bearer $STUDENT_TOKEN")

if [ "$RESPONSE" = "403" ]; then
  echo "✅ PASS: Student correctly blocked from admin endpoint"
else
  echo "❌ FAIL: Student accessed admin endpoint (got $RESPONSE)"
fi

echo "Testing Admin Access to Admin Endpoint..."
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
  http://localhost:8000/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if [ "$RESPONSE" = "200" ]; then
  echo "✅ PASS: Admin can access admin endpoint"
else
  echo "❌ FAIL: Admin blocked from admin endpoint (got $RESPONSE)"
fi
```

## Common Patterns

### Pattern 1: User Owns Resource OR Has Permission

```python
from app.core.rbac import has_permission

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    
    # Allow if: owns post OR has manage:posts permission
    if post.user_id != current_user.id:
        if not has_permission(current_user, "manage:posts", db):
            raise HTTPException(
                status_code=403,
                detail="You can only delete your own posts"
            )
    
    db.delete(post)
    db.commit()
```

### Pattern 2: Different Actions Based on Role

```python
@router.get("/posts")
async def list_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("read:posts"))
):
    query = db.query(Post).filter(Post.college_id == current_user.college_id)
    
    # Students see only active posts
    if current_user.role == UserRole.STUDENT:
        query = query.filter(Post.is_active == True)
    
    # Staff/Admin see all posts (including inactive)
    return query.all()
```

### Pattern 3: Conditional Permission Requirement

```python
@router.put("/alerts/{alert_id}")
async def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    # Created by user? Can edit (if still editable)
    if alert.created_by == current_user.id:
        # Students can only edit their own alerts within 24 hours
        if current_user.role == UserRole.STUDENT:
            if (datetime.now() - alert.created_at).hours > 24:
                raise HTTPException(403, "Edit window expired")
    else:
        # Not owner? Need manage:alerts permission
        if not has_permission(current_user, "manage:alerts", db):
            raise HTTPException(403, "Permission denied")
    
    # Update alert...
```

## Performance Considerations

The permission checking queries the database on each request. For high-traffic applications:

### Option 1: Cache User Permissions in JWT

```python
# During login, include permissions in token
access_token = create_access_token(
    data={
        "sub": user.username,
        "role": user.role.value,
        "permissions": list(get_user_permissions(user, db))  # Cache in token
    }
)
```

### Option 2: Redis Cache

```python
# Cache permissions for 5 minutes
from redis import Redis
redis_client = Redis()

def get_user_permissions_cached(user_id: int, db: Session):
    cache_key = f"permissions:{user_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return set(json.loads(cached))
    
    perms = get_user_permissions(user, db)
    redis_client.setex(cache_key, 300, json.dumps(list(perms)))
    return perms
```

## Summary

**Without adding permission checks:**
- ❌ Any authenticated user can access any endpoint
- ❌ Students can call admin APIs
- ❌ No enforcement of role-based access

**After adding permission checks:**
- ✅ Each endpoint validates required permissions
- ✅ 403 Forbidden for insufficient permissions
- ✅ Automatic enforcement of RBAC rules
- ✅ Custom permissions properly applied

**Next Steps:**
1. I'll update all existing routers to add permission checks
2. Test with student/staff/admin tokens
3. Document which permissions each endpoint requires
4. Create automated tests for RBAC enforcement

Would you like me to go ahead and add the permission checks to all existing endpoints?
