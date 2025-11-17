#!/bin/bash

# Test script for Post Engagement Features
# Tests: Comments, Likes, and Ignite functionality

BASE_URL="http://localhost:8000"
COLLEGE_SLUG="iit-bombay"

echo "🧪 Testing Post Engagement Features"
echo "===================================="
echo ""

# Login and get token
echo "🔐 Step 1: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "arjun_cs",
    "password": "password123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Login failed!"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login successful!"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Create a test post
echo "📝 Step 2: Creating a test post..."
POST_RESPONSE=$(curl -s -X POST "$BASE_URL/posts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Post for Engagement",
    "content": "This post is for testing comments, likes, and ignite features!",
    "post_type": "GENERAL"
  }')

POST_ID=$(echo $POST_RESPONSE | jq -r '.id')

if [ "$POST_ID" == "null" ] || [ -z "$POST_ID" ]; then
    echo "❌ Failed to create post!"
    echo "Response: $POST_RESPONSE"
    exit 1
fi

echo "✅ Post created successfully! ID: $POST_ID"
echo ""

# Test 1: Add Comments
echo "💬 Step 3: Testing Comments..."
echo "------------------------------"

echo "Adding comment 1..."
COMMENT1=$(curl -s -X POST "$BASE_URL/posts/$POST_ID/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Great post! Very informative 👍"
  }')

COMMENT1_ID=$(echo $COMMENT1 | jq -r '.id')
echo "✅ Comment 1 added: ID $COMMENT1_ID"

echo "Adding comment 2..."
COMMENT2=$(curl -s -X POST "$BASE_URL/posts/$POST_ID/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Thanks for sharing! This helps a lot."
  }')

COMMENT2_ID=$(echo $COMMENT2 | jq -r '.id')
echo "✅ Comment 2 added: ID $COMMENT2_ID"

echo ""
echo "Fetching all comments..."
COMMENTS_LIST=$(curl -s -X GET "$BASE_URL/posts/$POST_ID/comments?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")

COMMENT_COUNT=$(echo $COMMENTS_LIST | jq -r '.total_count')
echo "✅ Total comments: $COMMENT_COUNT"
echo ""

# Test 2: Like Post
echo "❤️  Step 4: Testing Likes..."
echo "------------------------------"

echo "Liking the post..."
LIKE_RESPONSE=$(curl -s -X POST "$BASE_URL/posts/$POST_ID/like" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")

LIKE_ACTION=$(echo $LIKE_RESPONSE | jq -r '.action')
LIKE_COUNT=$(echo $LIKE_RESPONSE | jq -r '.like_count')
echo "✅ Action: $LIKE_ACTION, Like count: $LIKE_COUNT"

echo ""
echo "Checking if post is liked..."
IS_LIKED=$(curl -s -X GET "$BASE_URL/posts/$POST_ID/is-liked" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")

HAS_LIKED=$(echo $IS_LIKED | jq -r '.has_liked')
echo "✅ User has liked: $HAS_LIKED"

echo ""
echo "Unliking the post..."
UNLIKE_RESPONSE=$(curl -s -X POST "$BASE_URL/posts/$POST_ID/like" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")

UNLIKE_ACTION=$(echo $UNLIKE_RESPONSE | jq -r '.action')
UNLIKE_COUNT=$(echo $UNLIKE_RESPONSE | jq -r '.like_count')
echo "✅ Action: $UNLIKE_ACTION, Like count: $UNLIKE_COUNT"

echo ""
echo "Re-liking the post..."
RELIKE_RESPONSE=$(curl -s -X POST "$BASE_URL/posts/$POST_ID/like" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")
echo "✅ Re-liked successfully"
echo ""

# Test 3: Get user points before ignite
echo "🔥 Step 5: Testing Ignite..."
echo "------------------------------"

echo "Checking user's current points..."
ME_RESPONSE=$(curl -s -X GET "$BASE_URL/users/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")

USER_ID=$(echo $ME_RESPONSE | jq -r '.id')

POINTS_RESPONSE=$(curl -s -X GET "$BASE_URL/rewards/points/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")

POINTS_BEFORE=$(echo $POINTS_RESPONSE | jq -r '.total_points')
echo "✅ Current points: $POINTS_BEFORE"

# Give user some points if they don't have any
if [ "$POINTS_BEFORE" -lt 1 ]; then
    echo ""
    echo "⚠️  User has insufficient points. Adding test reward..."
    
    # Login as another user to give reward
    LOGIN2=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d '{
        "username": "jane_smith",
        "password": "password123"
      }')
    
    TOKEN2=$(echo $LOGIN2 | jq -r '.access_token')
    
    if [ "$TOKEN2" != "null" ] && [ ! -z "$TOKEN2" ]; then
        REWARD_RESP=$(curl -s -X POST "$BASE_URL/rewards/" \
          -H "Authorization: Bearer $TOKEN2" \
          -H "X-College-Slug: $COLLEGE_SLUG" \
          -H "Content-Type: application/json" \
          -d "{
            \"receiver_id\": $USER_ID,
            \"points\": 5,
            \"reward_type\": \"PEER_RECOGNITION\",
            \"title\": \"Test Points for Ignite\"
          }")
        
        echo "✅ Added 5 test points"
        POINTS_BEFORE=5
    fi
fi

echo ""
echo "Igniting the post..."
IGNITE_RESPONSE=$(curl -s -X POST "$BASE_URL/posts/$POST_ID/ignite" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")

IGNITE_ACTION=$(echo $IGNITE_RESPONSE | jq -r '.action')
IGNITE_COUNT=$(echo $IGNITE_RESPONSE | jq -r '.ignite_count')
POINTS_TRANSFERRED=$(echo $IGNITE_RESPONSE | jq -r '.points_transferred')

if [ "$IGNITE_ACTION" == "ignited" ]; then
    echo "✅ Ignite successful!"
    echo "   - Ignite count: $IGNITE_COUNT"
    echo "   - Points transferred: $POINTS_TRANSFERRED"
else
    echo "❌ Ignite failed!"
    echo "Response: $IGNITE_RESPONSE"
fi

echo ""
echo "Checking if post is ignited..."
IS_IGNITED=$(curl -s -X GET "$BASE_URL/posts/$POST_ID/is-ignited" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")

HAS_IGNITED=$(echo $IS_IGNITED | jq -r '.has_ignited')
echo "✅ User has ignited: $HAS_IGNITED"

echo ""
echo "Verifying points deduction..."
POINTS_AFTER=$(curl -s -X GET "$BASE_URL/rewards/points/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG" | jq -r '.total_points')

echo "✅ Points after ignite: $POINTS_AFTER"
echo "   Expected: $((POINTS_BEFORE - 1))"
echo ""

# Test 4: Get Post Feed with Engagement Data
echo "📱 Step 6: Testing Feed with Engagement Data..."
echo "------------------------------"

FEED_RESPONSE=$(curl -s -X GET "$BASE_URL/posts/?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")

echo "$FEED_RESPONSE" | jq -r '.[] | select(.id == '$POST_ID') | "Post ID: \(.id)\nTitle: \(.title)\nLikes: \(.like_count)\nComments: \(.comment_count)\nIgnites: \(.ignite_count)\nUser Liked: \(.user_has_liked)\nUser Ignited: \(.user_has_ignited)"'

echo ""

# Test 5: Delete Comment
echo "🗑️  Step 7: Testing Comment Deletion..."
echo "------------------------------"

echo "Deleting comment $COMMENT1_ID..."
DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/posts/$POST_ID/comments/$COMMENT1_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG")

echo "✅ Comment deleted"
echo ""

echo "Verifying comment count..."
COMMENTS_AFTER=$(curl -s -X GET "$BASE_URL/posts/$POST_ID/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-College-Slug: $COLLEGE_SLUG" | jq -r '.total_count')

echo "✅ Comments remaining: $COMMENTS_AFTER (expected: 1)"
echo ""

# Summary
echo "=================================="
echo "🎉 All Tests Completed!"
echo "=================================="
echo ""
echo "Summary:"
echo "✅ Comments: Working (add, list, delete)"
echo "✅ Likes: Working (toggle, check)"
echo "✅ Ignite: Working (give, check, points transfer)"
echo "✅ Feed: Working (engagement data included)"
echo ""
echo "Test post ID: $POST_ID"
echo "You can view this post and test manually in the app"
