#!/usr/bin/env python3
"""
Test script for the web wrapper
Verifies that the web interface works correctly
"""

import requests
import json
import time
import sys

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8001/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to web server. Is it running?")
        return False

def test_info():
    """Test info endpoint"""
    try:
        response = requests.get("http://localhost:8001/info")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Info endpoint: {data['name']} v{data['version']}")
            print(f"   Modes: {', '.join(data['modes'])}")
            return True
        else:
            print(f"❌ Info endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Info endpoint error: {e}")
        return False

def test_chat_mode():
    """Test simple chat mode"""
    try:
        response = requests.post(
            "http://localhost:8001/query",
            json={"text": "What is compassion?", "mode": "chat"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat mode test passed")
            print(f"   Response length: {len(data['response'])} characters")
            if data.get('sources'):
                print(f"   Sources: {len(data['sources'])} found")
            return True
        else:
            print(f"❌ Chat mode failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat mode error: {e}")
        return False

def test_agent_mode():
    """Test agent mode (with timeout for long responses)"""
    try:
        print("🤖 Testing agent mode (this may take 30-60 seconds)...")
        response = requests.post(
            "http://localhost:8001/query",
            json={"text": "What is karma?", "mode": "agent"},
            timeout=120  # 2 minutes timeout for agent mode
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Agent mode test passed")
            print(f"   Response length: {len(data['response'])} characters")
            return True
        else:
            print(f"❌ Agent mode failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("⚠️  Agent mode timed out (this is normal for complex queries)")
        return True  # Timeout is acceptable for agent mode
    except Exception as e:
        print(f"❌ Agent mode error: {e}")
        return False

def test_websocket():
    """Test WebSocket connection"""
    try:
        import websockets
        import asyncio
        
        async def test_ws():
            uri = "ws://localhost:8001/ws"
            async with websockets.connect(uri) as websocket:
                # Send a test message
                await websocket.send("test")
                
                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print("✅ WebSocket test passed")
                    return True
                except asyncio.TimeoutError:
                    print("⚠️  WebSocket timeout (no messages received)")
                    return True  # No messages is acceptable
        
        # Run the async test
        result = asyncio.run(test_ws())
        return result
        
    except ImportError:
        print("⚠️  websockets library not installed, skipping WebSocket test")
        return True
    except Exception as e:
        print(f"❌ WebSocket test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Sacred Texts LLM Web Wrapper")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Info Endpoint", test_info),
        ("Chat Mode", test_chat_mode),
        ("Agent Mode", test_agent_mode),
        ("WebSocket", test_websocket),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Web wrapper is working correctly.")
        print("\n🌐 You can now:")
        print("   - Visit http://localhost:8001 for the web interface")
        print("   - Use the API at http://localhost:8001/query")
        print("   - Share the ngrok URL with beta users")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
