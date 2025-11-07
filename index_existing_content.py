#!/usr/bin/env python3
"""
Script to index all existing content for AI search.
This should be run after setting up the AI features to index existing files and posts.
"""

import requests
import json
import sys
from getpass import getpass

def get_auth_token(base_url: str, username: str, password: str) -> str:
    """Get authentication token"""
    try:
        response = requests.post(
            f"{base_url}/auth/login",
            data={
                "username": username,
                "password": password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ Authentication failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return None

def trigger_indexing(base_url: str, token: str) -> bool:
    """Trigger indexing of all existing content"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Index all content (files, posts, and college info)
        response = requests.post(
            f"{base_url}/ai/index",
            headers=headers,
            json={"content_type": "all"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Indexing started: {data['message']}")
            print(f"📊 Tasks created: {data['tasks_created']}")
            return True
        else:
            print(f"❌ Indexing failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during indexing: {e}")
        return False

def check_ai_stats(base_url: str, token: str):
    """Check AI system statistics"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/ai/stats", headers=headers)
        
        if response.status_code == 200:
            stats = response.json()
            print("\n📊 AI System Statistics:")
            print(f"  • Vector database documents: {stats['vector_database']['total_documents']}")
            print(f"  • Vector database size: {stats['vector_database']['total_size_mb']:.2f} MB")
            print(f"  • Indexed files: {stats['indexing']['indexed_files']}")
            print(f"  • Pending files: {stats['indexing']['pending_files']}")
            print(f"  • Failed files: {stats['indexing']['failed_files']}")
            print(f"  • Total conversations: {stats['conversations']['total_college_conversations']}")
        else:
            print(f"❌ Could not get stats: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

def test_ai_search(base_url: str, token: str):
    """Test AI search functionality"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test search
        response = requests.post(
            f"{base_url}/ai/search",
            headers=headers,
            json={
                "query": "computer science",
                "limit": 3
            }
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"\n🔍 Search test results ({len(results)} found):")
            for i, result in enumerate(results[:3], 1):
                metadata = result['metadata']
                title = metadata.get('title') or metadata.get('filename', 'Unknown')
                print(f"  {i}. {title} (similarity: {result['similarity']:.2f})")
        else:
            print(f"❌ Search test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during search test: {e}")

def main():
    print("🤖 College AI Content Indexer")
    print("=" * 50)
    
    # Configuration
    base_url = "http://localhost:8000"
    
    # Get credentials
    print("\n📝 Please provide your login credentials:")
    username = input("Username: ")
    password = getpass("Password: ")
    
    # Authenticate
    print("\n🔑 Authenticating...")
    token = get_auth_token(base_url, username, password)
    
    if not token:
        print("❌ Authentication failed. Please check your credentials.")
        sys.exit(1)
    
    print("✅ Authentication successful!")
    
    # Check current stats
    print("\n📊 Checking current AI statistics...")
    check_ai_stats(base_url, token)
    
    # Ask user if they want to proceed with indexing
    print("\n❓ Do you want to index all existing content? This will:")
    print("   • Process all uploaded files (PDF, DOCX, TXT, etc.)")
    print("   • Index all posts and announcements")
    print("   • Create college information index")
    print("   • This may take a few minutes and use OpenAI API credits")
    
    proceed = input("\nProceed with indexing? (y/N): ").lower().strip()
    
    if proceed != 'y':
        print("👋 Indexing cancelled. You can run this script again later.")
        sys.exit(0)
    
    # Trigger indexing
    print("\n🚀 Starting content indexing...")
    success = trigger_indexing(base_url, token)
    
    if success:
        print("\n⏳ Indexing is now running in the background.")
        print("   You can check progress by visiting: http://localhost:8000/ai/stats")
        
        # Wait a moment and check stats again
        import time
        print("\n⏱️  Waiting 10 seconds for initial processing...")
        time.sleep(10)
        
        print("\n📊 Updated statistics:")
        check_ai_stats(base_url, token)
        
        print("\n🧪 Testing search functionality...")
        test_ai_search(base_url, token)
        
        print("\n🎉 Setup complete! You can now:")
        print("   • Visit http://localhost:8000/docs to see AI endpoints")
        print("   • Use /ai/ask to chat with your college AI assistant")
        print("   • Use /ai/search for intelligent content search")
        print("   • Check /ai/stats for system status")
        
    else:
        print("❌ Indexing setup failed. Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()