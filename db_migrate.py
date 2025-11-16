#!/usr/bin/env python3
"""
Simple database migration runner for production
Uses psycopg2 instead of SQLAlchemy to avoid version conflicts
"""

import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ Error: psycopg2 not installed")
    print("Install it with: pip install psycopg2-binary")
    sys.exit(1)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/college_community')

def parse_database_url(url):
    """Parse DATABASE_URL into connection parameters"""
    # Remove postgresql:// prefix
    url = url.replace('postgresql://', '')
    
    # Split user:pass@host:port/db
    if '@' in url:
        auth, rest = url.split('@', 1)
        user, password = auth.split(':', 1) if ':' in auth else (auth, '')
    else:
        user = 'postgres'
        password = ''
        rest = url
    
    if '/' in rest:
        host_port, database = rest.split('/', 1)
    else:
        host_port = rest
        database = 'college_community'
    
    if ':' in host_port:
        host, port = host_port.split(':', 1)
    else:
        host = host_port
        port = '5432'
    
    return {
        'host': host,
        'port': port,
        'database': database,
        'user': user,
        'password': password
    }

class SimpleMigrationManager:
    def __init__(self):
        self.db_params = parse_database_url(DATABASE_URL)
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)
        
    def get_connection(self):
        """Create database connection"""
        return psycopg2.connect(**self.db_params)
    
    def create_migration_table(self):
        """Create migration tracking table"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        checksum VARCHAR(64) NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        execution_time_ms INTEGER
                    )
                """)
                conn.commit()
        finally:
            conn.close()
    
    def get_applied_migrations(self):
        """Get list of applied migrations"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(
                        "SELECT version, name, checksum FROM schema_migrations ORDER BY version"
                    )
                    return {row[0]: {'name': row[1], 'checksum': row[2]} for row in cursor.fetchall()}
                except psycopg2.Error:
                    return {}
        finally:
            conn.close()
    
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
                print(f"⚠️  Warning: Migration {version} has been modified after applying")
        
        return pending
    
    def apply_migration(self, migration):
        """Apply a single migration"""
        print(f"📦 Applying migration {migration['version']}...")
        
        start_time = datetime.now()
        
        conn = self.get_connection()
        try:
            # Read migration content
            content = migration['file'].read_text()
            
            # Extract metadata from comments
            lines = content.split('\n')
            name = migration['version']
            
            for line in lines[:10]:  # Check first 10 lines for metadata
                if line.startswith('-- Name:'):
                    name = line.replace('-- Name:', '').strip()
                    break
            
            with conn.cursor() as cursor:
                # Execute migration SQL
                cursor.execute(content)
                
                # Record migration
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                cursor.execute("""
                    INSERT INTO schema_migrations (version, name, checksum, execution_time_ms)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (version) DO NOTHING
                """, (
                    migration['version'],
                    name,
                    migration['checksum'],
                    int(execution_time)
                ))
                
                conn.commit()
                print(f"   ✅ Applied successfully ({int(execution_time)}ms)")
        
        except Exception as e:
            conn.rollback()
            print(f"   ❌ Failed: {e}")
            raise
        finally:
            conn.close()
    
    def migrate(self):
        """Apply all pending migrations"""
        print("=" * 60)
        print("DATABASE MIGRATION")
        print("=" * 60)
        print()
        
        self.create_migration_table()
        
        pending = self.get_pending_migrations()
        
        if not pending:
            print("✅ No pending migrations - database is up to date")
            return True
        
        print(f"🔄 Found {len(pending)} pending migration(s)")
        print()
        
        for migration in pending:
            try:
                self.apply_migration(migration)
            except Exception as e:
                print(f"\n❌ Migration failed: {e}")
                return False
        
        print()
        print("=" * 60)
        print("🎉 All migrations applied successfully!")
        print("=" * 60)
        return True
    
    def status(self):
        """Show migration status"""
        self.create_migration_table()
        
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        print("=" * 60)
        print("📋 MIGRATION STATUS")
        print("=" * 60)
        print()
        
        if applied:
            print(f"✅ Applied migrations ({len(applied)}):")
            for version, info in applied.items():
                print(f"   • {version}")
                print(f"     {info['name']}")
            print()
        
        if pending:
            print(f"⏳ Pending migrations ({len(pending)}):")
            for migration in pending:
                print(f"   • {migration['version']}")
            print()
        
        if not applied and not pending:
            print("🆕 No migrations found")
            print()

def main():
    """Main CLI interface"""
    args = sys.argv[1:]
    
    manager = SimpleMigrationManager()
    
    if not args or args[0] == "--migrate":
        success = manager.migrate()
        sys.exit(0 if success else 1)
    
    elif args[0] == "--status":
        manager.status()
    
    else:
        print("Database Migration System")
        print("=" * 40)
        print("Usage:")
        print("  python3 db_setup.py --migrate    # Apply pending migrations")
        print("  python3 db_setup.py --status     # Show migration status")
        print()
        print("Environment Variables:")
        print("  DATABASE_URL - PostgreSQL connection string")
        print("  Default: postgresql://postgres:postgres@localhost:5433/college_community")

if __name__ == "__main__":
    main()
