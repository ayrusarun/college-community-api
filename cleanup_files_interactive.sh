#!/bin/bash

# Safe interactive file cleanup script
# This script helps you clean up the files table safely

echo "=========================================="
echo "FILES TABLE CLEANUP UTILITY"
echo "=========================================="
echo ""

# Function to run SQL and show results
run_query() {
    docker-compose exec -T db psql -U postgres -d college_community -c "$1"
}

# Show current stats
echo "📊 Current Database Statistics:"
echo "-------------------------------------------"
run_query "
SELECT 
    'Total Files' as metric, 
    COUNT(*) as count,
    ROUND(SUM(file_size)::numeric / 1024 / 1024, 2) as total_mb
FROM files WHERE is_folder = FALSE
UNION ALL
SELECT 
    'Total Folders' as metric, 
    COUNT(*) as count,
    0 as total_mb
FROM files WHERE is_folder = TRUE;
"

echo ""
echo "📁 Storage by Department:"
echo "-------------------------------------------"
run_query "
SELECT 
    department,
    COUNT(*) as files,
    ROUND(SUM(file_size)::numeric / 1024 / 1024, 2) as mb
FROM files
WHERE is_folder = FALSE
GROUP BY department
ORDER BY mb DESC;
"

echo ""
echo "=========================================="
echo "CLEANUP OPTIONS"
echo "=========================================="
echo ""
echo "Choose a cleanup option:"
echo ""
echo "  1) Delete files older than X days"
echo "  2) Delete files from specific department"
echo "  3) Delete files by folder path"
echo "  4) Delete duplicate files (keep newest)"
echo "  5) Delete empty folders"
echo "  6) Delete orphaned records (no physical file)"
echo "  7) Delete files larger than X MB"
echo "  8) DANGER: Delete ALL files"
echo "  9) View files to delete (preview only)"
echo "  0) Exit"
echo ""
read -p "Enter option (0-9): " option

case $option in
    1)
        read -p "Delete files older than how many days? " days
        echo ""
        echo "Preview: Files to be deleted"
        run_query "
        SELECT COUNT(*) as files_to_delete, 
               ROUND(SUM(file_size)::numeric / 1024 / 1024, 2) as mb_to_free
        FROM files 
        WHERE is_folder = FALSE 
          AND created_at < NOW() - INTERVAL '$days days';
        "
        echo ""
        read -p "Confirm deletion? (type 'yes' to confirm): " confirm
        if [ "$confirm" = "yes" ]; then
            run_query "
            BEGIN;
            DELETE FROM files 
            WHERE is_folder = FALSE 
              AND created_at < NOW() - INTERVAL '$days days';
            COMMIT;
            SELECT 'Deleted ' || COUNT(*) || ' files' as result FROM files WHERE FALSE;
            "
            echo "✅ Cleanup completed"
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    2)
        echo "Available departments:"
        run_query "SELECT DISTINCT department FROM files ORDER BY department;"
        echo ""
        read -p "Enter department name: " dept
        echo ""
        echo "Preview: Files to be deleted"
        run_query "
        SELECT COUNT(*) as files_to_delete,
               ROUND(SUM(file_size)::numeric / 1024 / 1024, 2) as mb_to_free
        FROM files 
        WHERE department = '$dept';
        "
        echo ""
        read -p "Confirm deletion of all files from '$dept'? (type 'yes'): " confirm
        if [ "$confirm" = "yes" ]; then
            run_query "DELETE FROM files WHERE department = '$dept';"
            echo "✅ Deleted all files from $dept"
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    3)
        read -p "Enter folder path (e.g., /Documents): " folder
        echo ""
        echo "Preview: Files to be deleted"
        run_query "
        SELECT COUNT(*) as files_to_delete
        FROM files 
        WHERE folder_path = '$folder' OR folder_path LIKE '$folder/%';
        "
        echo ""
        read -p "Confirm deletion? (type 'yes'): " confirm
        if [ "$confirm" = "yes" ]; then
            run_query "DELETE FROM files WHERE folder_path = '$folder' OR folder_path LIKE '$folder/%';"
            echo "✅ Deleted files from $folder"
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    4)
        echo "Finding duplicates..."
        run_query "
        SELECT original_filename, department, COUNT(*) as duplicates
        FROM files
        WHERE is_folder = FALSE
        GROUP BY original_filename, department
        HAVING COUNT(*) > 1
        ORDER BY duplicates DESC
        LIMIT 10;
        "
        echo ""
        read -p "Delete duplicates (keep newest)? (type 'yes'): " confirm
        if [ "$confirm" = "yes" ]; then
            run_query "
            DELETE FROM files a
            USING files b
            WHERE a.id < b.id
              AND a.original_filename = b.original_filename
              AND a.department = b.department
              AND a.college_id = b.college_id;
            "
            echo "✅ Duplicates removed"
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    5)
        echo "Finding empty folders..."
        run_query "
        SELECT COUNT(*) as empty_folders
        FROM files f1
        WHERE is_folder = TRUE
          AND NOT EXISTS (
            SELECT 1 FROM files f2 
            WHERE f2.folder_path LIKE f1.folder_path || '%'
              AND f2.is_folder = FALSE
          );
        "
        echo ""
        read -p "Delete empty folders? (type 'yes'): " confirm
        if [ "$confirm" = "yes" ]; then
            run_query "
            DELETE FROM files f1
            WHERE is_folder = TRUE
              AND NOT EXISTS (
                SELECT 1 FROM files f2 
                WHERE f2.folder_path LIKE f1.folder_path || '%'
                  AND f2.is_folder = FALSE
              );
            "
            echo "✅ Empty folders deleted"
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    6)
        echo "Finding orphaned records..."
        run_query "
        SELECT COUNT(*) as orphaned_records
        FROM files 
        WHERE is_folder = FALSE 
          AND (file_path IS NULL OR file_path = '');
        "
        echo ""
        read -p "Delete orphaned records? (type 'yes'): " confirm
        if [ "$confirm" = "yes" ]; then
            run_query "DELETE FROM files WHERE is_folder = FALSE AND (file_path IS NULL OR file_path = '');"
            echo "✅ Orphaned records deleted"
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    7)
        read -p "Delete files larger than how many MB? " size_mb
        echo ""
        echo "Preview: Files to be deleted"
        run_query "
        SELECT COUNT(*) as files_to_delete,
               ROUND(SUM(file_size)::numeric / 1024 / 1024, 2) as mb_to_free
        FROM files 
        WHERE file_size > $size_mb * 1024 * 1024;
        "
        echo ""
        read -p "Confirm deletion? (type 'yes'): " confirm
        if [ "$confirm" = "yes" ]; then
            run_query "DELETE FROM files WHERE file_size > $size_mb * 1024 * 1024;"
            echo "✅ Large files deleted"
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    8)
        echo "⚠️  WARNING: This will delete ALL files!"
        echo ""
        read -p "Type 'DELETE ALL FILES' to confirm: " confirm
        if [ "$confirm" = "DELETE ALL FILES" ]; then
            run_query "DELETE FROM files;"
            echo "✅ All files deleted"
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    9)
        echo "Recent files:"
        run_query "
        SELECT 
            id,
            original_filename,
            department,
            folder_path,
            ROUND(file_size::numeric / 1024 / 1024, 2) as mb,
            created_at
        FROM files
        WHERE is_folder = FALSE
        ORDER BY created_at DESC
        LIMIT 20;
        "
        ;;
    
    0)
        echo "Exiting..."
        exit 0
        ;;
    
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Final Statistics:"
echo "=========================================="
run_query "
SELECT 
    'Remaining Files' as metric, 
    COUNT(*) as count,
    ROUND(SUM(file_size)::numeric / 1024 / 1024, 2) as total_mb
FROM files WHERE is_folder = FALSE;
"

echo ""
echo "💡 Tip: Run 'VACUUM FULL files; ANALYZE files;' to reclaim disk space"
