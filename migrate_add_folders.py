#!/usr/bin/env python3
"""
Migration script to add folder support to the files table
Run this script to add folder_path, is_folder, and parent_folder_id columns
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "college_community")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def run_migration():
    """Run the folder support migration"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected to database successfully!")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'files' AND column_name IN ('folder_path', 'is_folder', 'parent_folder_id')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        if 'folder_path' in existing_columns:
            print("⚠️  Migration already applied (folder_path column exists)")
            response = input("Do you want to continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Migration cancelled")
                return
        
        print("\n📦 Starting migration to add folder support...")
        
        # Add folder_path column
        if 'folder_path' not in existing_columns:
            print("  ➜ Adding folder_path column...")
            cursor.execute("""
                ALTER TABLE files 
                ADD COLUMN folder_path VARCHAR(1000) DEFAULT '/' NOT NULL
            """)
            print("  ✓ folder_path column added")
        else:
            print("  ⊙ folder_path column already exists")
        
        # Add is_folder column
        if 'is_folder' not in existing_columns:
            print("  ➜ Adding is_folder column...")
            cursor.execute("""
                ALTER TABLE files 
                ADD COLUMN is_folder BOOLEAN DEFAULT FALSE NOT NULL
            """)
            print("  ✓ is_folder column added")
        else:
            print("  ⊙ is_folder column already exists")
        
        # Add parent_folder_id column
        if 'parent_folder_id' not in existing_columns:
            print("  ➜ Adding parent_folder_id column...")
            cursor.execute("""
                ALTER TABLE files 
                ADD COLUMN parent_folder_id INTEGER NULL
            """)
            print("  ✓ parent_folder_id column added")
        else:
            print("  ⊙ parent_folder_id column already exists")
        
        # Create indexes
        print("  ➜ Creating indexes...")
        
        # Check if indexes exist
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'files' AND indexname = 'idx_files_folder_path'
        """)
        if not cursor.fetchone():
            cursor.execute("""
                CREATE INDEX idx_files_folder_path ON files(folder_path, college_id)
            """)
            print("  ✓ Index idx_files_folder_path created")
        else:
            print("  ⊙ Index idx_files_folder_path already exists")
        
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'files' AND indexname = 'idx_files_parent_folder'
        """)
        if not cursor.fetchone():
            cursor.execute("""
                CREATE INDEX idx_files_parent_folder ON files(parent_folder_id)
            """)
            print("  ✓ Index idx_files_parent_folder created")
        else:
            print("  ⊙ Index idx_files_parent_folder already exists")
        
        # Update existing files to set folder_path to root if NULL
        print("  ➜ Updating existing files...")
        cursor.execute("""
            UPDATE files 
            SET folder_path = '/' 
            WHERE folder_path IS NULL OR folder_path = ''
        """)
        updated_count = cursor.rowcount
        print(f"  ✓ Updated {updated_count} existing file(s) to root folder")
        
        # Create default folders for common categories
        print("\n📁 Creating default folders...")
        
        # Get all colleges
        cursor.execute("SELECT id, name FROM colleges")
        colleges = cursor.fetchall()
        
        default_folders = [
            ('/Documents', 'Document files'),
            ('/Images', 'Image files'),
            ('/Videos', 'Video files'),
            ('/Archives', 'Archived files'),
        ]
        
        for college_id, college_name in colleges:
            print(f"\n  Creating folders for college: {college_name} (ID: {college_id})")
            
            # Get a user from this college to be the creator
            cursor.execute("SELECT id FROM users WHERE college_id = %s LIMIT 1", (college_id,))
            user_result = cursor.fetchone()
            
            if not user_result:
                print(f"  ⚠️  No users found for college {college_id}, skipping folder creation")
                continue
            
            user_id = user_result[0]
            
            for folder_path, description in default_folders:
                # Check if folder already exists
                cursor.execute("""
                    SELECT id FROM files 
                    WHERE folder_path = %s AND is_folder = TRUE AND college_id = %s
                """, (folder_path, college_id))
                
                if not cursor.fetchone():
                    folder_name = folder_path.split('/')[-1]
                    cursor.execute("""
                        INSERT INTO files (
                            filename, original_filename, file_path, file_size,
                            file_type, mime_type, description, folder_path,
                            is_folder, department, college_id, uploaded_by,
                            upload_metadata, is_indexed
                        ) VALUES (
                            %s, %s, '', 0, 'OTHER', 'application/x-directory',
                            %s, %s, TRUE, 'System', %s, %s,
                            '{"file_count": 0}', 'indexed'
                        )
                    """, (folder_name, folder_name, description, folder_path, 
                          college_id, user_id))
                    print(f"    ✓ Created folder: {folder_path}")
                else:
                    print(f"    ⊙ Folder already exists: {folder_path}")
        
        print("\n✅ Migration completed successfully!")
        print("\n📋 Summary:")
        print("  • Added folder_path, is_folder, and parent_folder_id columns")
        print("  • Created indexes for faster folder queries")
        print(f"  • Updated {updated_count} existing files")
        print(f"  • Created default folders for {len(colleges)} college(s)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("FOLDER SUPPORT MIGRATION")
    print("=" * 60)
    print("\nThis will add folder support to the files table.")
    print("\nChanges to be made:")
    print("  1. Add folder_path column (VARCHAR 1000)")
    print("  2. Add is_folder column (BOOLEAN)")
    print("  3. Add parent_folder_id column (INTEGER)")
    print("  4. Create indexes for better performance")
    print("  5. Update existing files to root folder")
    print("  6. Create default folders")
    print("\n" + "=" * 60)
    
    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        run_migration()
    else:
        print("Migration cancelled")
