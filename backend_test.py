#!/usr/bin/env python3
"""
$DEEPOTUS Backend API Testing - Phase 6 Features
Tests all endpoints including new Phase 6 features:
1. Admin UI for blacklist (view/unblock/manual add)
2. Welcome email via Resend API on whitelist registration (bilingual FR/EN template with hero image)
3. Pagination on admin whitelist + chat-logs tables (25 per page)
4. Public read-only stats dashboard at /stats with counters + evolution chart and NO PII
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
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None
        self.admin_token = None
        self.test_email_verified = "olistruss639@gmail.com"  # Verified Resend email
        self.test_email_unverified = f"test_{int(time.time())}@example.com"  # Should fail email but succeed registration

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Dict[Any, Any] = None, params: Dict[str, str] = None, headers: Dict[str, str] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
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
            "",
            200
        )
        return success

    def test_chat_fr(self):
        """Test chat endpoint in French"""
        success, response = self.run_test(
            "Chat in French",
            "POST",
            "chat",
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
            "chat",
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
            "prophecy",
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
            "prophecy",
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
            "prophecy",
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
            "whitelist",
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
            "whitelist",
            200,
            data={"email": test_email, "lang": "en"}
        )
        
        if not success1:
            return False
            
        # Second submission (should be idempotent)
        success2, response2 = self.run_test(
            "Whitelist (duplicate - idempotent)",
            "POST",
            "whitelist",
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
            "whitelist",
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
            "stats",
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
            "admin/login",
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
            "admin/login",
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
            "admin/whitelist",
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
            "admin/whitelist",
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
            "admin/chat-logs",
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
            "admin/chat-logs",
            401
        )
        return success

    def test_admin_login_jwt(self):
        """Test admin login returns JWT token"""
        print("\n🔐 Testing Admin JWT Login...")
        
        success, response_data = self.run_test(
            "Admin login with correct password",
            "POST",
            "admin/login",
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
            "admin/whitelist",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        # Test legacy X-Admin-Token header
        success2, _ = self.run_test(
            "Admin whitelist with X-Admin-Token",
            "GET", 
            "admin/whitelist",
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
            "admin/evolution",
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
            "admin/evolution",
            200,
            params={"days": "7"},
            headers=auth_headers
        )
        
        # Test days parameter clamping
        success3, _ = self.run_test(
            "Evolution API - 90 days",
            "GET", 
            "admin/evolution",
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

    def test_public_stats_api(self):
        """Test public stats API - Phase 6 feature"""
        print("\n🔍 Testing Public Stats API (Phase 6)...")
        
        # Test default public stats
        success1, data1 = self.run_test(
            "Public Stats (default)",
            "GET",
            "public/stats",
            200
        )
        
        if success1:
            # Verify required fields
            required_fields = ['whitelist_count', 'chat_messages', 'prophecies_served', 
                             'launch_timestamp', 'generated_at', 'series_days', 'series']
            missing_fields = [f for f in required_fields if f not in data1]
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
                success1 = False
            else:
                print(f"   ✅ All required fields present")
            
            # Verify no PII leakage
            data_str = str(data1).lower()
            if '@' in data_str or 'email' in data_str:
                print(f"   ❌ Potential PII leak detected in public stats")
                success1 = False
            else:
                print(f"   ✅ No PII detected in public stats")
        
        # Test with different days parameter (should be clamped 1-90)
        success2, data2 = self.run_test(
            "Public Stats (days=7)",
            "GET",
            "public/stats?days=7",
            200
        )
        
        success3, data3 = self.run_test(
            "Public Stats (days=100, should clamp to 90)",
            "GET",
            "public/stats?days=100",
            200
        )
        
        if success3 and data3.get('series_days') != 90:
            print(f"   ❌ Days not properly clamped: expected 90, got {data3.get('series_days')}")
            success3 = False
        elif success3:
            print(f"   ✅ Days properly clamped to 90")
        
        return success1 and success2 and success3

    def test_admin_pagination_apis(self):
        """Test admin pagination APIs - Phase 6 feature"""
        print("\n🔍 Testing Admin Pagination APIs (Phase 6)...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test whitelist pagination
        success1, data1 = self.run_test(
            "Admin Whitelist Pagination (default)",
            "GET",
            "admin/whitelist",
            200,
            headers=auth_headers
        )
        
        if success1:
            required_fields = ['items', 'total', 'limit', 'skip']
            missing_fields = [f for f in required_fields if f not in data1]
            if missing_fields:
                print(f"   ❌ Missing pagination fields in whitelist: {missing_fields}")
                success1 = False
            else:
                print(f"   ✅ Whitelist pagination structure valid")
        
        # Test with specific pagination parameters
        success2, data2 = self.run_test(
            "Admin Whitelist Pagination (limit=5, skip=0)",
            "GET",
            "admin/whitelist?limit=5&skip=0",
            200,
            headers=auth_headers
        )
        
        if success2:
            if data2.get('limit') != 5 or data2.get('skip') != 0:
                print(f"   ❌ Pagination parameters not respected: limit={data2.get('limit')}, skip={data2.get('skip')}")
                success2 = False
            else:
                print(f"   ✅ Whitelist pagination parameters respected")
        
        # Test chat-logs pagination
        success3, data3 = self.run_test(
            "Admin Chat-logs Pagination",
            "GET",
            "admin/chat-logs?limit=5&skip=0",
            200,
            headers=auth_headers
        )
        
        if success3:
            required_fields = ['items', 'total', 'limit', 'skip']
            missing_fields = [f for f in required_fields if f not in data3]
            if missing_fields:
                print(f"   ❌ Missing pagination fields in chat-logs: {missing_fields}")
                success3 = False
            else:
                print(f"   ✅ Chat-logs pagination structure valid")
        
        return success1 and success2 and success3

    def test_blacklist_crud_apis(self):
        """Test blacklist CRUD operations - Phase 6 feature"""
        print("\n🔍 Testing Blacklist CRUD APIs (Phase 6)...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        test_email = f"blacklist_test_{int(time.time())}@example.com"
        
        # Test GET blacklist
        success1, data1 = self.run_test(
            "Admin Blacklist List",
            "GET",
            "admin/blacklist",
            200,
            headers=auth_headers
        )
        
        if success1:
            required_fields = ['items', 'total']
            missing_fields = [f for f in required_fields if f not in data1]
            if missing_fields:
                print(f"   ❌ Missing fields in blacklist response: {missing_fields}")
                success1 = False
            else:
                print(f"   ✅ Blacklist list structure valid")
        
        # Test POST blacklist (add email)
        success2, response2 = self.run_test(
            "Admin Blacklist Add",
            "POST",
            "admin/blacklist",
            200,
            data={"email": test_email, "reason": "test blacklist"},
            headers=auth_headers
        )
        
        if success2:
            print(f"   ✅ Email {test_email} added to blacklist")
        
        # Verify email was blacklisted
        success3, data3 = self.run_test(
            "Admin Blacklist List (after add)",
            "GET",
            "admin/blacklist",
            200,
            headers=auth_headers
        )
        
        entry_id = None
        if success3:
            blacklisted_emails = [item.get('email') for item in data3.get('items', [])]
            if test_email not in blacklisted_emails:
                print(f"   ❌ Email {test_email} not found in blacklist after adding")
                success3 = False
            else:
                print(f"   ✅ Email {test_email} found in blacklist")
                # Find the entry ID for deletion
                blacklist_entry = next((item for item in data3.get('items', []) if item.get('email') == test_email), None)
                if blacklist_entry:
                    entry_id = blacklist_entry.get('id')
        
        # Test DELETE blacklist (unblock)
        success4 = False
        if entry_id:
            success4, response4 = self.run_test(
                "Admin Blacklist Remove",
                "DELETE",
                f"admin/blacklist/{entry_id}",
                200,
                headers=auth_headers
            )
            
            if success4:
                print(f"   ✅ Email {test_email} removed from blacklist")
        
        # Test invalid email format
        success5, response5 = self.run_test(
            "Admin Blacklist Add (invalid email)",
            "POST",
            "admin/blacklist",
            422,  # Should return validation error
            data={"email": "invalid-email", "reason": "test"},
            headers=auth_headers
        )
        
        if success5:
            print(f"   ✅ Invalid email format properly rejected")
        
        return success1 and success2 and success3 and success4 and success5

    def test_email_functionality(self):
        """Test welcome email functionality - Phase 6 feature"""
        print("\n🔍 Testing Email Functionality (Phase 6)...")
        
        # Test with verified email (should succeed)
        success1, response1 = self.run_test(
            "Whitelist Registration (verified email)",
            "POST",
            "whitelist",
            200,
            data={"email": self.test_email_verified, "lang": "en"}
        )
        
        if success1:
            entry_id = response1.get('id')
            if not entry_id:
                print(f"   ❌ No entry ID returned for whitelist registration")
                success1 = False
            else:
                print(f"   ✅ Whitelist registration successful for verified email")
                
                # Wait for background email task
                print("   ⏳ Waiting 5 seconds for email processing...")
                time.sleep(5)
                
                # Check email status via admin API
                if self.admin_token:
                    auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
                    success_check, data_check = self.run_test(
                        "Check Email Status (verified)",
                        "GET",
                        "admin/whitelist",
                        200,
                        headers=auth_headers
                    )
                    
                    if success_check:
                        # Find our entry
                        our_entry = None
                        for item in data_check.get('items', []):
                            if item.get('email') == self.test_email_verified:
                                our_entry = item
                                break
                        
                        if our_entry:
                            email_sent = our_entry.get('email_sent', False)
                            print(f"   📧 Email sent status for {self.test_email_verified}: {email_sent}")
                            if email_sent:
                                print(f"   ✅ Email successfully sent to verified address")
                            else:
                                print(f"   ⚠️  Email not sent yet (may still be processing)")
        
        # Test with unverified email (registration should succeed, email should fail gracefully)
        success2, response2 = self.run_test(
            "Whitelist Registration (unverified email)",
            "POST",
            "whitelist",
            200,
            data={"email": self.test_email_unverified, "lang": "en"}
        )
        
        if success2:
            print(f"   ✅ Registration succeeded for unverified email (as expected)")
            
            # Wait and check email status
            time.sleep(3)
            
            if self.admin_token:
                auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
                success_check2, data_check2 = self.run_test(
                    "Check Email Status (unverified)",
                    "GET",
                    "admin/whitelist",
                    200,
                    headers=auth_headers
                )
                
                if success_check2:
                    # Find our entry
                    our_entry = None
                    for item in data_check2.get('items', []):
                        if item.get('email') == self.test_email_unverified:
                            our_entry = item
                            break
                    
                    if our_entry:
                        email_sent = our_entry.get('email_sent', False)
                        print(f"   📧 Email sent status for {self.test_email_unverified}: {email_sent}")
                        if not email_sent:
                            print(f"   ✅ Email correctly failed for unverified address (expected)")
                        else:
                            print(f"   ⚠️  Email unexpectedly succeeded for unverified address")
        
        return success1 and success2

    def test_regression_after_unblock(self):
        """Test that after unblock, email can register again - Phase 6 regression test"""
        print("\n🔍 Testing Regression: After unblock, email can register again...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        test_email = f"regression_test_{int(time.time())}@example.com"
        
        # 1. Add email to blacklist
        success1, _ = self.run_test(
            "Add email to blacklist",
            "POST",
            "admin/blacklist",
            200,
            data={"email": test_email, "reason": "regression test"},
            headers=auth_headers
        )
        
        if not success1:
            return False
        
        # 2. Try to register (should fail)
        success2, _ = self.run_test(
            "Try to register blacklisted email",
            "POST",
            "whitelist",
            403,  # Should be forbidden
            data={"email": test_email, "lang": "en"}
        )
        
        if success2:
            print(f"   ✅ Blacklisted email registration correctly blocked")
        
        # 3. Find and unblock the email
        success3, data3 = self.run_test(
            "Get blacklist to find entry",
            "GET",
            "admin/blacklist",
            200,
            headers=auth_headers
        )
        
        entry_id = None
        if success3:
            blacklist_entry = next((item for item in data3.get('items', []) if item.get('email') == test_email), None)
            if blacklist_entry:
                entry_id = blacklist_entry.get('id')
        
        success4 = False
        if entry_id:
            success4, _ = self.run_test(
                "Unblock email",
                "DELETE",
                f"admin/blacklist/{entry_id}",
                200,
                headers=auth_headers
            )
            
            if success4:
                print(f"   ✅ Email unblocked successfully")
        
        # 4. Try to register again (should succeed)
        success5, _ = self.run_test(
            "Try to register after unblock",
            "POST",
            "whitelist",
            200,  # Should succeed now
            data={"email": test_email, "lang": "en"}
        )
        
        if success5:
            print(f"   ✅ Email can register again after unblock (regression test passed)")
        
        return success1 and success2 and success3 and success4 and success5

    def run_all_tests(self):
        """Run all backend API tests - Phase 6 Features"""
        print("=" * 60)
        print("🚀 DEEPOTUS Backend API Testing - Phase 6 Features")
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
            
            # Phase 6 new features
            self.test_public_stats_api,
            self.test_admin_pagination_apis,
            self.test_blacklist_crud_apis,
            self.test_email_functionality,
            self.test_regression_after_unblock,
            
            # Phase 5 features - JWT and rate limiting
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