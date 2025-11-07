#!/bin/bash

echo "=========================================="
echo "Content Moderation Test Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

echo "${YELLOW}Step 1: Login to get access token${NC}"
echo "==========================================="
echo ""

# Login and extract token
echo "Logging in as john_doe..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "password123"
  }')

echo "Login Response:"
echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"
echo ""

# Extract the access token
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "${RED}Failed to get token. Please check if server is running and credentials are correct.${NC}"
    exit 1
fi

echo "${GREEN}✓ Successfully logged in!${NC}"
echo "Token: ${TOKEN:0:20}..."
echo ""
echo ""

echo "${YELLOW}Step 2: Test with APPROPRIATE content (Should succeed)${NC}"
echo "==========================================="
echo ""

APPROPRIATE_POST=$(curl -s -X POST "$API_URL/posts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Study Group for Data Structures",
    "content": "Hey everyone! I am organizing a study group for Data Structures class. We will meet every Tuesday and Thursday at the library from 3-5 PM. Topics will include trees, graphs, and dynamic programming. All skill levels welcome! Please DM me if interested.",
    "post_type": "GENERAL"
  }')

echo "Response:"
echo "$APPROPRIATE_POST" | python3 -m json.tool 2>/dev/null || echo "$APPROPRIATE_POST"
echo ""

if echo "$APPROPRIATE_POST" | grep -q '"id"'; then
    echo "${GREEN}✓ Test PASSED: Appropriate content was accepted${NC}"
else
    echo "${RED}✗ Test FAILED: Appropriate content was rejected${NC}"
fi
echo ""
echo ""

echo "${YELLOW}Step 3: Test with INAPPROPRIATE content (Should fail)${NC}"
echo "==========================================="
echo ""

INAPPROPRIATE_POST=$(curl -s -X POST "$API_URL/posts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Offensive Post",
    "content": "This is a damn stupid test with some profanity and offensive bullshit language that should be detected by the AI moderator.",
    "post_type": "GENERAL"
  }')

echo "Response:"
echo "$INAPPROPRIATE_POST" | python3 -m json.tool 2>/dev/null || echo "$INAPPROPRIATE_POST"
echo ""

if echo "$INAPPROPRIATE_POST" | grep -q "Inappropriate content found"; then
    echo "${GREEN}✓ Test PASSED: Inappropriate content was blocked${NC}"
else
    echo "${RED}✗ Test WARNING: Inappropriate content was not blocked (Check if OPENAI_API_KEY is configured)${NC}"
fi
echo ""
echo ""

echo "${YELLOW}Step 4: Test another APPROPRIATE post with image${NC}"
echo "==========================================="
echo ""

APPROPRIATE_POST_2=$(curl -s -X POST "$API_URL/posts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Campus Event: Tech Talk",
    "content": "Join us this Friday for an amazing tech talk by a Google engineer! Topics include cloud computing, microservices, and career advice. Free pizza and networking opportunity. See you there!",
    "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87",
    "post_type": "ANNOUNCEMENT"
  }')

echo "Response:"
echo "$APPROPRIATE_POST_2" | python3 -m json.tool 2>/dev/null || echo "$APPROPRIATE_POST_2"
echo ""

if echo "$APPROPRIATE_POST_2" | grep -q '"id"'; then
    echo "${GREEN}✓ Test PASSED: Appropriate content with image was accepted${NC}"
else
    echo "${RED}✗ Test FAILED: Appropriate content with image was rejected${NC}"
fi
echo ""
echo ""

echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "All tests completed!"
echo ""
echo "If inappropriate content is NOT being blocked:"
echo "1. Check if OPENAI_API_KEY is configured in .env file"
echo "2. Restart Docker containers: docker-compose restart"
echo "3. Check logs: docker-compose logs web"
echo ""
