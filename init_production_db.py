#!/usr/bin/env python3
"""
Production Database Initialization Script

This script sets up the database for production use with minimal essential data.
It creates the basic schema and essential records without test/demo data.

Usage:
    python init_production_db.py                    # Initialize production database
    python init_production_db.py --admin-user      # Also create admin user
    python init_production_db.py --sample-college  # Add one sample college
"""

import argparse
import sys
import getpass
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.models import Base, College, User
from app.core.security import get_password_hash
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

def create_schema():
    """Create database schema"""
    try:
        logger.info("🔨 Creating database schema...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database schema created successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to create schema: {e}")
        return False

def create_sample_college():
    """Create a sample college for testing"""
    try:
        db = SessionLocal()
        
        # Check if college already exists
        existing_college = db.query(College).first()
        if existing_college:
            logger.info(f"📚 College already exists: {existing_college.name}")
            db.close()
            return existing_college
        
        # Get college details
        logger.info("📚 Creating sample college...")
        college_name = input("Enter college name (or press Enter for 'Sample College'): ").strip()
        if not college_name:
            college_name = "Sample College"
        
        # Generate slug from name
        college_slug = college_name.lower().replace(" ", "-").replace("&", "and")
        college_slug = ''.join(c for c in college_slug if c.isalnum() or c == '-')
        
        college = College(
            name=college_name,
            slug=college_slug
        )
        
        db.add(college)
        db.commit()
        db.refresh(college)
        
        logger.info(f"✅ Created college: {college.name} (ID: {college.id})")
        db.close()
        return college
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to create college: {e}")
        db.rollback()
        db.close()
        return None

def create_admin_user(college_id=None):
    """Create an admin user for the system"""
    try:
        db = SessionLocal()
        
        # If no college_id provided, get the first available college
        if college_id is None:
            college = db.query(College).first()
            if not college:
                logger.error("❌ No college found. Create a college first.")
                db.close()
                return None
            college_id = college.id
            college_name = college.name
        else:
            college = db.query(College).filter(College.id == college_id).first()
            college_name = college.name if college else "Unknown"
        
        logger.info("👤 Creating admin user...")
        
        # Get admin user details
        full_name = input("Enter admin full name: ").strip()
        if not full_name:
            logger.error("❌ Full name is required")
            db.close()
            return None
        
        email = input("Enter admin email: ").strip()
        if not email or "@" not in email:
            logger.error("❌ Valid email is required")
            db.close()
            return None
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            logger.error(f"❌ User with email {email} already exists")
            db.close()
            return None
        
        # Get password securely
        password = getpass.getpass("Enter admin password: ")
        if len(password) < 6:
            logger.error("❌ Password must be at least 6 characters")
            db.close()
            return None
        
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            logger.error("❌ Passwords don't match")
            db.close()
            return None
        
        # Generate username from email
        username = email.split('@')[0].lower()
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            department="Administration",
            class_name="Staff",
            academic_year="2024-25",
            college_id=college_id
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"✅ Created admin user: {admin_user.full_name} ({admin_user.email})")
        logger.info(f"   College: {college_name}")
        logger.info(f"   Username: {admin_user.username}")
        
        db.close()
        return admin_user
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to create admin user: {e}")
        db.rollback()
        db.close()
        return None

def check_existing_data():
    """Check if database already has data"""
    try:
        db = SessionLocal()
        
        college_count = db.query(College).count()
        user_count = db.query(User).count()
        
        logger.info(f"📊 Current database state:")
        logger.info(f"   Colleges: {college_count}")
        logger.info(f"   Users: {user_count}")
        
        db.close()
        
        return college_count > 0 or user_count > 0
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to check existing data: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Production Database Initialization')
    parser.add_argument('--admin-user', action='store_true', help='Create an admin user')
    parser.add_argument('--sample-college', action='store_true', help='Create a sample college')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    logger.info("🚀 College Community API - Production Database Setup")
    logger.info("=" * 60)
    
    # Check database connection
    if not check_database_connection():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Check existing data
    has_data = check_existing_data()
    if has_data and not args.force:
        logger.warning("⚠️  Database already contains data!")
        response = input("Do you want to continue? (y/N): ")
        if response.lower() != 'y':
            logger.info("Operation cancelled.")
            sys.exit(0)
    
    # Create schema
    if not create_schema():
        logger.error("❌ Failed to create schema")
        sys.exit(1)
    
    college = None
    
    # Create sample college if requested
    if args.sample_college or args.admin_user:
        college = create_sample_college()
        if not college:
            logger.error("❌ Failed to create college")
            sys.exit(1)
    
    # Create admin user if requested
    if args.admin_user:
        college_id = college.id if college else None
        admin_user = create_admin_user(college_id)
        if not admin_user:
            logger.error("❌ Failed to create admin user")
            sys.exit(1)
    
    logger.info("\n🎉 Production database initialization completed!")
    logger.info("\n📋 Next Steps for Production:")
    logger.info("   1. Set up proper environment variables (.env file)")
    logger.info("   2. Configure production database URL")
    logger.info("   3. Set a secure SECRET_KEY")
    logger.info("   4. Update OpenAI API key if using AI features")
    logger.info("   5. Set up SSL certificates for HTTPS")
    logger.info("   6. Configure proper CORS settings")
    logger.info("   7. Set up monitoring and logging")
    
    if not args.admin_user and not args.sample_college:
        logger.info("\n💡 Tip: Run with --admin-user to create an admin user")
        logger.info("   or --sample-college to create a sample college")

if __name__ == "__main__":
    main()