#!/usr/bin/env python3
"""
Migration script to add AI-related tables and columns to the database.
Run this after updating the models.py file with AI features.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.database import get_database_url
from app.models.models import Base

def migrate_ai_features():
    """Add AI-related tables and columns to the existing database"""
    
    # Get database URL
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print("Starting AI features migration...")
    
    try:
        with engine.connect() as conn:
            # Add is_indexed column to files table if it doesn't exist
            try:
                conn.execute(text("""
                    ALTER TABLE files 
                    ADD COLUMN is_indexed VARCHAR(20) DEFAULT 'pending' NOT NULL;
                """))
                print("✓ Added is_indexed column to files table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✓ is_indexed column already exists in files table")
                else:
                    print(f"✗ Error adding is_indexed column: {e}")
            
            # Create ai_conversations table
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ai_conversations (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        college_id INTEGER NOT NULL REFERENCES colleges(id),
                        query TEXT NOT NULL,
                        response TEXT NOT NULL,
                        context_docs JSON,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_conversations_user_id ON ai_conversations(user_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_conversations_created_at ON ai_conversations(created_at);"))
                print("✓ Created ai_conversations table")
            except Exception as e:
                print(f"✗ Error creating ai_conversations table: {e}")
            
            # Create indexing_tasks table
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS indexing_tasks (
                        id SERIAL PRIMARY KEY,
                        content_type VARCHAR(50) NOT NULL,
                        content_id INTEGER NOT NULL,
                        college_id INTEGER NOT NULL REFERENCES colleges(id),
                        status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        processed_at TIMESTAMP
                    );
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_indexing_tasks_status ON indexing_tasks(status);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_indexing_tasks_college_id ON indexing_tasks(college_id);"))
                print("✓ Created indexing_tasks table")
            except Exception as e:
                print(f"✗ Error creating indexing_tasks table: {e}")
            
            # Commit all changes
            conn.commit()
            
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_ai_features()
    sys.exit(0 if success else 1)