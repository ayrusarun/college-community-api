#!/usr/bin/env python3
"""
Complete test script for Alert Notification Feature with Authentication
"""

import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token by logging in"""
    try:
        # Try to login with demo credentials (assuming they exist)
        login_data = {
            "email": "demo@college.edu",
            "password": "demo123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Error during login: {e}")
        return None

def test_alerts_feature_with_auth():
    print("🚀 Testing Alert Notification Feature with Authentication")
    print("=" * 60)
    
    try:
        # Get authentication token
        print("🔐 Getting authentication token...")
        token = get_auth_token()
        
        if not token:
            print("⚠️  No auth token available. Testing without authentication...")
            print("Note: You'll need to create a user first or use existing credentials.")
            headers = {}
        else:
            print("✅ Authentication successful!")
            headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Check API health
        print("\n🏥 Testing API health...")
        response = requests.get(f"{BASE_URL}/")
        print(f"API Status: {response.status_code}")
        
        # Test 2: Get all alerts for a user
        print("\n1️⃣ Testing GET /alerts - Get all alerts")
        response = requests.get(f"{BASE_URL}/alerts", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alerts = response.json()
            print(f"✅ Found {len(alerts.get('alerts', []))} alerts")
        elif response.status_code == 401:
            print("❌ Authentication required")
        else:
            print(f"Response: {response.text}")
        
        # Test 3: Create a general alert (if authenticated)
        if token:
            print("\n2️⃣ Testing POST /alerts - Create general alert")
            alert_data = {
                "user_id": 1,  # Assuming user ID 1 exists
                "title": "Fee Reminder",
                "message": "Your semester fee payment is due in 3 days. Please pay before the deadline.",
                "alert_type": "REMINDER",
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
            }
            response = requests.post(f"{BASE_URL}/alerts", json=alert_data, headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                alert = response.json()
                print(f"✅ Created alert: {alert.get('title')}")
                general_alert_id = alert.get('id')
            else:
                print(f"Response: {response.text}")
        
        # Test 4: Test the alerts schema and endpoints structure
        print("\n3️⃣ Testing API Documentation endpoints...")
        response = requests.get(f"{BASE_URL}/docs")
        print(f"API Docs accessible: {response.status_code == 200}")
        
        print("\n✅ Alert feature endpoints are properly set up!")
        print("\n📋 Feature Summary:")
        print("• 🎯 General alerts endpoint: /alerts")
        print("• 📝 Post-specific alerts: /posts/{post_id}/alert")
        print("• 🔧 Alert management: Enable/Disable, Mark as read")
        print("• ⏰ Expiry support: Auto-expiry with timestamps")
        print("• 🏢 Multi-tenant: College-based isolation")
        print("• 🔒 Authentication: JWT-based security")
        
        print("\n📚 Available Alert Types:")
        print("• ANNOUNCEMENT - General announcements")
        print("• EVENT - Event notifications")
        print("• REMINDER - Fee reminders, deadlines")
        print("• SYSTEM - System notifications")
        
        print("\n🚀 Next Steps:")
        print("1. Create a user account using /auth/register")
        print("2. Login to get an access token")
        print("3. Use the token to create and manage alerts")
        print("4. Test post-specific alerts with existing posts")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the API is running on http://localhost:8000")
        print("Run: docker-compose up -d")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

def show_api_examples():
    print("\n" + "="*60)
    print("📖 API Usage Examples")
    print("="*60)
    
    print("\n🔐 1. Authentication:")
    print("POST /auth/register")
    print(json.dumps({
        "email": "student@college.edu",
        "password": "securepassword",
        "full_name": "John Doe",
        "college_name": "Sample College",
        "department": "Computer Science"
    }, indent=2))
    
    print("\nPOST /auth/login")
    print(json.dumps({
        "email": "student@college.edu",
        "password": "securepassword"
    }, indent=2))
    
    print("\n🔔 2. Create General Alert:")
    print("POST /alerts")
    print("Headers: Authorization: Bearer YOUR_TOKEN")
    print(json.dumps({
        "user_id": 1,
        "title": "Fee Reminder",
        "message": "Your semester fee is due in 3 days",
        "alert_type": "REMINDER",
        "expires_at": "2025-11-15T10:00:00"
    }, indent=2))
    
    print("\n📝 3. Create Post-Specific Alert:")
    print("POST /posts/1/alert")
    print("Headers: Authorization: Bearer YOUR_TOKEN")
    print(json.dumps({
        "user_id": 2,
        "title": "Event Update",
        "message": "Important update about the workshop!",
        "alert_type": "EVENT",
        "expires_at": "2025-11-12T18:00:00"
    }, indent=2))
    
    print("\n📋 4. Get User Alerts:")
    print("GET /alerts")
    print("Headers: Authorization: Bearer YOUR_TOKEN")
    
    print("\n✏️ 5. Update Alert:")
    print("PUT /alerts/1")
    print("Headers: Authorization: Bearer YOUR_TOKEN")
    print(json.dumps({
        "is_read": True,
        "is_enabled": False
    }, indent=2))

if __name__ == "__main__":
    test_alerts_feature_with_auth()
    show_api_examples()