-- Name: Add Folder Support to Files
-- Description: Adds folder structure capabilities to the file management system
-- Version: 20241116_add_folder_support
-- Created: 2024-11-16

-- Add folder_path column to store the virtual folder path
ALTER TABLE files ADD COLUMN IF NOT EXISTS folder_path VARCHAR(1000) DEFAULT '/' NOT NULL;

-- Add is_folder column to distinguish folders from files
ALTER TABLE files ADD COLUMN IF NOT EXISTS is_folder BOOLEAN DEFAULT FALSE NOT NULL;

-- Add parent_folder_id for hierarchical structure (optional, for future use)
ALTER TABLE files ADD COLUMN IF NOT EXISTS parent_folder_id INTEGER NULL;

-- Create index on folder_path for faster folder queries
CREATE INDEX IF NOT EXISTS idx_files_folder_path ON files(folder_path, college_id);

-- Create index on parent_folder_id for hierarchical queries
CREATE INDEX IF NOT EXISTS idx_files_parent_folder ON files(parent_folder_id);

-- Update existing files to be in root folder
UPDATE files SET folder_path = '/' WHERE folder_path IS NULL OR folder_path = '';

-- Verify the changes
DO $$
DECLARE
    file_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO file_count FROM files WHERE folder_path = '/';
    RAISE NOTICE 'Migration completed: % files set to root folder', file_count;
    RAISE NOTICE 'Folder support columns added successfully';
END $$;
