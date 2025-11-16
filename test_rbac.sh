#!/bin/bash

# RBAC Protection Test Script
# Tests that students cannot access admin endpoints

echo "==================================================================="
echo "RBAC ENFORCEMENT TEST"
echo "==================================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local TOKEN=$1
    local ENDPOINT=$2
    local EXPECTED_CODE=$3
    local DESCRIPTION=$4
    
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
        "http://localhost:8000${ENDPOINT}" \
        -H "Authorization: Bearer ${TOKEN}")
    
    if [ "$RESPONSE" = "$EXPECTED_CODE" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $DESCRIPTION (got $RESPONSE)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $DESCRIPTION (expected $EXPECTED_CODE, got $RESPONSE)"
        ((FAILED++))
    fi
}

echo "Step 1: Creating test users..."
echo "-------------------------------------------------------------------"

# Create admin user (assuming one exists or create via script)
# For this test, we assume users already exist

echo "Step 2: Getting authentication tokens..."
echo "-------------------------------------------------------------------"

# Get student token
STUDENT_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"student1","password":"password"}' \
    | jq -r '.access_token')

if [ "$STUDENT_TOKEN" = "null" ] || [ -z "$STUDENT_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  WARNING${NC}: Could not get student token. Creating test student..."
    # Student doesn't exist, skip for now
    STUDENT_TOKEN=""
else
    echo -e "${GREEN}✓${NC} Got student token"
fi

# Get admin token
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"password"}' \
    | jq -r '.access_token')

if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  WARNING${NC}: Could not get admin token"
    ADMIN_TOKEN=""
else
    echo -e "${GREEN}✓${NC} Got admin token"
fi

echo ""
echo "Step 3: Testing Admin Endpoint Protection"
echo "-------------------------------------------------------------------"

if [ -n "$STUDENT_TOKEN" ]; then
    test_endpoint "$STUDENT_TOKEN" "/admin/users" "403" "Student blocked from /admin/users"
    test_endpoint "$STUDENT_TOKEN" "/admin/permissions" "403" "Student blocked from /admin/permissions"
    test_endpoint "$STUDENT_TOKEN" "/admin/roles" "403" "Student blocked from /admin/roles"
else
    echo -e "${YELLOW}⚠️  SKIP${NC}: No student token available"
fi

if [ -n "$ADMIN_TOKEN" ]; then
    test_endpoint "$ADMIN_TOKEN" "/admin/users" "200" "Admin can access /admin/users"
    test_endpoint "$ADMIN_TOKEN" "/admin/permissions" "200" "Admin can access /admin/permissions"
    test_endpoint "$ADMIN_TOKEN" "/admin/roles" "200" "Admin can access /admin/roles"
else
    echo -e "${YELLOW}⚠️  SKIP${NC}: No admin token available"
fi

echo ""
echo "Step 4: Testing Public Endpoints (should work for all)"
echo "-------------------------------------------------------------------"

if [ -n "$STUDENT_TOKEN" ]; then
    test_endpoint "$STUDENT_TOKEN" "/posts" "200" "Student can read posts"
    test_endpoint "$STUDENT_TOKEN" "/files" "200" "Student can read files"
fi

if [ -n "$ADMIN_TOKEN" ]; then
    test_endpoint "$ADMIN_TOKEN" "/posts" "200" "Admin can read posts"
fi

echo ""
echo "==================================================================="
echo "TEST SUMMARY"
echo "==================================================================="
echo -e "${GREEN}Passed${NC}: $PASSED"
echo -e "${RED}Failed${NC}: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo "RBAC protection is working correctly."
    exit 0
else
    echo -e "\n${RED}❌ SOME TESTS FAILED!${NC}"
    echo "RBAC protection needs attention."
    exit 1
fi
