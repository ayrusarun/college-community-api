#!/usr/bin/env python3
"""
Database Migration and Backup Tool

This script handles database migrations, backups, and data export/import
for both development and production environments.

Usage:
    python db_manager.py backup              # Create database backup
    python db_manager.py restore backup.sql # Restore from backup
    python db_manager.py migrate            # Run pending migrations
    python db_manager.py export-data        # Export data as JSON
    python db_manager.py import-data data.json  # Import data from JSON
"""

import argparse
import sys
import json
import os
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import SessionLocal, engine
from app.models.models import College, User, Post, Alert, RewardPoint, Reward
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_backup_command():
    """Generate appropriate backup command based on database URL"""
    db_url = settings.database_url
    
    if db_url.startswith("postgresql://"):
        # Parse PostgreSQL URL
        # Format: postgresql://user:password@host:port/database
        db_url = db_url.replace("postgresql://", "")
        if "@" in db_url:
            auth, host_db = db_url.split("@", 1)
            if ":" in auth:
                user, password = auth.split(":", 1)
            else:
                user, password = auth, ""
            
            if "/" in host_db:
                host_port, database = host_db.split("/", 1)
            else:
                host_port, database = host_db, ""
            
            if ":" in host_port:
                host, port = host_port.split(":", 1)
            else:
                host, port = host_port, "5432"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{database}_{timestamp}.sql"
        
        # Set PGPASSWORD environment variable for non-interactive backup
        env_vars = f"PGPASSWORD={password}" if password else ""
        
        backup_cmd = f'{env_vars} pg_dump -h {host} -p {port} -U {user} -d {database} > {backup_file}'
        restore_cmd = f'{env_vars} psql -h {host} -p {port} -U {user} -d {database} < {backup_file}'
        
        return backup_cmd, restore_cmd, backup_file
    
    else:
        logger.error("❌ Unsupported database type. Currently only PostgreSQL is supported.")
        return None, None, None

def backup_database():
    """Create a database backup"""
    try:
        backup_cmd, _, backup_file = get_db_backup_command()
        if not backup_cmd:
            return False
        
        logger.info("📦 Creating database backup...")
        logger.info(f"Backup file: {backup_file}")
        
        # Execute backup command
        exit_code = os.system(backup_cmd)
        
        if exit_code == 0:
            logger.info(f"✅ Database backup created successfully: {backup_file}")
            
            # Check file size
            if os.path.exists(backup_file):
                size_mb = os.path.getsize(backup_file) / (1024 * 1024)
                logger.info(f"📊 Backup size: {size_mb:.2f} MB")
            
            return True
        else:
            logger.error(f"❌ Backup failed with exit code: {exit_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return False

def restore_database(backup_file):
    """Restore database from backup"""
    try:
        if not os.path.exists(backup_file):
            logger.error(f"❌ Backup file not found: {backup_file}")
            return False
        
        _, restore_cmd, _ = get_db_backup_command()
        if not restore_cmd:
            return False
        
        # Replace backup_file in restore command
        restore_cmd = restore_cmd.replace("< {backup_file}", f"< {backup_file}")
        
        logger.warning("🚨 WARNING: This will overwrite the current database!")
        confirmation = input("Are you sure you want to restore? Type 'YES' to confirm: ")
        if confirmation != 'YES':
            logger.info("Restore cancelled.")
            return False
        
        logger.info(f"🔄 Restoring database from {backup_file}...")
        
        # Execute restore command
        exit_code = os.system(restore_cmd)
        
        if exit_code == 0:
            logger.info("✅ Database restored successfully!")
            return True
        else:
            logger.error(f"❌ Restore failed with exit code: {exit_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Restore failed: {e}")
        return False

def export_data():
    """Export database data as JSON"""
    try:
        db = SessionLocal()
        
        logger.info("📤 Exporting database data...")
        
        # Export all tables
        data = {
            "colleges": [],
            "users": [],
            "posts": [],
            "alerts": [],
            "reward_points": [],
            "rewards": []
        }
        
        # Export colleges
        colleges = db.query(College).all()
        for college in colleges:
            data["colleges"].append({
                "id": college.id,
                "name": college.name,
                "slug": college.slug
            })
        
        # Export users (excluding password hashes)
        users = db.query(User).all()
        for user in users:
            data["users"].append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "department": user.department,
                "class_name": user.class_name,
                "academic_year": user.academic_year,
                "college_id": user.college_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })
        
        # Export posts
        posts = db.query(Post).all()
        for post in posts:
            data["posts"].append({
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "image_url": post.image_url,
                "post_type": post.post_type.value if post.post_type else None,
                "author_id": post.author_id,
                "college_id": post.college_id,
                "post_metadata": post.post_metadata,
                "created_at": post.created_at.isoformat() if post.created_at else None
            })
        
        # Export alerts
        alerts = db.query(Alert).all()
        for alert in alerts:
            data["alerts"].append({
                "id": alert.id,
                "user_id": alert.user_id,
                "title": alert.title,
                "message": alert.message,
                "alert_type": alert.alert_type.value if alert.alert_type else None,
                "is_enabled": alert.is_enabled,
                "is_read": alert.is_read,
                "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
                "post_id": alert.post_id,
                "college_id": alert.college_id,
                "created_by": alert.created_by,
                "created_at": alert.created_at.isoformat() if alert.created_at else None
            })
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"data_export_{timestamp}.json"
        
        # Write to file
        with open(export_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"✅ Data exported successfully: {export_file}")
        logger.info(f"📊 Export summary:")
        logger.info(f"   • Colleges: {len(data['colleges'])}")
        logger.info(f"   • Users: {len(data['users'])}")
        logger.info(f"   • Posts: {len(data['posts'])}")
        logger.info(f"   • Alerts: {len(data['alerts'])}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Data export failed: {e}")
        return False

def check_database_health():
    """Check database connection and basic health"""
    try:
        db = SessionLocal()
        
        logger.info("🏥 Checking database health...")
        
        # Test basic query
        result = db.execute(text("SELECT version()")).fetchone()
        logger.info(f"✅ Database connection: OK")
        logger.info(f"📊 Database version: {result[0] if result else 'Unknown'}")
        
        # Check table counts
        tables = {
            "colleges": College,
            "users": User,
            "posts": Post,
            "alerts": Alert,
            "reward_points": RewardPoint,
            "rewards": Reward
        }
        
        logger.info("📋 Table statistics:")
        for table_name, model in tables.items():
            try:
                count = db.query(model).count()
                logger.info(f"   • {table_name}: {count} records")
            except Exception as e:
                logger.warning(f"   • {table_name}: Error ({e})")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Database Management Tool')
    parser.add_argument('action', choices=[
        'backup', 'restore', 'export-data', 'health-check'
    ], help='Action to perform')
    parser.add_argument('file', nargs='?', help='File for restore/import operations')
    
    args = parser.parse_args()
    
    logger.info("🛠️  College Community API - Database Manager")
    logger.info("=" * 50)
    
    if args.action == 'backup':
        success = backup_database()
    elif args.action == 'restore':
        if not args.file:
            logger.error("❌ Backup file required for restore operation")
            sys.exit(1)
        success = restore_database(args.file)
    elif args.action == 'export-data':
        success = export_data()
    elif args.action == 'health-check':
        success = check_database_health()
    else:
        logger.error(f"❌ Unknown action: {args.action}")
        sys.exit(1)
    
    if success:
        logger.info("🎉 Operation completed successfully!")
    else:
        logger.error("❌ Operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()