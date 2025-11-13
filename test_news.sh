#!/bin/bash

# Test script for the news API endpoint

echo "Testing News API Endpoints..."
echo "================================"

# Base URL
BASE_URL="http://localhost:8000"

# First, get a login token (assuming you have test credentials)
echo "1. Testing login to get authentication token..."

# You may need to adjust these credentials based on your test setup
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser@example.com&password=testpass")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    # Extract token from response
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "✅ Login successful"
else
    echo "❌ Login failed. Please ensure you have test users set up."
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo ""
echo "2. Testing tech news endpoint..."
echo "================================"

# Test the tech news endpoint
NEWS_RESPONSE=$(curl -s -X GET "${BASE_URL}/news/tech-headlines" \
  -H "Authorization: Bearer $TOKEN")

echo "$NEWS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print('✅ Tech news endpoint working!')
        print(f'   Articles fetched: {data.get(\"total_articles\", 0)}')
        print(f'   Cache status: {\"Using cache\" if data.get(\"cache_info\", {}).get(\"is_cached\") else \"Fresh data\"}')
        if data.get('articles') and len(data['articles']) > 0:
            print(f'   Sample article: {data[\"articles\"][0].get(\"title\", \"No title\")[:60]}...')
    else:
        print('❌ Tech news endpoint failed')
        print(f'   Error: {data}')
except Exception as e:
    print(f'❌ Failed to parse response: {e}')
    print('Raw response:')
    sys.stdin.seek(0)
    print(sys.stdin.read())
"

echo ""
echo "3. Testing cache status endpoint..."
echo "================================"

CACHE_RESPONSE=$(curl -s -X GET "${BASE_URL}/news/cache-status" \
  -H "Authorization: Bearer $TOKEN")

echo "$CACHE_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('✅ Cache status endpoint working!')
    print(f'   Cache valid: {data.get(\"cache_valid\")}')
    print(f'   Cached articles: {data.get(\"cached_articles_count\", 0)}')
    print(f'   Last updated: {data.get(\"last_updated\", \"Never\")}')
    print(f'   Next refresh: {data.get(\"next_refresh\", \"N/A\")}')
except Exception as e:
    print(f'❌ Failed to parse cache status: {e}')
"

echo ""
echo "4. Testing manual cache refresh..."
echo "================================"

REFRESH_RESPONSE=$(curl -s -X POST "${BASE_URL}/news/refresh-cache" \
  -H "Authorization: Bearer $TOKEN")

echo "$REFRESH_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print('✅ Manual cache refresh working!')
        print(f'   Articles refreshed: {data.get(\"articles_count\", 0)}')
        print(f'   Updated at: {data.get(\"updated_at\")}')
    else:
        print('❌ Manual cache refresh failed')
        print(f'   Error: {data}')
except Exception as e:
    print(f'❌ Failed to parse refresh response: {e}')
"

echo ""
echo "Testing complete! 🎉"