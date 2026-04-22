#!/usr/bin/env python3
"""
DEEPOTUS Backend API Testing - Phase 7 Features
Testing 5 new features: webhook, public stats, bulk import, JWT rotation, sessions
"""

import requests
import json
import time
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# Use public endpoint from .env
BASE_URL = "https://prophet-ai-memecoin.preview.emergentagent.com/api"
ADMIN_PASSWORD = "deepotus2026"

class DeepotusAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.admin_jti = None
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED {details}")
        else:
            print(f"❌ {test_name}: FAILED {details}")
            self.errors.append(f"{test_name}: {details}")
    
    def make_request(self, method: str, endpoint: str, data=None, headers=None, expected_status=200):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = headers or {}
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response.status_code == expected_status, response
        except Exception as e:
            return False, str(e)
    
    def admin_login(self, ip_header: str = None) -> bool:
        """Login as admin and get JWT token"""
        headers = {}
        if ip_header:
            headers["X-Forwarded-For"] = ip_header
            
        success, response = self.make_request(
            "POST", 
            "/admin/login", 
            {"password": ADMIN_PASSWORD},
            headers=headers
        )
        
        if success and hasattr(response, 'json'):
            try:
                data = response.json()
                self.admin_token = data.get("token")
                self.admin_jti = data.get("jti")
                return True
            except:
                pass
        return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if not self.admin_token:
            return {}
        return {"Authorization": f"Bearer {self.admin_token}"}

    def test_resend_webhook(self):
        """Test 1: Resend webhook endpoint without secret"""
        print("\n🔍 Testing Resend webhook endpoint...")
        
        # Test webhook event payload (simulating Resend webhook)
        webhook_payload = {
            "type": "email.delivered",
            "data": {
                "email_id": f"test-email-{uuid.uuid4().hex[:8]}",
                "to": ["test@example.com"],
                "subject": "Test Email"
            }
        }
        
        success, response = self.make_request(
            "POST",
            "/webhooks/resend",
            webhook_payload
        )
        
        if success and hasattr(response, 'json'):
            try:
                result = response.json()
                if result.get("ok") and "processed" in result:
                    self.log_result("Webhook Processing", True, f"Event type: {result.get('processed')}")
                else:
                    self.log_result("Webhook Processing", False, f"Unexpected response: {result}")
            except:
                self.log_result("Webhook Processing", False, "Invalid JSON response")
        else:
            self.log_result("Webhook Processing", False, f"Request failed: {response}")
    
    def test_public_stats(self):
        """Test 2: Enhanced public stats with language distribution and top sessions"""
        print("\n🔍 Testing enhanced public stats...")
        
        success, response = self.make_request("GET", "/public/stats?days=30")
        
        if success and hasattr(response, 'json'):
            try:
                data = response.json()
                
                # Check required fields
                required_fields = [
                    "whitelist_count", "chat_messages", "prophecies_served", 
                    "launch_timestamp", "generated_at", "series_days", "series",
                    "lang_distribution", "top_sessions"
                ]
                
                missing_fields = [f for f in required_fields if f not in data]
                if missing_fields:
                    self.log_result("Public Stats Structure", False, f"Missing fields: {missing_fields}")
                    return
                
                # Check language distribution structure
                lang_dist = data.get("lang_distribution", {})
                if "whitelist" not in lang_dist or "chat" not in lang_dist:
                    self.log_result("Language Distribution", False, "Missing whitelist/chat in lang_distribution")
                else:
                    # Check FR/EN counts exist
                    wl = lang_dist["whitelist"]
                    ch = lang_dist["chat"]
                    if "fr" in wl and "en" in wl and "fr" in ch and "en" in ch:
                        self.log_result("Language Distribution", True, f"WL: FR={wl['fr']}, EN={wl['en']} | Chat: FR={ch['fr']}, EN={ch['en']}")
                    else:
                        self.log_result("Language Distribution", False, "Missing FR/EN counts")
                
                # Check top sessions anonymization
                top_sessions = data.get("top_sessions", [])
                privacy_violation = False
                for session in top_sessions:
                    anon_id = session.get("anon_id", "")
                    # Check if anon_id starts with 'anon-' and is properly anonymized
                    if not anon_id.startswith("anon-"):
                        privacy_violation = True
                        break
                    # Check for any email addresses or raw session IDs (critical security check)
                    session_str = json.dumps(session)
                    if "@" in session_str or "chat-" in session_str:
                        privacy_violation = True
                        break
                
                if privacy_violation:
                    self.log_result("Top Sessions Privacy", False, "CRITICAL: Raw emails or session IDs detected!")
                else:
                    self.log_result("Top Sessions Privacy", True, f"Found {len(top_sessions)} anonymized sessions")
                
                self.log_result("Public Stats API", True, f"All required fields present")
                
            except Exception as e:
                self.log_result("Public Stats API", False, f"JSON parsing error: {e}")
        else:
            self.log_result("Public Stats API", False, f"Request failed: {response}")
    
    def test_bulk_blacklist_import(self):
        """Test 3: Bulk blacklist CSV import"""
        print("\n🔍 Testing bulk blacklist CSV import...")
        
        if not self.admin_login():
            self.log_result("Admin Login for Blacklist", False, "Could not login as admin")
            return
        
        # Test CSV import with valid data
        csv_data = """email,reason
test1@spam.com,bot
test2@spam.com,abuse
invalid-email,invalid
test1@spam.com,duplicate"""
        
        success, response = self.make_request(
            "POST",
            "/admin/blacklist/import",
            {"csv_text": csv_data, "reason": "bulk test"},
            headers=self.get_auth_headers()
        )
        
        if success and hasattr(response, 'json'):
            try:
                result = response.json()
                expected_fields = ["imported", "skipped_invalid", "skipped_existing", "total_rows", "errors"]
                
                if all(field in result for field in expected_fields):
                    imported = result["imported"]
                    skipped_invalid = result["skipped_invalid"] 
                    skipped_existing = result["skipped_existing"]
                    total_rows = result["total_rows"]
                    
                    self.log_result("Bulk Import Structure", True, f"Imported: {imported}, Invalid: {skipped_invalid}, Existing: {skipped_existing}, Total: {total_rows}")
                    
                    # Verify logic: should import 2 valid emails, skip 1 invalid, handle 1 duplicate
                    if total_rows == 4:
                        self.log_result("Bulk Import Logic", True, "Correct row count processing")
                    else:
                        self.log_result("Bulk Import Logic", False, f"Expected 4 rows, got {total_rows}")
                else:
                    self.log_result("Bulk Import Structure", False, f"Missing fields in response: {result}")
                    
            except Exception as e:
                self.log_result("Bulk Import", False, f"JSON parsing error: {e}")
        else:
            self.log_result("Bulk Import", False, f"Request failed: {response}")
    
    def test_jwt_sessions_management(self):
        """Test 4 & 5: JWT rotation and session management"""
        print("\n🔍 Testing JWT sessions and rotation...")
        
        # Login with different IPs to create multiple sessions
        session_tokens = []
        session_jtis = []
        
        for i, ip in enumerate(["192.168.1.100", "192.168.1.101", "192.168.1.102"]):
            if self.admin_login(ip_header=ip):
                session_tokens.append(self.admin_token)
                session_jtis.append(self.admin_jti)
                print(f"  Created session {i+1} from IP {ip}: {self.admin_jti[:8]}...")
        
        if len(session_tokens) < 2:
            self.log_result("Multiple Sessions Creation", False, "Could not create multiple sessions")
            return
        
        self.log_result("Multiple Sessions Creation", True, f"Created {len(session_tokens)} sessions")
        
        # Test: Get sessions list
        success, response = self.make_request(
            "GET",
            "/admin/sessions",
            headers={"Authorization": f"Bearer {session_tokens[0]}"}
        )
        
        if success and hasattr(response, 'json'):
            try:
                data = response.json()
                sessions = data.get("items", [])
                total = data.get("total", 0)
                
                # Check if we can see our sessions
                current_session_found = False
                for session in sessions:
                    if session.get("is_current"):
                        current_session_found = True
                        break
                
                if current_session_found and total >= len(session_tokens):
                    self.log_result("Sessions List", True, f"Found {total} sessions, current session marked")
                else:
                    self.log_result("Sessions List", False, f"Sessions list incomplete or current not marked")
                    
            except Exception as e:
                self.log_result("Sessions List", False, f"JSON parsing error: {e}")
        else:
            self.log_result("Sessions List", False, f"Request failed: {response}")
        
        # Test: Revoke a specific session
        if len(session_jtis) >= 2:
            target_jti = session_jtis[1]  # Revoke second session
            success, response = self.make_request(
                "DELETE",
                f"/admin/sessions/{target_jti}",
                headers={"Authorization": f"Bearer {session_tokens[0]}"}
            )
            
            if success:
                self.log_result("Session Revocation", True, f"Revoked session {target_jti[:8]}...")
                
                # Verify revoked session can't be used
                success, response = self.make_request(
                    "GET",
                    "/admin/sessions",
                    headers={"Authorization": f"Bearer {session_tokens[1]}"},
                    expected_status=401
                )
                
                if success:  # Should get 401
                    self.log_result("Revoked Session Blocked", True, "Revoked session correctly rejected")
                else:
                    self.log_result("Revoked Session Blocked", False, "Revoked session still works")
            else:
                self.log_result("Session Revocation", False, f"Could not revoke session: {response}")
        
        # Test: Revoke others
        success, response = self.make_request(
            "POST",
            "/admin/sessions/revoke-others",
            headers={"Authorization": f"Bearer {session_tokens[0]}"}
        )
        
        if success and hasattr(response, 'json'):
            try:
                result = response.json()
                if result.get("ok"):
                    self.log_result("Revoke Others", True, result.get("message", ""))
                else:
                    self.log_result("Revoke Others", False, f"Unexpected response: {result}")
            except:
                self.log_result("Revoke Others", False, "Invalid JSON response")
        else:
            self.log_result("Revoke Others", False, f"Request failed: {response}")
        
        # Test: JWT secret rotation (this will invalidate current session)
        success, response = self.make_request(
            "POST",
            "/admin/rotate-secret",
            headers={"Authorization": f"Bearer {session_tokens[0]}"}
        )
        
        if success and hasattr(response, 'json'):
            try:
                result = response.json()
                if result.get("ok") and "rotated_at" in result:
                    self.log_result("JWT Rotation", True, f"Rotated at {result.get('rotated_at')}")
                    
                    # Verify that the token is now invalid (expected behavior)
                    time.sleep(1)  # Brief pause
                    success, response = self.make_request(
                        "GET",
                        "/admin/sessions",
                        headers={"Authorization": f"Bearer {session_tokens[0]}"},
                        expected_status=401
                    )
                    
                    if success:  # Should get 401
                        self.log_result("Post-Rotation Token Invalid", True, "Token correctly invalidated after rotation")
                    else:
                        self.log_result("Post-Rotation Token Invalid", False, "Token still works after rotation")
                        
                else:
                    self.log_result("JWT Rotation", False, f"Unexpected response: {result}")
            except Exception as e:
                self.log_result("JWT Rotation", False, f"JSON parsing error: {e}")
        else:
            self.log_result("JWT Rotation", False, f"Request failed: {response}")
    
    def test_basic_functionality(self):
        """Test that basic functionality still works"""
        print("\n🔍 Testing basic functionality...")
        
        # Test whitelist endpoint
        success, response = self.make_request(
            "POST",
            "/whitelist",
            {"email": f"test-{uuid.uuid4().hex[:8]}@example.com", "lang": "en"}
        )
        
        if success:
            self.log_result("Whitelist Endpoint", True, "Basic whitelist functionality works")
        else:
            self.log_result("Whitelist Endpoint", False, f"Whitelist failed: {response}")
        
        # Test admin whitelist with email_status
        if self.admin_login():
            success, response = self.make_request(
                "GET",
                "/admin/whitelist?limit=5",
                headers=self.get_auth_headers()
            )
            
            if success and hasattr(response, 'json'):
                try:
                    data = response.json()
                    items = data.get("items", [])
                    if items and "email_status" in items[0]:
                        self.log_result("Admin Whitelist Email Status", True, "email_status field present")
                    else:
                        self.log_result("Admin Whitelist Email Status", False, "email_status field missing")
                except:
                    self.log_result("Admin Whitelist Email Status", False, "JSON parsing error")
            else:
                self.log_result("Admin Whitelist Email Status", False, f"Request failed: {response}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting DEEPOTUS Phase 7 Feature Testing...")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test all new features
        self.test_resend_webhook()
        self.test_public_stats()
        self.test_bulk_blacklist_import()
        self.test_jwt_sessions_management()
        self.test_basic_functionality()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.errors:
            print(f"\n❌ FAILED TESTS:")
            for error in self.errors:
                print(f"  • {error}")
        else:
            print(f"\n✅ ALL TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = DeepotusAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)