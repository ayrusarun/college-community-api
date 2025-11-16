-- ========================================
-- FILES TABLE CLEANUP QUERIES
-- ========================================
-- Run with: docker-compose exec -T db psql -U postgres -d college_community < cleanup_files.sql

-- ========================================
-- VIEW CURRENT STATE
-- ========================================

-- 1. Count all files
SELECT 'Total Files' as metric, COUNT(*) as count FROM files WHERE is_folder = FALSE;

-- 2. Count folders
SELECT 'Total Folders' as metric, COUNT(*) as count FROM files WHERE is_folder = TRUE;

-- 3. Storage by department
SELECT 
    department,
    COUNT(*) as file_count,
    ROUND(SUM(file_size)::numeric / 1024 / 1024, 2) as size_mb
FROM files
WHERE is_folder = FALSE
GROUP BY department
ORDER BY size_mb DESC;

-- 4. Files by type
SELECT 
    file_type,
    COUNT(*) as count,
    ROUND(SUM(file_size)::numeric / 1024 / 1024, 2) as size_mb
FROM files
WHERE is_folder = FALSE
GROUP BY file_type
ORDER BY count DESC;

-- 5. Oldest files
SELECT 
    id,
    original_filename,
    department,
    created_at,
    ROUND(file_size::numeric / 1024 / 1024, 2) as size_mb
FROM files
WHERE is_folder = FALSE
ORDER BY created_at ASC
LIMIT 10;


-- ========================================
-- CLEANUP QUERIES (USE WITH CAUTION!)
-- ========================================

-- ** OPTION 1: Delete all files (DANGEROUS - DELETES EVERYTHING) **
-- UNCOMMENT TO RUN:
-- BEGIN;
-- DELETE FROM files;
-- COMMIT;


-- ** OPTION 2: Delete all files from specific department **
-- UNCOMMENT AND MODIFY:
-- BEGIN;
-- DELETE FROM files WHERE department = 'DEPARTMENT_NAME_HERE';
-- COMMIT;


-- ** OPTION 3: Delete files older than X days **
-- Delete files older than 90 days
-- UNCOMMENT TO RUN:
-- BEGIN;
-- DELETE FROM files 
-- WHERE is_folder = FALSE 
--   AND created_at < NOW() - INTERVAL '90 days';
-- COMMIT;


-- ** OPTION 4: Delete files by type **
-- Example: Delete all test files
-- UNCOMMENT AND MODIFY:
-- BEGIN;
-- DELETE FROM files 
-- WHERE original_filename LIKE '%test%' 
--    OR original_filename LIKE '%sample%';
-- COMMIT;


-- ** OPTION 5: Delete orphaned file records (no physical file) **
-- UNCOMMENT TO RUN:
-- BEGIN;
-- DELETE FROM files 
-- WHERE is_folder = FALSE 
--   AND (file_path IS NULL OR file_path = '');
-- COMMIT;


-- ** OPTION 6: Delete duplicate files (keep newest) **
-- This keeps the most recent upload of duplicate filenames
-- UNCOMMENT TO RUN:
-- BEGIN;
-- DELETE FROM files a
-- USING files b
-- WHERE a.id < b.id
--   AND a.original_filename = b.original_filename
--   AND a.department = b.department
--   AND a.college_id = b.college_id;
-- COMMIT;


-- ** OPTION 7: Delete files from specific folder **
-- UNCOMMENT AND MODIFY:
-- BEGIN;
-- DELETE FROM files 
-- WHERE folder_path = '/path/to/folder';
-- COMMIT;


-- ** OPTION 8: Delete empty folders **
-- Folders with no files inside
-- UNCOMMENT TO RUN:
-- BEGIN;
-- DELETE FROM files f1
-- WHERE is_folder = TRUE
--   AND NOT EXISTS (
--     SELECT 1 FROM files f2 
--     WHERE f2.folder_path LIKE f1.folder_path || '%'
--       AND f2.is_folder = FALSE
--   );
-- COMMIT;


-- ** OPTION 9: Delete files by size (larger than X MB) **
-- Delete files larger than 50MB
-- UNCOMMENT TO RUN:
-- BEGIN;
-- DELETE FROM files 
-- WHERE file_size > 50 * 1024 * 1024;
-- COMMIT;


-- ** OPTION 10: Reset all files to root folder **
-- UNCOMMENT TO RUN:
-- BEGIN;
-- UPDATE files 
-- SET folder_path = '/' 
-- WHERE is_folder = FALSE;
-- COMMIT;


-- ** OPTION 11: Delete ALL folders (keeps files in root) **
-- UNCOMMENT TO RUN:
-- BEGIN;
-- UPDATE files SET folder_path = '/' WHERE is_folder = FALSE;
-- DELETE FROM files WHERE is_folder = TRUE;
-- COMMIT;


-- ** OPTION 12: Complete cleanup - Keep only recent files **
-- Keeps files from last 30 days only
-- UNCOMMENT TO RUN:
-- BEGIN;
-- DELETE FROM files 
-- WHERE created_at < NOW() - INTERVAL '30 days';
-- COMMIT;


-- ========================================
-- POST-CLEANUP VERIFICATION
-- ========================================

-- After cleanup, run these to verify:
-- SELECT COUNT(*) as remaining_files FROM files WHERE is_folder = FALSE;
-- SELECT COUNT(*) as remaining_folders FROM files WHERE is_folder = TRUE;
-- SELECT SUM(file_size) / 1024 / 1024 / 1024 as total_gb FROM files WHERE is_folder = FALSE;


-- ========================================
-- VACUUM AND OPTIMIZE
-- ========================================
-- Run after large deletions to reclaim disk space:
-- VACUUM FULL files;
-- ANALYZE files;
