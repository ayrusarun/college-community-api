#!/bin/bash

# Migration script for Post Engagement Features
# Run this script to add comments, likes, and ignite features

echo "🚀 Starting Post Engagement Migration..."

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Database connection details
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-college_community}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

echo "📊 Database: $DB_NAME"
echo "🖥️  Host: $DB_HOST:$DB_PORT"
echo "👤 User: $DB_USER"
echo ""

# Check if PostgreSQL is accessible
echo "🔍 Checking database connection..."
if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c '\q' 2>/dev/null; then
    echo "❌ Error: Cannot connect to database"
    echo "Please check your database credentials and ensure PostgreSQL is running"
    exit 1
fi

echo "✅ Database connection successful"
echo ""

# Run migration
echo "📝 Running migration: 20241117_120000_add_post_engagement.sql"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f migrations/20241117_120000_add_post_engagement.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration completed successfully!"
    echo ""
    echo "📋 Summary of changes:"
    echo "   ✅ Created post_likes table"
    echo "   ✅ Created post_comments table"
    echo "   ✅ Created post_ignites table"
    echo "   ✅ Added like_count, comment_count, ignite_count to posts"
    echo "   ✅ Created optimized indexes"
    echo "   ✅ Created automatic counter update triggers"
    echo ""
    echo "🎉 Post engagement features are now available!"
else
    echo ""
    echo "❌ Migration failed!"
    echo "Please check the error messages above"
    exit 1
fi
