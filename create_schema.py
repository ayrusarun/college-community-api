#!/usr/bin/env python3
"""
Database Schema Creation Script for Production Deployment

This script creates all database tables and schema without populating data.
Perfect for production environments where you want to start with a clean database.

Usage:
    python create_schema.py              # Create all tables
    python create_schema.py --drop       # Drop and recreate all tables
    python create_schema.py --check      # Check existing tables
"""

import argparse
import sys
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import SessionLocal, engine
from app.models.models import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database connection successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def get_existing_tables():
    """Get list of existing tables in the database"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return tables
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to get table list: {e}")
        return []

def drop_all_tables():
    """Drop all existing tables (DANGEROUS!)"""
    try:
        logger.warning("🚨 DROPPING ALL TABLES - This will delete all data!")
        
        # Get confirmation
        confirmation = input("Are you sure you want to drop all tables? Type 'YES' to confirm: ")
        if confirmation != 'YES':
            logger.info("Operation cancelled.")
            return False
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ All tables dropped successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        return False

def create_all_tables():
    """Create all database tables from models"""
    try:
        logger.info("🔨 Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info("✅ Database schema created successfully!")
        logger.info(f"📊 Tables created: {len(tables)}")
        
        for table in sorted(tables):
            logger.info(f"   • {table}")
        
        return True
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False

def check_tables():
    """Check existing database tables and their structure"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if not tables:
            logger.info("📋 No tables found in database")
            return
        
        logger.info(f"📊 Found {len(tables)} tables:")
        
        for table_name in sorted(tables):
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            
            logger.info(f"\n🔹 Table: {table_name}")
            logger.info(f"   Columns: {len(columns)}")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] else ""
                logger.info(f"     • {col['name']}: {col['type']} {nullable}{default}")
            
            if indexes:
                logger.info(f"   Indexes: {len(indexes)}")
                for idx in indexes:
                    logger.info(f"     • {idx['name']}: {idx['column_names']}")
            
            if foreign_keys:
                logger.info(f"   Foreign Keys: {len(foreign_keys)}")
                for fk in foreign_keys:
                    logger.info(f"     • {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to check tables: {e}")

def main():
    parser = argparse.ArgumentParser(description='Database Schema Management')
    parser.add_argument('--drop', action='store_true', help='Drop all tables before creating')
    parser.add_argument('--check', action='store_true', help='Check existing tables')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    logger.info("🚀 College Community API - Database Schema Manager")
    logger.info("=" * 60)
    
    # Check database connection first
    if not check_database_connection():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Handle different operations
    if args.check:
        logger.info("🔍 Checking existing database schema...")
        check_tables()
        return
    
    # Check if tables already exist
    existing_tables = get_existing_tables()
    if existing_tables and not args.drop:
        logger.warning(f"⚠️  Database already has {len(existing_tables)} tables:")
        for table in sorted(existing_tables):
            logger.warning(f"   • {table}")
        
        if not args.force:
            response = input("\nDo you want to continue anyway? This might cause conflicts (y/N): ")
            if response.lower() != 'y':
                logger.info("Operation cancelled.")
                sys.exit(0)
    
    # Drop tables if requested
    if args.drop:
        if not drop_all_tables():
            sys.exit(1)
    
    # Create all tables
    if create_all_tables():
        logger.info("\n🎉 Database schema setup completed successfully!")
        logger.info("\n📋 Next Steps:")
        logger.info("   1. Run init_db.py to populate with sample data (development)")
        logger.info("   2. Or manually create your first college and users (production)")
        logger.info("   3. Start the FastAPI application")
    else:
        logger.error("❌ Schema creation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()