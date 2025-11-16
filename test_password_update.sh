#!/bin/bash

# Test Password Update API
# This script demonstrates how to use the password update endpoint

BASE_URL="http://localhost:8000"

echo "=== Testing Password Update API ==="
echo ""

# Step 1: Login to get access token
echo "1. Logging in to get access token..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "arjun_cs",
    "password": "password111"
  }')

echo "Login Response: $LOGIN_RESPONSE"
echo ""

# Extract access token
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed. Please check your credentials."
    exit 1
fi

echo "✅ Login successful!"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Step 2: Update password
echo "2. Updating password..."
UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/auth/update-password" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "current_password": "password111",
    "new_password": "p222"
  }')

echo "Update Response: $UPDATE_RESPONSE"
echo ""

# Check if password update was successful
if echo "$UPDATE_RESPONSE" | grep -q "Password updated successfully"; then
    echo "✅ Password updated successfully!"
else
    echo "❌ Password update failed!"
    echo "Response: $UPDATE_RESPONSE"
    exit 1
fi

echo ""
echo "3. Testing login with new password..."
NEW_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "arjun_cs",
    "password": "password222"
  }')

if echo "$NEW_LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login with new password successful!"
    
    # Extract new token
    NEW_TOKEN=$(echo $NEW_LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    # Step 4: Reset password back to original
    echo ""
    echo "4. Resetting password back to original..."
    RESET_RESPONSE=$(curl -s -X PUT "$BASE_URL/auth/update-password" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $NEW_TOKEN" \
      -d '{
        "current_password": "password222",
        "new_password": "password111"
      }')
    
    if echo "$RESET_RESPONSE" | grep -q "Password updated successfully"; then
        echo "✅ Password reset to original successfully!"
    else
        echo "⚠️  Warning: Could not reset password to original"
        echo "   You may need to manually reset it"
    fi
else
    echo "❌ Login with new password failed!"
    echo "Response: $NEW_LOGIN_RESPONSE"
fi

echo ""
echo "=== Test Complete ==="
