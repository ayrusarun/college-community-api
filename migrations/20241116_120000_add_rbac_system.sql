-- Name: Add RBAC (Role-Based Access Control) System
-- Description: Adds roles, permissions, and scopes for fine-grained access control
-- Version: 20241116_add_rbac_system
-- Created: 2024-11-16
-- Idempotent: Can be run multiple times safely

-- Create role enum type (only if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('admin', 'staff', 'student');
        RAISE NOTICE 'Created user_role enum type';
    ELSE
        RAISE NOTICE 'user_role enum type already exists, skipping';
    END IF;
END $$;

-- Add role column to users table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'role') THEN
        ALTER TABLE users ADD COLUMN role user_role DEFAULT 'student' NOT NULL;
        RAISE NOTICE 'Added role column to users table';
    ELSE
        RAISE NOTICE 'role column already exists in users table, skipping';
    END IF;
END $$;

-- Add is_active column for account management
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'is_active') THEN
        ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;
        RAISE NOTICE 'Added is_active column to users table';
    ELSE
        RAISE NOTICE 'is_active column already exists in users table, skipping';
    END IF;
END $$;

-- Create permissions table for granular access control
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'read:posts', 'write:posts'
    resource VARCHAR(50) NOT NULL,      -- e.g., 'posts', 'files', 'alerts'
    action VARCHAR(50) NOT NULL,        -- e.g., 'read', 'write', 'delete'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create role_permissions junction table
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role user_role NOT NULL,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    college_id INTEGER REFERENCES colleges(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role, permission_id, college_id)
);

-- Create user_custom_permissions for user-specific overrides
CREATE TABLE IF NOT EXISTS user_custom_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    granted BOOLEAN DEFAULT TRUE NOT NULL,  -- TRUE = grant, FALSE = revoke
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(id),
    UNIQUE(user_id, permission_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role, college_id);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role);
CREATE INDEX IF NOT EXISTS idx_user_custom_permissions_user ON user_custom_permissions(user_id);

-- Insert default permissions for all resources
INSERT INTO permissions (name, resource, action, description) VALUES
-- Posts permissions
('read:posts', 'posts', 'read', 'View posts'),
('write:posts', 'posts', 'write', 'Create posts'),
('update:posts', 'posts', 'update', 'Update own posts'),
('delete:posts', 'posts', 'delete', 'Delete own posts'),
('manage:posts', 'posts', 'manage', 'Manage all posts (admin only)'),

-- Alerts permissions
('read:alerts', 'alerts', 'read', 'View alerts'),
('write:alerts', 'alerts', 'write', 'Create alerts'),
('update:alerts', 'alerts', 'update', 'Update own alerts'),
('delete:alerts', 'alerts', 'delete', 'Delete own alerts'),
('manage:alerts', 'alerts', 'manage', 'Manage all alerts (admin/staff only)'),

-- Files permissions
('read:files', 'files', 'read', 'View and download files'),
('write:files', 'files', 'write', 'Upload files'),
('update:files', 'files', 'update', 'Update own files'),
('delete:files', 'files', 'delete', 'Delete own files'),
('manage:files', 'files', 'manage', 'Manage all files (admin only)'),

-- Folders permissions
('read:folders', 'folders', 'read', 'Browse folders'),
('write:folders', 'folders', 'write', 'Create folders'),
('update:folders', 'folders', 'update', 'Update own folders'),
('delete:folders', 'folders', 'delete', 'Delete own folders'),
('manage:folders', 'folders', 'manage', 'Manage all folders (admin only)'),

-- Rewards permissions
('read:rewards', 'rewards', 'read', 'View rewards'),
('write:rewards', 'rewards', 'write', 'Give rewards'),
('manage:rewards', 'rewards', 'manage', 'Manage reward system (admin only)'),

-- Store permissions
('read:store', 'store', 'read', 'View store products'),
('write:store', 'store', 'write', 'Purchase products'),
('manage:store', 'store', 'manage', 'Manage store products (admin/staff only)'),

-- Users permissions
('read:users', 'users', 'read', 'View user profiles'),
('write:users', 'users', 'write', 'Create users'),
('update:users', 'users', 'update', 'Update user profiles'),
('delete:users', 'users', 'delete', 'Delete users'),
('manage:users', 'users', 'manage', 'Manage all users (admin only)'),

-- AI permissions
('read:ai', 'ai', 'read', 'Query AI assistant'),
('manage:ai', 'ai', 'manage', 'Manage AI indexing (admin only)')
ON CONFLICT (name) DO NOTHING;

-- Set default role for existing users (idempotent)
UPDATE users SET role = 'student' WHERE role IS NULL;
UPDATE users SET is_active = TRUE WHERE is_active IS NULL;

-- Populate role_permissions for all colleges (idempotent)
DO $$
DECLARE
    college_record RECORD;
BEGIN
    -- For each college, insert role-permission mappings
    FOR college_record IN SELECT id FROM colleges LOOP
        
        -- STUDENT PERMISSIONS (19 permissions)
        INSERT INTO role_permissions (role, permission_id, college_id)
        SELECT 'student'::user_role, p.id, college_record.id
        FROM permissions p
        WHERE p.name IN (
            'read:posts', 'write:posts', 'update:posts', 'delete:posts',
            'read:alerts', 
            'read:files', 'write:files', 'update:files', 'delete:files',
            'read:folders', 'write:folders', 'update:folders', 'delete:folders',
            'read:rewards', 'write:rewards',
            'read:store', 'write:store',
            'read:users',
            'read:ai'
        )
        ON CONFLICT (role, permission_id, college_id) DO NOTHING;

        -- STAFF PERMISSIONS (24 permissions - includes student permissions + management)
        INSERT INTO role_permissions (role, permission_id, college_id)
        SELECT 'staff'::user_role, p.id, college_record.id
        FROM permissions p
        WHERE p.name IN (
            'read:posts', 'write:posts', 'update:posts', 'delete:posts', 'manage:posts',
            'read:alerts', 'write:alerts', 'update:alerts', 'delete:alerts', 'manage:alerts',
            'read:files', 'write:files', 'update:files', 'delete:files',
            'read:folders', 'write:folders', 'update:folders', 'delete:folders',
            'read:rewards', 'write:rewards',
            'read:store', 'write:store', 'manage:store',
            'read:users', 'update:users',
            'read:ai'
        )
        ON CONFLICT (role, permission_id, college_id) DO NOTHING;

        -- ADMIN PERMISSIONS (all 34 permissions)
        INSERT INTO role_permissions (role, permission_id, college_id)
        SELECT 'admin'::user_role, p.id, college_record.id
        FROM permissions p
        ON CONFLICT (role, permission_id, college_id) DO NOTHING;

    END LOOP;
    
    RAISE NOTICE 'Role permissions populated for all colleges';
END $$;

-- Create or replace function to get default permissions for a role
CREATE OR REPLACE FUNCTION get_default_role_permissions()
RETURNS TABLE(role_name user_role, permission_names TEXT[]) AS $$
BEGIN
    -- Student default permissions (read-only mostly)
    RETURN QUERY SELECT 
        'student'::user_role,
        ARRAY[
            'read:posts', 'write:posts', 'update:posts', 'delete:posts',
            'read:alerts',
            'read:files', 'write:files', 'update:files', 'delete:files',
            'read:folders', 'write:folders', 'update:folders', 'delete:folders',
            'read:rewards', 'write:rewards',
            'read:store', 'write:store',
            'read:users',
            'read:ai'
        ]::TEXT[];
    
    -- Staff permissions (more access)
    RETURN QUERY SELECT 
        'staff'::user_role,
        ARRAY[
            'read:posts', 'write:posts', 'update:posts', 'delete:posts', 'manage:posts',
            'read:alerts', 'write:alerts', 'update:alerts', 'delete:alerts', 'manage:alerts',
            'read:files', 'write:files', 'update:files', 'delete:files',
            'read:folders', 'write:folders', 'update:folders', 'delete:folders',
            'read:rewards', 'write:rewards',
            'read:store', 'write:store', 'manage:store',
            'read:users', 'update:users',
            'read:ai'
        ]::TEXT[];
    
    -- Admin permissions (full access)
    RETURN QUERY SELECT 
        'admin'::user_role,
        ARRAY[
            'read:posts', 'write:posts', 'update:posts', 'delete:posts', 'manage:posts',
            'read:alerts', 'write:alerts', 'update:alerts', 'delete:alerts', 'manage:alerts',
            'read:files', 'write:files', 'update:files', 'delete:files', 'manage:files',
            'read:folders', 'write:folders', 'update:folders', 'delete:folders', 'manage:folders',
            'read:rewards', 'write:rewards', 'manage:rewards',
            'read:store', 'write:store', 'manage:store',
            'read:users', 'write:users', 'update:users', 'delete:users', 'manage:users',
            'read:ai', 'manage:ai'
        ]::TEXT[];
END;
$$ LANGUAGE plpgsql;

-- Verification and summary
DO $$
DECLARE
    perm_count INTEGER;
    user_count INTEGER;
    admin_count INTEGER;
    staff_count INTEGER;
    student_count INTEGER;
    role_perm_count INTEGER;
    tables_created TEXT;
BEGIN
    -- Count permissions
    SELECT COUNT(*) INTO perm_count FROM permissions;
    SELECT COUNT(*) INTO role_perm_count FROM role_permissions;
    
    -- Count users by role
    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO admin_count FROM users WHERE role = 'admin';
    SELECT COUNT(*) INTO staff_count FROM users WHERE role = 'staff';
    SELECT COUNT(*) INTO student_count FROM users WHERE role = 'student';
    
    -- Check if tables exist
    tables_created := '';
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'permissions') THEN
        tables_created := tables_created || 'permissions ';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'role_permissions') THEN
        tables_created := tables_created || 'role_permissions ';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_custom_permissions') THEN
        tables_created := tables_created || 'user_custom_permissions';
    END IF;
    
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'RBAC Migration Completed Successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables Created/Verified: %', tables_created;
    RAISE NOTICE 'Total Permissions: %', perm_count;
    RAISE NOTICE 'Role Permission Mappings: %', role_perm_count;
    RAISE NOTICE 'Total Users: %', user_count;
    RAISE NOTICE '  - Admins: %', admin_count;
    RAISE NOTICE '  - Staff: %', staff_count;
    RAISE NOTICE '  - Students: %', student_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Available Roles: admin, staff, student';
    RAISE NOTICE 'Default Role: student';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Promote admin users: UPDATE users SET role = ''admin'' WHERE username = ''your_admin'';';
    RAISE NOTICE '  2. Restart your application to load RBAC models';
    RAISE NOTICE '  3. Test with: GET /auth/me to see your role and permissions';
    RAISE NOTICE '';
END $$;
