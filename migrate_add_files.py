"""
Migration script to add file upload functionality to existing database
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.models import Base


def add_file_tables():
    """Add file tables to the existing database"""
    db = SessionLocal()
    
    try:
        print("🔄 Adding file tables...")
        
        # Create the files table
        create_files_table_sql = """
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER NOT NULL,
            file_type VARCHAR(20) NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            description TEXT,
            department VARCHAR(100) NOT NULL,
            college_id INTEGER NOT NULL,
            uploaded_by INTEGER NOT NULL,
            upload_metadata JSON DEFAULT '{"downloads": 0, "views": 0}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (college_id) REFERENCES colleges(id),
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
        """
        
        db.execute(text(create_files_table_sql))
        
        # Create indexes for better performance
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_files_department ON files(department)",
            "CREATE INDEX IF NOT EXISTS idx_files_college_id ON files(college_id)",
            "CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_files_file_type ON files(file_type)"
        ]
        
        for index_sql in indexes_sql:
            db.execute(text(index_sql))
        
        # Add updated_at trigger function if it doesn't exist
        trigger_function_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
        """
        
        db.execute(text(trigger_function_sql))
        
        # Create trigger for files table
        trigger_sql = """
        DROP TRIGGER IF EXISTS update_files_updated_at ON files;
        CREATE TRIGGER update_files_updated_at 
            BEFORE UPDATE ON files 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column()
        """
        
        db.execute(text(trigger_sql))
        
        db.commit()
        print("✅ File tables added successfully!")
        
        # Verify table creation
        result = db.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'files'"))
        if result.scalar() > 0:
            print("✅ Files table verified in database")
        else:
            print("❌ Files table creation failed")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding file tables: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_file_tables()