-- Migration: Populate role_permissions table with default permissions
-- This populates role_permissions for all existing colleges

DO $$
DECLARE
    college_record RECORD;
    role_type_name TEXT;
BEGIN
    -- Detect which enum type name is being used (user_role or userrole)
    SELECT typname INTO role_type_name
    FROM pg_type 
    WHERE typname IN ('user_role', 'userrole')
    ORDER BY CASE WHEN typname = 'user_role' THEN 1 ELSE 2 END
    LIMIT 1;
    
    -- For each college, insert role-permission mappings
    FOR college_record IN SELECT id FROM colleges LOOP
        
        -- STUDENT PERMISSIONS (19 permissions)
        EXECUTE format('INSERT INTO role_permissions (role, permission_id, college_id)
        SELECT $1::%I, p.id, $2
        FROM permissions p
        WHERE p.name = ANY($3)
        ON CONFLICT (role, permission_id, college_id) DO NOTHING', role_type_name)
        USING 'student', college_record.id, ARRAY[
            'read:posts', 'write:posts', 'update:posts', 'delete:posts',
            'read:alerts', 
            'read:files', 'write:files', 'update:files', 'delete:files',
            'read:folders', 'write:folders', 'update:folders', 'delete:folders',
            'read:rewards', 'write:rewards',
            'read:store', 'write:store',
            'read:users',
            'read:ai'
        ];

        -- STAFF PERMISSIONS (24 permissions)
        EXECUTE format('INSERT INTO role_permissions (role, permission_id, college_id)
        SELECT $1::%I, p.id, $2
        FROM permissions p
        WHERE p.name = ANY($3)
        ON CONFLICT (role, permission_id, college_id) DO NOTHING', role_type_name)
        USING 'staff', college_record.id, ARRAY[
            'read:posts', 'write:posts', 'update:posts', 'delete:posts', 'manage:posts',
            'read:alerts', 'write:alerts', 'update:alerts', 'delete:alerts', 'manage:alerts',
            'read:files', 'write:files', 'update:files', 'delete:files',
            'read:folders', 'write:folders', 'update:folders', 'delete:folders',
            'read:rewards', 'write:rewards',
            'read:store', 'write:store', 'manage:store',
            'read:users', 'update:users',
            'read:ai'
        ];

        -- ADMIN PERMISSIONS (all 34 permissions)
        EXECUTE format('INSERT INTO role_permissions (role, permission_id, college_id)
        SELECT $1::%I, p.id, $2
        FROM permissions p
        ON CONFLICT (role, permission_id, college_id) DO NOTHING', role_type_name)
        USING 'admin', college_record.id;

    END LOOP;
    
    RAISE NOTICE 'Role permissions populated for all colleges using enum type: %', role_type_name;
END $$;
