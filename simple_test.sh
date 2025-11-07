#!/bin/bash

# Simple test - create one test user and upload one file
API_BASE="http://localhost:8000"

echo "🧪 Creating Test User and Uploading Sample File"
echo "=============================================="

# Test user details
USERNAME="testuser"
PASSWORD="password123"
EMAIL="testuser@iitm.ac.in"
FULL_NAME="Test User"
DEPARTMENT="Computer Science & Engineering"
CLASS_NAME="Final Year"
ACADEMIC_YEAR="2024-25"
COLLEGE_ID=52  # IIT Madras from database query

echo "1. Creating test user..."

# Create user (this might fail if user exists)
CREATE_USER_JSON=$(cat <<EOF
{
    "username": "$USERNAME",
    "password": "$PASSWORD",
    "email": "$EMAIL",
    "full_name": "$FULL_NAME",
    "department": "$DEPARTMENT",
    "class_name": "$CLASS_NAME",
    "academic_year": "$ACADEMIC_YEAR",
    "college_id": $COLLEGE_ID
}
EOF
)

CREATE_RESPONSE=$(curl -s -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "$CREATE_USER_JSON")

echo "Create user response: $CREATE_RESPONSE"

echo ""
echo "2. Attempting login..."

# Login
LOGIN_JSON=$(cat <<EOF
{
    "username": "$USERNAME",
    "password": "$PASSWORD"
}
EOF
)

LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d "$LOGIN_JSON")

echo "Login response: $LOGIN_RESPONSE"

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "
try:
    import sys, json
    data = json.load(sys.stdin)
    print(data.get('access_token', ''))
except:
    print('')
" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed"
    exit 1
fi

echo "✅ Login successful"
echo "Token: ${TOKEN:0:50}..."

echo ""
echo "3. Uploading sample file..."

# Create a simple test file
TEST_FILE="sample_upload_test.txt"
cat > $TEST_FILE << 'EOF'
Sample File Upload Test
=======================

This is a test file for the College Community API file upload functionality.

Department: Computer Science & Engineering
Subject: Software Engineering
Topic: File Upload API Testing

Content:
- File upload validation
- Authentication testing
- Database storage verification
- File retrieval testing

This file will be used to verify that:
1. Files can be uploaded successfully
2. File metadata is stored correctly
3. Files can be retrieved and downloaded
4. Department-based organization works
5. College isolation is maintained

Test Date: $(date)
EOF

echo "Created test file: $TEST_FILE"

# Upload file
UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/files/upload" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$TEST_FILE" \
    -F "description=Test file upload for API validation and functionality testing")

echo "Upload response: $UPLOAD_RESPONSE"

# Check if upload was successful
FILE_ID=$(echo $UPLOAD_RESPONSE | python3 -c "
try:
    import sys, json
    data = json.load(sys.stdin)
    print(data.get('id', ''))
except:
    print('')
" 2>/dev/null)

if [ ! -z "$FILE_ID" ]; then
    echo "✅ Upload successful! File ID: $FILE_ID"
    
    echo ""
    echo "4. Testing file retrieval..."
    
    # Get file details
    FILE_DETAILS=$(curl -s -X GET "$API_BASE/files/$FILE_ID" \
        -H "Authorization: Bearer $TOKEN")
    echo "File details: $FILE_DETAILS"
    
    echo ""
    echo "5. Testing file listing..."
    
    # Get files list
    FILES_LIST=$(curl -s -X GET "$API_BASE/files/" \
        -H "Authorization: Bearer $TOKEN")
    echo "Files list: $FILES_LIST"
    
    echo ""
    echo "6. Testing file download..."
    
    # Download file
    curl -s -X GET "$API_BASE/files/$FILE_ID/download" \
        -H "Authorization: Bearer $TOKEN" \
        -o "downloaded_$TEST_FILE"
    
    if [ -f "downloaded_$TEST_FILE" ]; then
        echo "✅ File downloaded successfully"
        echo "Original size: $(wc -c < $TEST_FILE) bytes"
        echo "Downloaded size: $(wc -c < downloaded_$TEST_FILE) bytes"
        
        # Clean up
        rm -f "downloaded_$TEST_FILE"
    else
        echo "❌ File download failed"
    fi
    
    echo ""
    echo "7. Testing file statistics..."
    
    # Get statistics
    STATS=$(curl -s -X GET "$API_BASE/files/stats/summary" \
        -H "Authorization: Bearer $TOKEN")
    echo "Statistics: $STATS"
    
else
    echo "❌ Upload failed"
fi

# Clean up
rm -f $TEST_FILE

echo ""
echo "🎯 Test completed!"