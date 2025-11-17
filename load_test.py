#!/usr/bin/env python3
"""
Load Testing Script for College Community API
Authenticates and tests GET /posts endpoint with 100+ RPS
"""
import asyncio
import aiohttp
import time
from collections import defaultdict

# Configuration
BASE_URL = "http://195.35.20.155:8000"
USERNAME = "arjun_cs"
PASSWORD = "password123"
REQUESTS_PER_SECOND = 100
DURATION_SECONDS = 10

# Statistics
stats = defaultdict(lambda: {"success": 0, "failed": 0, "total_time": 0, "response_times": []})


async def get_auth_token(session):
    """Login and get JWT token"""
    login_url = f"{BASE_URL}/login"
    data = aiohttp.FormData()
    data.add_field('username', USERNAME)
    data.add_field('password', PASSWORD)
    
    try:
        async with session.post(login_url, data=data) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("access_token")
            else:
                print(f"❌ Login failed with status: {response.status}")
                text = await response.text()
                print(f"Response: {text}")
                return None
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return None


async def fetch_posts(session, token, endpoint_name):
    """Fetch posts with authentication"""
    url = f"{BASE_URL}/posts"
    headers = {"Authorization": f"Bearer {token}"}
    
    start = time.time()
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            await response.text()
            elapsed = time.time() - start
            
            if response.status == 200:
                stats[endpoint_name]["success"] += 1
            else:
                stats[endpoint_name]["failed"] += 1
            
            stats[endpoint_name]["total_time"] += elapsed
            stats[endpoint_name]["response_times"].append(elapsed)
            return response.status
    except Exception as e:
        elapsed = time.time() - start
        stats[endpoint_name]["failed"] += 1
        stats[endpoint_name]["total_time"] += elapsed
        return f"Error: {str(e)}"


async def run_load_test():
    """Main load test function"""
    print(f"🔐 Authenticating as {USERNAME}...")
    
    connector = aiohttp.TCPConnector(limit=200, limit_per_host=200)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Get auth token
        token = await get_auth_token(session)
        if not token:
            print("❌ Authentication failed. Exiting.")
            return
        
        print(f"✅ Authentication successful!")
        print(f"🚀 Starting load test: {REQUESTS_PER_SECOND} requests/sec for {DURATION_SECONDS} seconds")
        print(f"📊 Target: GET /posts endpoint")
        print(f"🎯 Total requests: {REQUESTS_PER_SECOND * DURATION_SECONDS}\n")
        
        # Run load test
        total_requests = REQUESTS_PER_SECOND * DURATION_SECONDS
        start_time = time.time()
        
        tasks = []
        for i in range(total_requests):
            tasks.append(fetch_posts(session, token, "GET /posts"))
            
            # Send requests in batches to maintain RPS
            if (i + 1) % REQUESTS_PER_SECOND == 0:
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
                
                # Sleep to maintain rate
                elapsed = time.time() - start_time
                expected_time = (i + 1) / REQUESTS_PER_SECOND
                if elapsed < expected_time:
                    await asyncio.sleep(expected_time - elapsed)
                
                # Progress update
                print(f"⏳ Sent {i + 1}/{total_requests} requests...")
        
        # Send remaining requests
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        # Print results
        print("\n" + "="*60)
        print("📈 LOAD TEST RESULTS")
        print("="*60)
        
        for endpoint, data in stats.items():
            total = data["success"] + data["failed"]
            avg_time = data["total_time"] / total if total > 0 else 0
            success_rate = (data["success"] / total * 100) if total > 0 else 0
            
            print(f"\n🎯 {endpoint}:")
            print(f"  ✅ Successful: {data['success']}")
            print(f"  ❌ Failed: {data['failed']}")
            print(f"  📊 Success Rate: {success_rate:.2f}%")
            print(f"  ⏱️  Avg Response Time: {avg_time*1000:.2f}ms")
            
            # Percentiles
            if data["response_times"]:
                sorted_times = sorted(data["response_times"])
                p50 = sorted_times[len(sorted_times)//2] * 1000
                p95 = sorted_times[int(len(sorted_times)*0.95)] * 1000
                p99 = sorted_times[int(len(sorted_times)*0.99)] * 1000
                
                print(f"  📊 P50: {p50:.2f}ms | P95: {p95:.2f}ms | P99: {p99:.2f}ms")
        
        total_time = end_time - start_time
        actual_rps = total_requests / total_time
        
        print(f"\n{'='*60}")
        print(f"⏱️  Total Duration: {total_time:.2f}s")
        print(f"🚀 Actual RPS: {actual_rps:.2f}")
        print(f"📦 Total Requests: {total_requests}")
        print("="*60)


if __name__ == "__main__":
    print("🧪 College Community API Load Tester")
    print("="*60)
    asyncio.run(run_load_test())
    print("\n✅ Test completed!")
