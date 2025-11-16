#!/bin/bash
# File cleanup queries for the files table
# Run with: docker-compose exec -T db psql -U postgres -d college_community < cleanup_files.sql

echo "=========================================="
echo "FILES TABLE CLEANUP QUERIES"
echo "=========================================="
echo ""

# Choose which cleanup operation you want to run:

# 1. VIEW ALL FILES WITH DETAILS
echo "1. View all files with details:"
echo "-------------------------------------------"
docker-compose exec -T db psql -U postgres -d college_community << 'EOF'
SELECT 
    id,
    original_filename,
    file_size,
    file_type,
    department,
    folder_path,
    is_folder,
    created_at
FROM files
ORDER BY created_at DESC
LIMIT 20;
EOF

echo ""
echo "2. View storage usage by department:"
echo "-------------------------------------------"
docker-compose exec -T db psql -U postgres -d college_community << 'EOF'
SELECT 
    department,
    COUNT(*) as file_count,
    SUM(file_size) as total_bytes,
    ROUND(SUM(file_size)::numeric / 1024 / 1024, 2) as total_mb,
    ROUND(SUM(file_size)::numeric / 1024 / 1024 / 1024, 2) as total_gb
FROM files
WHERE is_folder = FALSE
GROUP BY department
ORDER BY total_bytes DESC;
EOF

echo ""
echo "3. View files without physical files (orphaned records):"
echo "-------------------------------------------"
docker-compose exec -T db psql -U postgres -d college_community << 'EOF'
SELECT COUNT(*) as orphaned_count
FROM files 
WHERE is_folder = FALSE 
  AND (file_path IS NULL OR file_path = '');
EOF

echo ""
echo "=========================================="
echo "CLEANUP OPTIONS"
echo "=========================================="
echo ""
echo "Run these commands carefully in production!"
echo ""
