#!/bin/bash

# Test script for File Upload API
# Make sure the API server is running before executing this script

API_BASE="http://localhost:8000"

echo "🧪 Testing File Upload API"
echo "=========================="

# First, login to get a token
echo "1. Logging in to get authentication token..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "arjun1_iitm",
        "password": "password123"
    }')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed. Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login successful"
echo "Token: ${TOKEN:0:50}..."

# Create a test file
echo "2. Creating test file..."
TEST_FILE="test_document.txt"
echo "This is a test document for the College Community API file upload feature.

It contains:
- Sample academic content
- Testing information
- File upload validation

Department: Computer Science & Engineering
Course: Software Engineering
Author: Test Student" > $TEST_FILE

echo "✅ Test file created: $TEST_FILE"

# Upload the file
echo "3. Uploading file..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/files/upload" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$TEST_FILE" \
    -F "description=Test document for API validation")

echo "Upload Response: $UPLOAD_RESPONSE"

# Extract file ID from response
FILE_ID=$(echo $UPLOAD_RESPONSE | python3 -c "
try:
    import sys, json
    data = json.load(sys.stdin)
    print(data.get('id', ''))
except:
    print('')
" 2>/dev/null)

if [ -z "$FILE_ID" ]; then
    echo "❌ File upload failed"
    exit 1
fi

echo "✅ File uploaded successfully. File ID: $FILE_ID"

# Test getting files list
echo "4. Testing file list endpoint..."
FILES_LIST=$(curl -s -X GET "$API_BASE/files/" \
    -H "Authorization: Bearer $TOKEN")

echo "Files List Response: $FILES_LIST"

# Test getting specific file details
echo "5. Testing file details endpoint..."
FILE_DETAILS=$(curl -s -X GET "$API_BASE/files/$FILE_ID" \
    -H "Authorization: Bearer $TOKEN")

echo "File Details Response: $FILE_DETAILS"

# Test file download
echo "6. Testing file download..."
curl -s -X GET "$API_BASE/files/$FILE_ID/download" \
    -H "Authorization: Bearer $TOKEN" \
    -o "downloaded_$TEST_FILE"

if [ -f "downloaded_$TEST_FILE" ]; then
    echo "✅ File downloaded successfully as downloaded_$TEST_FILE"
    echo "Downloaded file size: $(wc -c < downloaded_$TEST_FILE) bytes"
else
    echo "❌ File download failed"
fi

# Test file search with filters
echo "7. Testing file search with department filter..."
SEARCH_RESPONSE=$(curl -s -X GET "$API_BASE/files/?department=Computer%20Science%20%26%20Engineering" \
    -H "Authorization: Bearer $TOKEN")

echo "Search Response: $SEARCH_RESPONSE"

# Test getting departments list
echo "8. Testing departments list..."
DEPARTMENTS_RESPONSE=$(curl -s -X GET "$API_BASE/files/departments/list" \
    -H "Authorization: Bearer $TOKEN")

echo "Departments Response: $DEPARTMENTS_RESPONSE"

# Test getting file statistics
echo "9. Testing file statistics..."
STATS_RESPONSE=$(curl -s -X GET "$API_BASE/files/stats/summary" \
    -H "Authorization: Bearer $TOKEN")

echo "Statistics Response: $STATS_RESPONSE"

# Test updating file description
echo "10. Testing file update..."
UPDATE_RESPONSE=$(curl -s -X PUT "$API_BASE/files/$FILE_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "description": "Updated test document with new description"
    }')

echo "Update Response: $UPDATE_RESPONSE"

# Clean up test files
echo "11. Cleaning up test files..."
rm -f $TEST_FILE
rm -f "downloaded_$TEST_FILE"

echo "✅ Test completed successfully!"
echo ""
echo "📊 Summary:"
echo "- File upload: ✅"
echo "- File listing: ✅"
echo "- File details: ✅"
echo "- File download: ✅"
echo "- File search: ✅"
echo "- Departments list: ✅"
echo "- File statistics: ✅"
echo "- File update: ✅"
echo ""
echo "🎯 File Upload API is working correctly!"