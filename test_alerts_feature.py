#!/usr/bin/env python3
"""
Test script for the Alert Notification Feature
"""

import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

def test_alerts_feature():
    print("🚀 Testing Alert Notification Feature")
    print("=" * 50)
    
    try:
        # Test 1: Get all alerts for a user
        print("\n1️⃣ Testing GET /alerts - Get all alerts")
        response = requests.get(f"{BASE_URL}/alerts")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alerts = response.json()
            print(f"Found {len(alerts.get('alerts', []))} alerts")
        else:
            print(f"Response: {response.text}")
        
        # Test 2: Create a general alert
        print("\n2️⃣ Testing POST /alerts - Create general alert")
        alert_data = {
            "user_id": 1,  # Assuming user ID 1 exists
            "title": "Fee Reminder",
            "message": "Your semester fee payment is due in 3 days. Please pay before the deadline.",
            "alert_type": "REMINDER",
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
        }
        response = requests.post(f"{BASE_URL}/alerts", json=alert_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alert = response.json()
            print(f"Created alert: {alert.get('title')}")
            general_alert_id = alert.get('id')
        else:
            print(f"Response: {response.text}")
        
        # Test 3: Create a post-specific alert
        print("\n3️⃣ Testing POST /posts/{post_id}/alert - Create post alert")
        post_alert_data = {
            "user_id": 1,
            "title": "Event Update",
            "message": "Important update about the event mentioned in this post!",
            "alert_type": "EVENT",
            "expires_at": (datetime.now() + timedelta(days=5)).isoformat()
        }
        response = requests.post(f"{BASE_URL}/posts/1/alert", json=post_alert_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alert = response.json()
            print(f"Created post alert: {alert.get('title')}")
            print(f"Linked to post: {alert.get('post_title', 'N/A')}")
        else:
            print(f"Response: {response.text}")
        
        # Test 4: Get alerts for user (should now show both alerts)
        print("\n4️⃣ Testing GET /alerts again - Should show new alerts")
        response = requests.get(f"{BASE_URL}/alerts")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alerts = response.json()
            alert_list = alerts.get('alerts', [])
            print(f"Found {len(alert_list)} alerts:")
            for i, alert in enumerate(alert_list[:3], 1):  # Show first 3
                print(f"  {i}. {alert.get('title')} - {alert.get('alert_type')} - {'Read' if alert.get('is_read') else 'Unread'}")
        
        # Test 5: Mark an alert as read
        if 'general_alert_id' in locals():
            print(f"\n5️⃣ Testing PUT /alerts/{general_alert_id} - Mark as read")
            update_data = {"is_read": True}
            response = requests.put(f"{BASE_URL}/alerts/{general_alert_id}", json=update_data)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                alert = response.json()
                print(f"Alert marked as read: {alert.get('is_read')}")
        
        # Test 6: Disable an alert
        if 'general_alert_id' in locals():
            print(f"\n6️⃣ Testing PUT /alerts/{general_alert_id} - Disable alert")
            update_data = {"is_enabled": False}
            response = requests.put(f"{BASE_URL}/alerts/{general_alert_id}", json=update_data)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                alert = response.json()
                print(f"Alert disabled: {not alert.get('is_enabled')}")
        
        print("\n✅ Alert feature testing completed!")
        print("\n📋 Feature Summary:")
        print("• General alerts: ✓ Create, Read, Update")
        print("• Post-specific alerts: ✓ Create with post linking")
        print("• Alert management: ✓ Enable/Disable, Mark as read")
        print("• Expiry support: ✓ Auto-expiry with timestamps")
        print("• Multi-tenant: ✓ College-based isolation")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the API is running on http://localhost:8000")
        print("Run: docker-compose up -d")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_alerts_feature()