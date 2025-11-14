#!/usr/bin/env python3

"""
Single Schema File Approach - Simple Database Setup
Always applies COMPLETE schema from one master file.

Usage:
    python setup_db.py                # Setup/Update database
    python setup_db.py --reset        # Reset and recreate
    python setup_db.py --status       # Show current state

Philosophy:
- ONE master schema file contains EVERYTHING
- Always safe to run (uses IF NOT EXISTS)
- No version tracking needed
- Add new tables/changes to same file
- Perfect for single developer or small teams
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://college_user:college_pass@localhost:5432/college_community_db'
)

def read_master_schema():
    """Read the master schema file"""
    schema_file = os.path.join(os.path.dirname(__file__), "master_schema.sql")
    
    if not os.path.exists(schema_file):
        print(f"❌ Master schema file not found: {schema_file}")
        print("💡 Create master_schema.sql with your complete database schema")
        sys.exit(1)
    
    with open(schema_file, 'r') as f:
        return f.read()

def apply_master_schema():
    """Apply the complete schema from master file"""
    print("🗄️ Single Schema Database Setup")
    print("=" * 40)
    
    try:
        # Connect to database
        engine = create_engine(DATABASE_URL)
        
        print(f"📡 Connecting to database...")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Read and apply schema
        print("📖 Reading master schema...")
        schema_sql = read_master_schema()
        
        print("🔨 Applying complete schema...")
        
        with engine.connect() as conn:
            # Execute the entire schema
            conn.execute(text(schema_sql))
            conn.commit()
        
        print("✅ Schema applied successfully!")
        
        # Show summary
        with engine.connect() as conn:
            # Count tables
            tables_result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = tables_result.scalar()
            
            # Count sample data
            try:
                users_result = conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = users_result.scalar()
                
                colleges_result = conn.execute(text("SELECT COUNT(*) FROM colleges"))  
                college_count = colleges_result.scalar()
                
                print(f"\n📊 Database Summary:")
                print(f"   • Tables: {table_count}")
                print(f"   • Colleges: {college_count}")
                print(f"   • Users: {user_count}")
                
            except:
                print(f"\n📊 Database Summary:")
                print(f"   • Tables created: {table_count}")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def show_status():
    """Show current database status"""
    print("📊 Database Status")
    print("=" * 30)
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Get all tables
            tables_result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' ORDER BY table_name
            """))
            tables = [row[0] for row in tables_result]
            
            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    try:
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.scalar()
                        print(f"   • {table}: {count} records")
                    except:
                        print(f"   • {table}: (unable to count)")
            else:
                print("⚠️ No tables found - database might be empty")
                
    except Exception as e:
        print(f"❌ Cannot connect to database: {e}")

def reset_database():
    """Reset database by dropping all tables"""
    confirm = input("⚠️ This will DELETE ALL DATA. Type 'DELETE' to confirm: ")
    if confirm != 'DELETE':
        print("❌ Reset cancelled")
        return
    
    print("🗑️ Resetting database...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Get all tables
            tables_result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in tables_result]
            
            if tables:
                # Drop all tables (cascade to handle foreign keys)
                for table in tables:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                
                conn.commit()
                print(f"🗑️ Dropped {len(tables)} tables")
            else:
                print("ℹ️ No tables to drop")
        
        # Apply fresh schema
        apply_master_schema()
        
    except Exception as e:
        print(f"❌ Reset failed: {e}")

def main():
    """Main CLI interface"""
    args = sys.argv[1:]
    
    if not args:
        # Default: apply schema
        apply_master_schema()
    
    elif args[0] == "--status":
        show_status()
    
    elif args[0] == "--reset":
        reset_database()
    
    else:
        print("Single Schema Database Setup")
        print("=" * 30)
        print("Usage:")
        print("  python setup_db.py          # Apply master schema")
        print("  python setup_db.py --status # Show database status") 
        print("  python setup_db.py --reset  # Reset database")
        print("")
        print("Master schema file: master_schema.sql")
        print("Add all your tables and changes to that ONE file!")

if __name__ == "__main__":
    main()