# Database Migration System 🚀

This system handles database schema changes and future migrations automatically.

## Quick Start

### Fresh Installation
```bash
python db_setup.py
```
Auto-detects if you need fresh installation or just migrations.

### Manual Commands
```bash
# Fresh database setup
python db_setup.py --fresh

# Apply pending migrations  
python db_setup.py --migrate

# Check migration status
python db_setup.py --status

# Reset database (⚠️ DELETES ALL DATA)
python db_setup.py --reset
```

## Creating New Schema Changes

### 1. Create Migration
```bash
python db_setup.py --create-migration "Add user preferences"
```
This creates: `migrations/20241114_143022_add_user_preferences.sql`

### 2. Edit Migration File
```sql
-- Name: Add User Preferences
-- Description: Add user preferences table
-- Version: 20241114_143022
-- Created: 2024-11-14T14:30:22

-- Your SQL changes here
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    theme VARCHAR(20) DEFAULT 'light',
    notifications BOOLEAN DEFAULT true,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id);
```

### 3. Apply Migration
```bash
python db_setup.py --migrate
```

## Migration Examples

### Adding New Table
```bash
python db_setup.py --create-migration "Add discussion forums"
```

### Modifying Existing Table  
```bash
python db_setup.py --create-migration "Add email verification to users"
```

### Adding Indexes
```bash
python db_setup.py --create-migration "Add performance indexes"
```

## System Features

✅ **Version Tracking** - Each migration has unique timestamp version  
✅ **Checksum Validation** - Detects if applied migrations were modified  
✅ **Safe Execution** - Won't apply same migration twice  
✅ **Error Handling** - Rolls back on failure  
✅ **Performance Tracking** - Records execution time  
✅ **Template Generation** - Auto-generates migration templates  

## Production Workflow

### New Server Setup
```bash
# 1. Clone repo
git clone your-repo

# 2. Setup database
python db_setup.py

# 3. Start application
docker-compose up
```

### Schema Updates
```bash
# Developer creates migration
python db_setup.py --create-migration "New feature schema"

# Edit the generated SQL file
# Commit to git

# Production deployment
git pull
python db_setup.py --migrate
```

## Migration File Format

```sql
-- Name: Human readable name
-- Description: What this migration does  
-- Version: 20241114_143022 (auto-generated)
-- Created: 2024-11-14T14:30:22 (auto-generated)

-- Your SQL statements here
-- Use IF NOT EXISTS for safety
-- Add proper indexes
-- Include sample data if needed
```

## Migration Status

Check what's applied vs pending:
```bash
python db_setup.py --status
```

Output:
```
📋 Migration Status
==================================================
✅ Applied migrations (3):
   • baseline - Initial database schema  
   • 20241114_120000 - Add Rewards Store System
   • 20241114_143022 - Add User Preferences

⏳ Pending migrations (1):
   • 20241114_150000 - Add Discussion Forums
```

## Safety Features

- **Automatic Backups** - Consider adding pg_dump before migrations
- **Rollback Support** - Create reverse migrations when needed  
- **Testing** - Test migrations on development first
- **Checksum Verification** - Prevents modified migration re-execution

## Troubleshooting

### Migration Fails
```bash
# Check what failed
python db_setup.py --status

# Fix the migration file
# Re-run
python db_setup.py --migrate
```

### Start Fresh (Development Only)
```bash
python db_setup.py --reset
```

### Manual Database Operations
```bash
# Connect to PostgreSQL
psql postgresql://college_user:college_pass@localhost:5432/college_community_db

# Check migration table
SELECT * FROM schema_migrations ORDER BY applied_at;
```

This system grows with your project and keeps your database schema organized! 🎯