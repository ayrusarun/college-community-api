#!/usr/bin/env python3
"""
Simple migration script for adding folder support to files table
This script directly modifies the database without SQLAlchemy dependencies
"""

import os
import psycopg2
from psycopg2 import sql

# Database configuration from environment or defaults
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "college_community_db")
DB_USER = os.getenv("DB_USER", "college_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "college_pass")

def get_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        )
    """, (table_name, column_name))
    return cursor.fetchone()[0]

def run_migration():
    """Run the folder support migration"""
    print("=" * 60)
    print("FOLDER SUPPORT MIGRATION")
    print("=" * 60)
    print()
    
    try:
        # Connect to database
        conn = get_connection()
        conn.autocommit = False  # Use transaction
        cursor = conn.cursor()
        
        print("✅ Connected to database successfully!")
        print()
        
        # Check if migration is needed
        folder_path_exists = check_column_exists(cursor, 'files', 'folder_path')
        is_folder_exists = check_column_exists(cursor, 'files', 'is_folder')
        parent_folder_id_exists = check_column_exists(cursor, 'files', 'parent_folder_id')
        
        if folder_path_exists and is_folder_exists and parent_folder_id_exists:
            print("⚠️  Migration already applied!")
            print("    All folder columns already exist in the files table.")
            cursor.close()
            conn.close()
            return
        
        print("📦 Starting migration to add folder support...")
        print()
        
        # Add folder_path column
        if not folder_path_exists:
            print("  ➜ Adding folder_path column...")
            cursor.execute("""
                ALTER TABLE files 
                ADD COLUMN folder_path VARCHAR(1000) DEFAULT '/' NOT NULL
            """)
            print("  ✓ folder_path column added")
        else:
            print("  ⊙ folder_path column already exists")
        
        # Add is_folder column
        if not is_folder_exists:
            print("  ➜ Adding is_folder column...")
            cursor.execute("""
                ALTER TABLE files 
                ADD COLUMN is_folder BOOLEAN DEFAULT FALSE NOT NULL
            """)
            print("  ✓ is_folder column added")
        else:
            print("  ⊙ is_folder column already exists")
        
        # Add parent_folder_id column
        if not parent_folder_id_exists:
            print("  ➜ Adding parent_folder_id column...")
            cursor.execute("""
                ALTER TABLE files 
                ADD COLUMN parent_folder_id INTEGER NULL
            """)
            print("  ✓ parent_folder_id column added")
        else:
            print("  ⊙ parent_folder_id column already exists")
        
        print()
        print("  ➜ Creating indexes...")
        
        # Create indexes (will skip if they exist)
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_folder_path 
                ON files(folder_path, college_id)
            """)
            print("  ✓ Index idx_files_folder_path created")
        except Exception as e:
            print(f"  ⚠️  Index creation note: {e}")
        
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_parent_folder 
                ON files(parent_folder_id)
            """)
            print("  ✓ Index idx_files_parent_folder created")
        except Exception as e:
            print(f"  ⚠️  Index creation note: {e}")
        
        print()
        print("  ➜ Updating existing files...")
        cursor.execute("""
            UPDATE files 
            SET folder_path = '/' 
            WHERE folder_path IS NULL OR folder_path = ''
        """)
        updated_count = cursor.rowcount
        print(f"  ✓ Updated {updated_count} existing file(s) to root folder")
        
        # Commit the transaction
        conn.commit()
        
        print()
        print("✅ Migration completed successfully!")
        print()
        print("📋 Summary:")
        print("  • Added folder_path, is_folder, and parent_folder_id columns")
        print("  • Created indexes for faster folder queries")
        print(f"  • Updated {updated_count} existing files")
        print()
        print("Next steps:")
        print("  1. Restart your application")
        print("  2. Test folder endpoints with: ./test_folders.sh")
        print("  3. Read documentation: FOLDER_FEATURE_DOCUMENTATION.md")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print()
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print()
        print(f"❌ Error during migration: {e}")
        if conn:
            conn.rollback()
        raise

if __name__ == "__main__":
    import sys
    
    print()
    print("This migration will add folder support to the files table.")
    print()
    print("Changes to be made:")
    print("  1. Add folder_path column (VARCHAR 1000)")
    print("  2. Add is_folder column (BOOLEAN)")
    print("  3. Add parent_folder_id column (INTEGER)")
    print("  4. Create indexes for better performance")
    print("  5. Update existing files to root folder")
    print()
    print("-" * 60)
    
    # Check if --yes flag is provided
    if "--yes" in sys.argv or "-y" in sys.argv:
        run_migration()
    else:
        response = input("\nProceed with migration? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            run_migration()
        else:
            print("Migration cancelled")
            sys.exit(0)
