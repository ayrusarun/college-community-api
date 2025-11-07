#!/bin/bash

# Simple script to index existing content for AI search
# This will authenticate with an existing user and trigger content indexing

echo "🤖 College AI Content Indexer"
echo "=============================="

BASE_URL="http://localhost:8000"

# Try to authenticate with a test user
echo "🔑 Authenticating with test user (arjun_cs)..."

# Use JSON format for authentication
AUTH_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "arjun_cs", "password": "password123"}')

TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Authentication failed with arjun_cs. Trying with manual credentials..."
    echo "Please provide your credentials:"
    read -p "Username: " USERNAME
    read -s -p "Password: " PASSWORD
    echo ""
    
    AUTH_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")
    
    TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$TOKEN" ]; then
        echo "❌ Authentication failed. Response: $AUTH_RESPONSE"
        exit 1
    fi
fi

echo "✅ Authentication successful!"

# Check current AI statistics
echo ""
echo "📊 Current AI Statistics:"
curl -s -X GET "$BASE_URL/ai/stats" \
  -H "Authorization: Bearer $TOKEN" | jq . 2>/dev/null || echo "jq not available, raw response above"

echo ""
echo "📋 Current content in database:"
echo "Files: 8, Posts: 12 (from previous check)"

echo ""
echo "🚀 Starting content indexing..."
INDEX_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/index" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content_type": "all"}')

echo "Indexing response: $INDEX_RESPONSE"

# Wait a few seconds for processing to start
echo ""
echo "⏳ Waiting for initial processing (10 seconds)..."
sleep 10

echo ""
echo "📊 Updated AI Statistics:"
curl -s -X GET "$BASE_URL/ai/stats" \
  -H "Authorization: Bearer $TOKEN" | jq . 2>/dev/null || echo "jq not available, showing raw response"

echo ""
echo "🧪 Testing AI search functionality..."
SEARCH_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "computer science engineering",
    "limit": 3
  }')

echo "Search results: $SEARCH_RESPONSE"

echo ""
echo "🎉 Setup complete! Your existing content is being indexed."
echo "📍 You can now:"
echo "   • Visit http://localhost:8000/docs#/ai to see AI endpoints"
echo "   • Use /ai/ask to chat with your AI assistant"
echo "   • Use /ai/search for intelligent content search"
echo "   • Check /ai/stats for indexing progress"
echo ""
echo "💡 Note: Indexing happens in the background. Large files may take a few minutes."