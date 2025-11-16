#!/bin/bash

# Quick verification script for folder feature
# This script checks if the folder endpoints are accessible

BASE_URL="http://localhost:8000"

echo "================================================"
echo "FOLDER FEATURE - QUICK VERIFICATION"
echo "================================================"
echo ""

# Check if API is running
echo "1. Checking if API is running..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs")
if [ "$response" = "200" ]; then
    echo "   ✅ API is running (http://localhost:8000)"
else
    echo "   ❌ API is not responding (got HTTP $response)"
    echo "   Please check: docker-compose ps"
    exit 1
fi
echo ""

# Check API documentation for new endpoints
echo "2. Checking API documentation..."
response=$(curl -s "$BASE_URL/openapi.json")

if echo "$response" | grep -q "folders/create"; then
    echo "   ✅ Folder create endpoint found"
else
    echo "   ⚠️  Folder create endpoint not found in API docs"
fi

if echo "$response" | grep -q "folders/browse"; then
    echo "   ✅ Folder browse endpoint found"
else
    echo "   ⚠️  Folder browse endpoint not found in API docs"
fi

if echo "$response" | grep -q "folders/delete"; then
    echo "   ✅ Folder delete endpoint found"
else
    echo "   ⚠️  Folder delete endpoint not found in API docs"
fi

if echo "$response" | grep -q "folders/move"; then
    echo "   ✅ Folder move endpoint found"
else
    echo "   ⚠️  Folder move endpoint not found in API docs"
fi

echo ""
echo "3. Database schema verification..."
# Check database
db_check=$(docker-compose exec -T db psql -U postgres -d college_community -c "\d files" 2>&1)

if echo "$db_check" | grep -q "folder_path"; then
    echo "   ✅ folder_path column exists"
else
    echo "   ❌ folder_path column missing"
fi

if echo "$db_check" | grep -q "is_folder"; then
    echo "   ✅ is_folder column exists"
else
    echo "   ❌ is_folder column missing"
fi

if echo "$db_check" | grep -q "parent_folder_id"; then
    echo "   ✅ parent_folder_id column exists"
else
    echo "   ❌ parent_folder_id column missing"
fi

if echo "$db_check" | grep -q "idx_files_folder_path"; then
    echo "   ✅ folder_path index exists"
else
    echo "   ⚠️  folder_path index missing"
fi

echo ""
echo "================================================"
echo "VERIFICATION COMPLETE"
echo "================================================"
echo ""
echo "📚 Next Steps:"
echo ""
echo "1. Get your authentication token:"
echo "   curl -X POST 'http://localhost:8000/auth/login' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"username\":\"your_username\",\"password\":\"your_password\"}'"
echo ""
echo "2. Test folder creation (replace YOUR_TOKEN):"
echo "   curl -X POST 'http://localhost:8000/files/folders/create' \\"
echo "     -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"name\":\"Test Folder\",\"parent_path\":\"/\"}'"
echo ""
echo "3. Browse root folder:"
echo "   curl -X GET 'http://localhost:8000/files/folders/browse?folder_path=/' \\"
echo "     -H 'Authorization: Bearer YOUR_TOKEN'"
echo ""
echo "4. View API documentation:"
echo "   Open: http://localhost:8000/docs"
echo ""
echo "📖 Documentation:"
echo "   • Full docs: FOLDER_FEATURE_DOCUMENTATION.md"
echo "   • Quick ref: FOLDER_QUICK_REFERENCE.md"
echo "   • Summary:   FOLDER_IMPLEMENTATION_SUMMARY.md"
echo ""
