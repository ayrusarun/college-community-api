#!/bin/bash

# RBAC Migration Runner for Production
# This script applies the RBAC migration safely and can be run multiple times

set -e  # Exit on error

echo "=================================================="
echo "RBAC Migration Script"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if docker-compose is running
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}Error: Docker containers are not running${NC}"
    echo "Please start the containers first: docker-compose up -d"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker containers are running"
echo ""

# Check if migration file exists
MIGRATION_FILE="migrations/20241116_120000_add_rbac_system.sql"
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}Error: Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Migration file found"
echo ""

# Backup reminder
echo -e "${YELLOW}⚠️  REMINDER: Have you backed up your database?${NC}"
echo "   This migration is idempotent and safe, but backups are always recommended."
echo ""
read -p "Continue with migration? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled."
    exit 0
fi

echo ""
echo "Running RBAC migration..."
echo "=================================================="
echo ""

# Run the migration
if cat "$MIGRATION_FILE" | docker-compose exec -T db psql -U postgres -d college_community; then
    echo ""
    echo -e "${GREEN}✓ Migration completed successfully!${NC}"
    echo ""
    
    # Show current user role distribution
    echo "Current User Distribution:"
    echo "=================================================="
    docker-compose exec -T db psql -U postgres -d college_community -c \
        "SELECT role, COUNT(*) as count FROM users GROUP BY role ORDER BY role;"
    
    echo ""
    echo "Next Steps:"
    echo "=================================================="
    echo "1. Promote admin users (if needed):"
    echo "   docker-compose exec db psql -U postgres -d college_community -c \\"
    echo "     \"UPDATE users SET role = 'admin' WHERE username = 'your_admin_username';\""
    echo ""
    echo "2. Restart the application to load RBAC:"
    echo "   docker-compose restart web"
    echo ""
    echo "3. Test the RBAC system:"
    echo "   - Login and check: GET http://localhost:8000/auth/me"
    echo "   - Try admin endpoints: GET http://localhost:8000/admin/users"
    echo ""
    
else
    echo ""
    echo -e "${RED}✗ Migration failed${NC}"
    echo "Please check the error messages above."
    exit 1
fi
