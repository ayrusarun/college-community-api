-- Migration: Populate role_permissions table with default permissions
-- This populates role_permissions for all existing colleges

DO $$
DECLARE
    college_record RECORD;
    perm_id INT;
BEGIN
    -- For each college, insert role-permission mappings
    FOR college_record IN SELECT id FROM colleges LOOP
        
        -- STUDENT PERMISSIONS (19 permissions)
        INSERT INTO role_permissions (role, permission_id, college_id)
        SELECT 'student', p.id, college_record.id
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
        SELECT 'staff', p.id, college_record.id
        FROM permissions p
        WHERE p.name IN (
            'read:posts', 'write:posts', 'update:posts', 'delete:posts', 'manage:posts',
            'read:alerts', 'write:alerts', 'update:alerts', 'delete:alerts', 'manage:alerts',
            'read:files', 'write:files', 'update:files', 'delete:files',
            'read:folders', 'write:folders', 'update:folders', 'delete:folders',
            'read:rewards', 'write:rewards',
            'read:store', 'write:store', 'manage:store',
            'read:users',
            'read:ai'
        )
        ON CONFLICT (role, permission_id, college_id) DO NOTHING;

        -- ADMIN PERMISSIONS (all 34 permissions)
        INSERT INTO role_permissions (role, permission_id, college_id)
        SELECT 'admin', p.id, college_record.id
        FROM permissions p
        ON CONFLICT (role, permission_id, college_id) DO NOTHING;

    END LOOP;
    
    RAISE NOTICE 'Role permissions populated for all colleges';
END $$;
