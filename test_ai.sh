#!/bin/bash

# Test script for AI functionality

echo "🤖 Testing College AI Assistant Features"
echo "========================================"

# Base URL for API
BASE_URL="http://localhost:8000"

# Test authentication first (you'll need to update these credentials)
USERNAME="test_user"
PASSWORD="test_password"

echo "1. Authenticating user..."
AUTH_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Authentication failed. Please ensure you have a valid user account."
    echo "Response: $AUTH_RESPONSE"
    exit 1
fi

echo "✅ Authentication successful"

# Test AI endpoints
echo ""
echo "2. Testing AI statistics..."
curl -s -X GET "$BASE_URL/ai/stats" \
  -H "Authorization: Bearer $TOKEN" | jq .

echo ""
echo "3. Testing knowledge search..."
curl -s -X POST "$BASE_URL/ai/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "computer science courses",
    "content_type": "file",
    "limit": 3
  }' | jq .

echo ""
echo "4. Testing AI chat assistant..."
curl -s -X POST "$BASE_URL/ai/ask" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What files are available for computer science students?",
    "context_filter": "files"
  }' | jq .

echo ""
echo "5. Testing indexing request..."
curl -s -X POST "$BASE_URL/ai/index" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "all"
  }' | jq .

echo ""
echo "6. Getting conversation history..."
curl -s -X GET "$BASE_URL/ai/conversations?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq .

echo ""
echo "🎉 AI testing completed!"
echo ""
echo "Note: For full functionality, make sure:"
echo "- OPENAI_API_KEY is set in your environment"
echo "- The required Python packages are installed (numpy, PyPDF2, python-docx)"
echo "- Some files and posts exist in your college database"