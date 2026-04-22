#!/usr/bin/env python3
"""
$DEEPOTUS Backend API Testing
Tests all 4 main endpoints: /api/chat, /api/prophecy, /api/whitelist, /api/stats
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class DeepotusAPITester:
    def __init__(self, base_url="https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Dict[Any, Any] = None, params: Dict[str, str] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys())}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API endpoint",
            "GET",
            "api/",
            200
        )
        return success

    def test_chat_fr(self):
        """Test chat endpoint in French"""
        success, response = self.run_test(
            "Chat in French",
            "POST",
            "api/chat",
            200,
            data={
                "message": "Que pense le Deep State de la Fed ?",
                "lang": "fr"
            }
        )
        if success and response:
            self.session_id = response.get('session_id')
            print(f"   Session ID: {self.session_id}")
            print(f"   Reply preview: {response.get('reply', '')[:100]}...")
            # Verify response structure
            required_keys = ['session_id', 'reply', 'lang']
            missing_keys = [key for key in required_keys if key not in response]
            if missing_keys:
                print(f"   ⚠️  Missing keys: {missing_keys}")
                return False
            if response.get('lang') != 'fr':
                print(f"   ⚠️  Expected lang='fr', got '{response.get('lang')}'")
                return False
        return success

    def test_chat_en(self):
        """Test chat endpoint in English"""
        success, response = self.run_test(
            "Chat in English",
            "POST",
            "api/chat",
            200,
            data={
                "message": "What does the Deep State think of the Fed?",
                "lang": "en",
                "session_id": self.session_id  # Reuse session if available
            }
        )
        if success and response:
            print(f"   Reply preview: {response.get('reply', '')[:100]}...")
            if response.get('lang') != 'en':
                print(f"   ⚠️  Expected lang='en', got '{response.get('lang')}'")
                return False
        return success

    def test_prophecy_seeded_fr(self):
        """Test prophecy endpoint with seeded data in French"""
        success, response = self.run_test(
            "Prophecy (seeded, FR)",
            "GET",
            "api/prophecy",
            200,
            params={"lang": "fr", "live": "false"}
        )
        if success and response:
            print(f"   Prophecy: {response.get('prophecy', '')[:100]}...")
            required_keys = ['prophecy', 'lang', 'generated_at']
            missing_keys = [key for key in required_keys if key not in response]
            if missing_keys:
                print(f"   ⚠️  Missing keys: {missing_keys}")
                return False
        return success

    def test_prophecy_seeded_en(self):
        """Test prophecy endpoint with seeded data in English"""
        success, response = self.run_test(
            "Prophecy (seeded, EN)",
            "GET",
            "api/prophecy",
            200,
            params={"lang": "en", "live": "false"}
        )
        if success and response:
            print(f"   Prophecy: {response.get('prophecy', '')[:100]}...")
        return success

    def test_prophecy_live_fr(self):
        """Test prophecy endpoint with live LLM in French"""
        success, response = self.run_test(
            "Prophecy (live LLM, FR)",
            "GET",
            "api/prophecy",
            200,
            params={"lang": "fr", "live": "true"}
        )
        if success and response:
            print(f"   Live prophecy: {response.get('prophecy', '')[:100]}...")
        return success

    def test_whitelist_valid_email(self):
        """Test whitelist with valid email"""
        test_email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"
        success, response = self.run_test(
            "Whitelist (valid email)",
            "POST",
            "api/whitelist",
            200,
            data={
                "email": test_email,
                "lang": "fr"
            }
        )
        if success and response:
            print(f"   Position: {response.get('position')}")
            print(f"   Email: {response.get('email')}")
            required_keys = ['id', 'email', 'position', 'created_at']
            missing_keys = [key for key in required_keys if key not in response]
            if missing_keys:
                print(f"   ⚠️  Missing keys: {missing_keys}")
                return False
        return success

    def test_whitelist_duplicate_email(self):
        """Test whitelist idempotency with duplicate email"""
        test_email = f"duplicate_{datetime.now().strftime('%H%M%S')}@example.com"
        
        # First submission
        success1, response1 = self.run_test(
            "Whitelist (first submission)",
            "POST",
            "api/whitelist",
            200,
            data={"email": test_email, "lang": "en"}
        )
        
        if not success1:
            return False
            
        # Second submission (should be idempotent)
        success2, response2 = self.run_test(
            "Whitelist (duplicate - idempotent)",
            "POST",
            "api/whitelist",
            200,
            data={"email": test_email, "lang": "en"}
        )
        
        if success2 and response1 and response2:
            if response1.get('id') != response2.get('id'):
                print(f"   ⚠️  Idempotency failed: different IDs")
                return False
            if response1.get('position') != response2.get('position'):
                print(f"   ⚠️  Idempotency failed: different positions")
                return False
            print(f"   ✓ Idempotency verified - same ID and position")
        
        return success2

    def test_whitelist_invalid_email(self):
        """Test whitelist with invalid email"""
        success, response = self.run_test(
            "Whitelist (invalid email)",
            "POST",
            "api/whitelist",
            422,  # Expecting validation error
            data={
                "email": "not-an-email",
                "lang": "fr"
            }
        )
        return success

    def test_stats(self):
        """Test stats endpoint"""
        success, response = self.run_test(
            "Stats endpoint",
            "GET",
            "api/stats",
            200
        )
        if success and response:
            print(f"   Whitelist count: {response.get('whitelist_count')}")
            print(f"   Prophecies served: {response.get('prophecies_served')}")
            print(f"   Chat messages: {response.get('chat_messages')}")
            print(f"   Launch timestamp: {response.get('launch_timestamp')}")
            
            required_keys = ['whitelist_count', 'prophecies_served', 'chat_messages', 'launch_timestamp']
            missing_keys = [key for key in required_keys if key not in response]
            if missing_keys:
                print(f"   ⚠️  Missing keys: {missing_keys}")
                return False
                
            # Verify launch_timestamp is ISO format
            try:
                datetime.fromisoformat(response.get('launch_timestamp', '').replace('Z', '+00:00'))
                print(f"   ✓ Launch timestamp is valid ISO format")
            except:
                print(f"   ⚠️  Launch timestamp is not valid ISO format")
                return False
        return success

    def run_all_tests(self):
        """Run all backend API tests"""
        print("=" * 60)
        print("🚀 DEEPOTUS Backend API Testing")
        print("=" * 60)
        
        tests = [
            self.test_root_endpoint,
            self.test_chat_fr,
            self.test_chat_en,
            self.test_prophecy_seeded_fr,
            self.test_prophecy_seeded_en,
            self.test_prophecy_live_fr,
            self.test_whitelist_valid_email,
            self.test_whitelist_duplicate_email,
            self.test_whitelist_invalid_email,
            self.test_stats,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print("=" * 60)
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = DeepotusAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())