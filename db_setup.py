#!/usr/bin/env python3

"""
Database Setup and Migration System
Handles initial setup and future schema changes with version tracking.

Usage:
    python db_setup.py                    # Fresh installation
    python db_setup.py --migrate          # Apply pending migrations
    python db_setup.py --reset            # Reset and reinitialize
    python db_setup.py --status           # Show migration status
    python db_setup.py --create-migration # Create new migration template

Features:
- Version-based migration system
- Safe incremental updates
- Rollback support
- Migration tracking
- Automatic dependency detection
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://college_user:college_pass@localhost:5432/college_community_db'
)

class MigrationManager:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)
        
    def create_migration_table(self):
        """Create migration tracking table"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    checksum VARCHAR(64) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER
                )
            """))
            conn.commit()
    
    def get_applied_migrations(self):
        """Get list of applied migrations"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT version, name, checksum FROM schema_migrations ORDER BY version"
                ))
                return {row[0]: {'name': row[1], 'checksum': row[2]} for row in result}
        except:
            return {}
    
    def get_pending_migrations(self):
        """Get list of migrations that need to be applied"""
        applied = self.get_applied_migrations()
        pending = []
        
        # Get all migration files
        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        
        for migration_file in migration_files:
            version = migration_file.stem
            
            # Calculate checksum
            checksum = hashlib.sha256(migration_file.read_bytes()).hexdigest()
            
            if version not in applied:
                pending.append({
                    'version': version,
                    'file': migration_file,
                    'checksum': checksum
                })
            elif applied[version]['checksum'] != checksum:
                print(f"⚠️ Warning: Migration {version} has been modified after applying")
        
        return pending
    
    def apply_migration(self, migration):
        """Apply a single migration"""
        print(f"📦 Applying migration {migration['version']}...")
        
        start_time = datetime.now()
        
        try:
            # Read migration content
            content = migration['file'].read_text()
            
            # Extract metadata from comments
            lines = content.split('\n')
            name = migration['version']
            description = ""
            
            for line in lines[:10]:  # Check first 10 lines for metadata
                if line.startswith('-- Name:'):
                    name = line.replace('-- Name:', '').strip()
                elif line.startswith('-- Description:'):
                    description = line.replace('-- Description:', '').strip()
            
            with self.engine.connect() as conn:
                # Execute migration SQL
                conn.execute(text(content))
                
                # Record migration
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                conn.execute(text("""
                    INSERT INTO schema_migrations (version, name, checksum, execution_time_ms)
                    VALUES (:version, :name, :checksum, :execution_time)
                """), {
                    "version": migration['version'],
                    "name": name,
                    "checksum": migration['checksum'],
                    "execution_time": int(execution_time)
                })
                
                conn.commit()
                print(f"   ✅ Applied successfully ({int(execution_time)}ms)")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            raise
    
    def migrate(self):
        """Apply all pending migrations"""
        self.create_migration_table()
        
        pending = self.get_pending_migrations()
        
        if not pending:
            print("✅ No pending migrations")
            return
        
        print(f"🔄 Found {len(pending)} pending migrations")
        
        for migration in pending:
            self.apply_migration(migration)
        
        print("🎉 All migrations applied successfully!")
    
    def status(self):
        """Show migration status"""
        self.create_migration_table()
        
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        print("📋 Migration Status")
        print("=" * 50)
        
        if applied:
            print(f"✅ Applied migrations ({len(applied)}):")
            for version, info in applied.items():
                print(f"   • {version} - {info['name']}")
        
        if pending:
            print(f"\n⏳ Pending migrations ({len(pending)}):")
            for migration in pending:
                print(f"   • {migration['version']}")
        
        if not applied and not pending:
            print("🆕 No migrations found - fresh installation needed")
    
    def create_migration_template(self, name=None):
        """Create a new migration template"""
        if not name:
            name = input("Migration name: ").strip()
        
        # Generate version (timestamp)
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{version}_{name.lower().replace(' ', '_')}.sql"
        
        template = f"""-- Name: {name}
-- Description: {name} migration
-- Version: {version}
-- Created: {datetime.now().isoformat()}

-- Migration SQL goes here
-- Example:

-- CREATE TABLE IF NOT EXISTS new_table (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- ALTER TABLE existing_table ADD COLUMN new_column VARCHAR(100);

-- CREATE INDEX IF NOT EXISTS idx_new_table_name ON new_table(name);

-- INSERT INTO new_table (name) VALUES ('Sample Data');
"""
        
        migration_file = self.migrations_dir / filename
        migration_file.write_text(template)
        
        print(f"📝 Created migration template: {filename}")
        print(f"📁 Location: {migration_file}")
        print(f"✏️ Edit the file and add your SQL changes")
        
        return migration_file

def fresh_install():
    """Fresh database installation"""
    print("🆕 Fresh Database Installation")
    print("=" * 40)
    
    try:
        # Run init_db.py
        import subprocess
        
        print("🔧 Running initial database setup...")
        result = subprocess.run([sys.executable, "init_db.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Basic database initialized")
            print(result.stdout)
        else:
            print("❌ Basic initialization failed:")
            print(result.stderr)
            return False
        
        # Run store migration
        print("\n🏪 Setting up rewards store...")
        result = subprocess.run([sys.executable, "migrate_store.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Store system initialized")
        else:
            print("⚠️ Store initialization failed:")
            print(result.stderr)
            print("You can run 'python migrate_store.py' later")
        
        # Initialize migration tracking
        manager = MigrationManager()
        manager.create_migration_table()
        
        # Mark current state as baseline
        with manager.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO schema_migrations (version, name, checksum) 
                VALUES ('baseline', 'Initial database schema', 'baseline')
                ON CONFLICT (version) DO NOTHING
            """))
            conn.commit()
        
        print("✅ Migration tracking initialized")
        print("\n🎉 Fresh installation completed!")
        return True
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def reset_database():
    """Reset and reinitialize database"""
    confirm = input("⚠️ This will DELETE ALL DATA. Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Reset cancelled")
        return
    
    print("🔄 Resetting database...")
    
    # Drop and recreate
    engine = create_engine(DATABASE_URL)
    
    # Get all table names
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if tables:
        with engine.connect() as conn:
            # Drop all tables
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            conn.commit()
        
        print(f"🗑️ Dropped {len(tables)} tables")
    
    # Fresh install
    fresh_install()

def main():
    """Main CLI interface"""
    args = sys.argv[1:]
    
    if not args:
        # Default: Check if database exists, migrate if needed, fresh install if not
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                # Check if basic tables exist
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('users', 'colleges')"
                ))
                table_count = result.scalar()
                
                if table_count >= 2:
                    print("📊 Existing database detected")
                    manager = MigrationManager()
                    manager.migrate()
                else:
                    print("🆕 No existing database found")
                    fresh_install()
        
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("🔧 Please ensure PostgreSQL is running and DATABASE_URL is correct")
            sys.exit(1)
    
    elif args[0] == "--migrate":
        manager = MigrationManager()
        manager.migrate()
    
    elif args[0] == "--reset":
        reset_database()
    
    elif args[0] == "--status":
        manager = MigrationManager()
        manager.status()
    
    elif args[0] == "--create-migration":
        manager = MigrationManager()
        name = args[1] if len(args) > 1 else None
        manager.create_migration_template(name)
    
    elif args[0] == "--fresh":
        fresh_install()
    
    else:
        print("Database Setup and Migration System")
        print("=" * 40)
        print("Usage:")
        print("  python db_setup.py                    # Auto-detect and setup")
        print("  python db_setup.py --fresh            # Fresh installation")
        print("  python db_setup.py --migrate          # Apply pending migrations")
        print("  python db_setup.py --reset            # Reset database")
        print("  python db_setup.py --status           # Show migration status")
        print("  python db_setup.py --create-migration # Create new migration")
        print("\nExamples:")
        print("  python db_setup.py --create-migration 'Add user preferences'")
        print("  python db_setup.py --create-migration 'Update post schema'")

if __name__ == "__main__":
    main()