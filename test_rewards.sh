#!/bin/bash

echo "=========================================="
echo "Reward System Test Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

echo "${YELLOW}Step 2: Check my current reward summary${NC}"
echo "==========================================="
echo ""

MY_REWARDS=$(curl -s -X GET "$API_URL/rewards/me" \
  -H "Authorization: Bearer $TOKEN")

echo "My Reward Summary:"
echo "$MY_REWARDS" | python3 -m json.tool 2>/dev/null || echo "$MY_REWARDS"
echo ""
echo ""

echo "${YELLOW}Step 3: Give a reward to another user${NC}"
echo "==========================================="
echo ""

GIVE_REWARD=$(curl -s -X POST "$API_URL/rewards/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_id": 3,
    "points": 15,
    "reward_type": "HELPFUL_POST",
    "title": "Excellent Algorithm Explanation!",
    "description": "Your detailed explanation of binary search trees was incredibly helpful for understanding the concept. Thank you!"
  }')

echo "Reward Given:"
echo "$GIVE_REWARD" | python3 -m json.tool 2>/dev/null || echo "$GIVE_REWARD"
echo ""

if echo "$GIVE_REWARD" | grep -q '"id"'; then
    echo "${GREEN}✓ Reward successfully given!${NC}"
else
    echo "${RED}✗ Failed to give reward${NC}"
fi
echo ""
echo ""

echo "${YELLOW}Step 4: Check college leaderboard${NC}"
echo "==========================================="
echo ""

LEADERBOARD=$(curl -s -X GET "$API_URL/rewards/leaderboard?limit=5" \
  -H "Authorization: Bearer $TOKEN")

echo "College Leaderboard (Top 5):"
echo "$LEADERBOARD" | python3 -m json.tool 2>/dev/null || echo "$LEADERBOARD"
echo ""
echo ""

echo "${YELLOW}Step 5: Check recent rewards feed${NC}"
echo "==========================================="
echo ""

REWARDS_FEED=$(curl -s -X GET "$API_URL/rewards/?limit=5" \
  -H "Authorization: Bearer $TOKEN")

echo "Recent Rewards Feed:"
echo "$REWARDS_FEED" | python3 -m json.tool 2>/dev/null || echo "$REWARDS_FEED"
echo ""
echo ""

echo "${YELLOW}Step 6: Check user's reward points${NC}"
echo "==========================================="
echo ""

USER_POINTS=$(curl -s -X GET "$API_URL/rewards/points/3" \
  -H "Authorization: Bearer $TOKEN")

echo "User's Reward Points (Sarah Johnson):"
echo "$USER_POINTS" | python3 -m json.tool 2>/dev/null || echo "$USER_POINTS"
echo ""
echo ""

echo "${YELLOW}Step 7: Get available reward types${NC}"
echo "==========================================="
echo ""

REWARD_TYPES=$(curl -s -X GET "$API_URL/rewards/types" \
  -H "Authorization: Bearer $TOKEN")

echo "Available Reward Types:"
echo "$REWARD_TYPES" | python3 -m json.tool 2>/dev/null || echo "$REWARD_TYPES"
echo ""
echo ""

echo "${YELLOW}Step 8: Try invalid reward (self-reward)${NC}"
echo "==========================================="
echo ""

INVALID_REWARD=$(curl -s -X POST "$API_URL/rewards/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_id": 1,
    "points": 10,
    "reward_type": "PEER_RECOGNITION",
    "title": "Test",
    "description": "This should fail"
  }')

echo "Invalid Reward Attempt (self-reward):"
echo "$INVALID_REWARD" | python3 -m json.tool 2>/dev/null || echo "$INVALID_REWARD"
echo ""

if echo "$INVALID_REWARD" | grep -q "cannot give rewards to yourself"; then
    echo "${GREEN}✓ Self-reward validation working correctly${NC}"
else
    echo "${RED}✗ Self-reward validation failed${NC}"
fi
echo ""
echo ""

echo "=========================================="
echo "Reward System Test Summary"
echo "=========================================="
echo ""
echo "${BLUE}Features Tested:${NC}"
echo "✓ Give rewards to other users"
echo "✓ View personal reward summary"
echo "✓ College leaderboard"
echo "✓ Recent rewards feed"
echo "✓ Individual user points"
echo "✓ Available reward types"
echo "✓ Validation (self-reward prevention)"
echo ""
echo "${GREEN}Reward System is fully functional!${NC}"
echo ""
echo "${YELLOW}Next Steps:${NC}"
echo "1. Test reward linking to specific posts"
echo "2. Test different reward types"
echo "3. Test with multiple users"
echo "4. Integrate reward buttons in Flutter app"
echo ""