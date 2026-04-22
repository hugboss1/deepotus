#!/usr/bin/env python3
"""
$DEEPOTUS Backend API Testing - Phase 5 Features
Tests all endpoints including new Phase 5 features:
1. Rate-limit on /api/admin/login (5 attempts / 10min per IP, 429 response)
2. Admin auth switched to JWT (HS256, 24h TTL, Authorization: Bearer header)
3. Admin evolution chart API showing whitelist + chat growth
4. Admin can Delete whitelist entries
5. Admin can Blacklist whitelist entries
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any

class DeepotusAPITester:
    def __init__(self, base_url="https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None
        self.admin_token = None

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Dict[Any, Any] = None, params: Dict[str, str] = None, headers: Dict[str, str] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
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

    def test_admin_login_correct_password(self):
        """Test admin login with correct password"""
        success, response = self.run_test(
            "Admin login (correct password)",
            "POST",
            "api/admin/login",
            200,
            data={"password": "deepotus2026"}
        )
        if success and response:
            self.admin_token = response.get('token')
            print(f"   Token received: {self.admin_token[:20]}...")
            print(f"   Expires at: {response.get('expires_at')}")
            required_keys = ['token', 'expires_at']
            missing_keys = [key for key in required_keys if key not in response]
            if missing_keys:
                print(f"   ⚠️  Missing keys: {missing_keys}")
                return False
        return success

    def test_admin_login_wrong_password(self):
        """Test admin login with wrong password"""
        success, response = self.run_test(
            "Admin login (wrong password)",
            "POST",
            "api/admin/login",
            401,
            data={"password": "wrongpassword"}
        )
        return success

    def test_admin_whitelist_with_token(self):
        """Test admin whitelist endpoint with valid token"""
        if not self.admin_token:
            print("❌ No admin token available, skipping test")
            return False
            
        success, response = self.run_test(
            "Admin whitelist (with token)",
            "GET",
            "api/admin/whitelist",
            200,
            headers={"X-Admin-Token": self.admin_token}
        )
        if success and response:
            print(f"   Total whitelist items: {response.get('total')}")
            print(f"   Items returned: {len(response.get('items', []))}")
            required_keys = ['items', 'total']
            missing_keys = [key for key in required_keys if key not in response]
            if missing_keys:
                print(f"   ⚠️  Missing keys: {missing_keys}")
                return False
        return success

    def test_admin_whitelist_without_token(self):
        """Test admin whitelist endpoint without token"""
        success, response = self.run_test(
            "Admin whitelist (without token)",
            "GET",
            "api/admin/whitelist",
            401
        )
        return success

    def test_admin_chat_logs_with_token(self):
        """Test admin chat logs endpoint with valid token"""
        if not self.admin_token:
            print("❌ No admin token available, skipping test")
            return False
            
        success, response = self.run_test(
            "Admin chat logs (with token)",
            "GET",
            "api/admin/chat-logs",
            200,
            headers={"X-Admin-Token": self.admin_token}
        )
        if success and response:
            print(f"   Total chat logs: {response.get('total')}")
            print(f"   Items returned: {len(response.get('items', []))}")
            required_keys = ['items', 'total']
            missing_keys = [key for key in required_keys if key not in response]
            if missing_keys:
                print(f"   ⚠️  Missing keys: {missing_keys}")
                return False
        return success

    def test_admin_chat_logs_without_token(self):
        """Test admin chat logs endpoint without token"""
        success, response = self.run_test(
            "Admin chat logs (without token)",
            "GET",
            "api/admin/chat-logs",
            401
        )
        return success

    def test_admin_login_jwt(self):
        """Test admin login returns JWT token"""
        print("\n🔐 Testing Admin JWT Login...")
        
        success, response_data = self.run_test(
            "Admin login with correct password",
            "POST",
            "api/admin/login",
            200,
            data={"password": "deepotus2026"}
        )
        
        if success and response_data:
            token = response_data.get('token', '')
            if token.startswith('eyJ'):
                self.admin_token = token
                print(f"   ✅ JWT token format valid: {token[:20]}...")
                return True
            else:
                print(f"   ❌ Token doesn't start with 'eyJ': {token[:20]}")
        
        return False

    def test_rate_limiting(self):
        """Test rate limiting on admin login"""
        print("\n⏱️ Testing Rate Limiting...")
        
        # Use unique IP for rate limit testing
        test_ip = "198.51.100.123"
        headers = {"X-Forwarded-For": test_ip, "Content-Type": "application/json"}
        
        # Make 5 failed attempts
        for i in range(5):
            response = requests.post(
                f"{self.base_url}/api/admin/login",
                json={"password": "wrongpassword"},
                headers=headers,
                timeout=30
            )
            print(f"   Attempt {i+1}: Status {response.status_code}")
        
        # 6th attempt should be rate limited
        response = requests.post(
            f"{self.base_url}/api/admin/login", 
            json={"password": "wrongpassword"},
            headers=headers,
            timeout=30
        )
        
        success = response.status_code == 429
        if success:
            print(f"✅ Rate limiting works - Status: {response.status_code}")
            try:
                data = response.json()
                if "Too many login attempts" in data.get('detail', ''):
                    print("   ✅ Correct error message")
                else:
                    print(f"   ⚠️ Unexpected message: {data.get('detail', '')}")
            except:
                pass
        else:
            print(f"❌ Rate limiting failed - Status: {response.status_code}")
        
        return success

    def test_jwt_auth_headers(self):
        """Test JWT authentication with both Bearer and legacy headers"""
        if not self.admin_token:
            print("❌ JWT auth test skipped - No admin token available")
            return False
            
        print("\n🔑 Testing JWT Authentication Headers...")
        
        # Test Authorization: Bearer header
        success1, _ = self.run_test(
            "Admin whitelist with Bearer token",
            "GET",
            "api/admin/whitelist",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        # Test legacy X-Admin-Token header
        success2, _ = self.run_test(
            "Admin whitelist with X-Admin-Token",
            "GET", 
            "api/admin/whitelist",
            200,
            headers={"X-Admin-Token": self.admin_token}
        )
        
        return success1 and success2

    def test_evolution_api(self):
        """Test admin evolution API"""
        if not self.admin_token:
            print("❌ Evolution API test skipped - No admin token available")
            return False
            
        print("\n📈 Testing Evolution API...")
        
        auth_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test default days (30)
        success1, response_data = self.run_test(
            "Evolution API - default 30 days",
            "GET",
            "api/admin/evolution",
            200,
            headers=auth_headers
        )
        
        if success1 and response_data:
            required_fields = ['days', 'series']
            if all(field in response_data for field in required_fields):
                print("   ✅ Evolution API response structure valid")
                
                # Check series structure
                if response_data['series'] and len(response_data['series']) > 0:
                    series_item = response_data['series'][0]
                    series_fields = ['date', 'whitelist', 'chat', 'whitelist_daily', 'chat_daily']
                    if all(field in series_item for field in series_fields):
                        print("   ✅ Evolution series structure valid")
                    else:
                        print(f"   ❌ Missing fields in series: {series_item}")
                else:
                    print("   ✅ Empty series (expected for new install)")
            else:
                print(f"   ❌ Missing fields in response: {response_data}")
        
        # Test custom days parameter
        success2, _ = self.run_test(
            "Evolution API - 7 days",
            "GET",
            "api/admin/evolution",
            200,
            params={"days": "7"},
            headers=auth_headers
        )
        
        # Test days parameter clamping
        success3, _ = self.run_test(
            "Evolution API - 90 days",
            "GET", 
            "api/admin/evolution",
            200,
            params={"days": "90"},
            headers=auth_headers
        )
        
        return success1 and success2 and success3

    def test_whitelist_operations(self):
        """Test whitelist delete and blacklist operations"""
        if not self.admin_token:
            print("❌ Whitelist operations test skipped - No admin token available")
            return False
            
        print("\n📝 Testing Whitelist Operations...")
        
        auth_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # First, create a test whitelist entry
        test_email = f"test-{int(time.time())}@example.com"
        create_response = requests.post(
            f"{self.base_url}/api/whitelist",
            json={"email": test_email, "lang": "en"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if create_response.status_code != 200:
            print(f"❌ Failed to create test whitelist entry - Status: {create_response.status_code}")
            return False
        
        entry_data = create_response.json()
        entry_id = entry_data['id']
        print(f"   ✅ Created test entry {entry_id}")
        
        # Test delete operation
        delete_response = requests.delete(
            f"{self.base_url}/api/admin/whitelist/{entry_id}",
            headers=auth_headers,
            timeout=30
        )
        
        success1 = delete_response.status_code == 200
        if success1:
            print(f"   ✅ Delete operation successful")
            
            # Verify entry was deleted (should return 404)
            verify_response = requests.delete(
                f"{self.base_url}/api/admin/whitelist/{entry_id}",
                headers=auth_headers,
                timeout=30
            )
            if verify_response.status_code == 404:
                print(f"   ✅ Entry properly deleted (404 on re-delete)")
        else:
            print(f"   ❌ Delete operation failed - Status: {delete_response.status_code}")
        
        # Create another test entry for blacklist test
        test_email2 = f"blacklist-test-{int(time.time())}@example.com"
        create_response2 = requests.post(
            f"{self.base_url}/api/whitelist",
            json={"email": test_email2, "lang": "en"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        success2 = False
        success3 = False
        
        if create_response2.status_code == 200:
            entry_data2 = create_response2.json()
            entry_id2 = entry_data2['id']
            
            # Test blacklist operation
            blacklist_response = requests.post(
                f"{self.base_url}/api/admin/whitelist/{entry_id2}/blacklist",
                json={},
                headers=auth_headers,
                timeout=30
            )
            
            success2 = blacklist_response.status_code == 200
            if success2:
                print(f"   ✅ Blacklist operation successful")
                
                # Test that blacklisted email cannot re-register
                reregister_response = requests.post(
                    f"{self.base_url}/api/whitelist",
                    json={"email": test_email2, "lang": "en"},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                success3 = reregister_response.status_code == 403
                if success3:
                    print(f"   ✅ Blacklisted email re-registration blocked")
                    try:
                        data = reregister_response.json()
                        if "blacklisted" in data.get('detail', '').lower():
                            print("   ✅ Correct blacklist error message")
                    except:
                        pass
                else:
                    print(f"   ❌ Blacklisted email re-registration not blocked - Status: {reregister_response.status_code}")
            else:
                print(f"   ❌ Blacklist operation failed - Status: {blacklist_response.status_code}")
        
        return success1 and success2 and success3

    def run_all_tests(self):
        """Run all backend API tests - Phase 5 Features"""
        print("=" * 60)
        print("🚀 DEEPOTUS Backend API Testing - Phase 5 Features")
        print("=" * 60)
        
        tests = [
            # Original public endpoints
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
            
            # Phase 5 new features - JWT and rate limiting
            self.test_admin_login_jwt,
            self.test_rate_limiting,
            self.test_jwt_auth_headers,
            self.test_evolution_api,
            self.test_whitelist_operations,
            
            # Original admin endpoints (updated to use JWT)
            self.test_admin_login_correct_password,
            self.test_admin_login_wrong_password,
            self.test_admin_whitelist_with_token,
            self.test_admin_whitelist_without_token,
            self.test_admin_chat_logs_with_token,
            self.test_admin_chat_logs_without_token,
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