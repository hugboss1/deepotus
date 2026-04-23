#!/usr/bin/env python3
"""
DEEPOTUS Backend API Testing - Access Card System
Testing Level 2 Access Card system: request, verify, status, image, email flow, regression tests
"""

import requests
import json
import time
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

# Use public endpoint from .env
BASE_URL = "https://prophet-ai-memecoin.preview.emergentagent.com/api"
ADMIN_PASSWORD = "deepotus2026"

class AccessCardAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.admin_jti = None
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []
        self.test_email = f"qa+level2test{int(time.time())}@example.com"
        self.test_accreditation = None
        self.test_session_token = None
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED {details}")
        else:
            print(f"❌ {test_name}: FAILED {details}")
            self.errors.append(f"{test_name}: {details}")
    
    def make_request(self, method: str, endpoint: str, data=None, headers=None, expected_status=200, response_type="json"):
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
            
            if response.status_code == expected_status:
                if response_type == "json":
                    return True, response.json() if response.text else {}
                elif response_type == "text":
                    return True, response.text
                elif response_type == "raw":
                    return True, response
                else:
                    return True, response
            else:
                return False, {"error": f"Status {response.status_code}: {response.text[:200]}"}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    def admin_login(self):
        """Login as admin"""
        data = {"password": ADMIN_PASSWORD}
        success, response = self.make_request("POST", "admin/login", data)
        if success and "token" in response:
            self.admin_token = response["token"]
            self.admin_jti = response.get("jti")
            return True
        return False
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}

    def test_access_card_request_basic(self):
        """Test POST /api/access-card/request with basic email"""
        data = {"email": self.test_email}
        success, response = self.make_request("POST", "access-card/request", data)
        
        if success:
            # Check required fields
            required_fields = ['ok', 'email', 'accreditation_number', 'display_name', 'message']
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                # Check accreditation number format: DS-02-XXXX-XXXX-XX
                accred_pattern = r'^DS-02-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{2}$'
                accred = response.get('accreditation_number', '')
                
                if re.match(accred_pattern, accred):
                    if response.get('ok') == True:
                        self.test_accreditation = accred
                        self.log_result("Access Card Request Basic", True, 
                                      f"Accred: {accred}, Display: {response.get('display_name')}")
                        return True
                    else:
                        self.log_result("Access Card Request Basic", False, "ok field is not True")
                else:
                    self.log_result("Access Card Request Basic", False, f"Invalid accreditation format: {accred}")
            else:
                self.log_result("Access Card Request Basic", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Access Card Request Basic", False, f"Request failed: {response}")
        return False

    def test_access_card_request_with_display_name(self):
        """Test POST /api/access-card/request with custom display_name"""
        test_email = f"qa+displayname{int(time.time())}@example.com"
        custom_name = "AGENT TESTER-007"
        data = {"email": test_email, "display_name": custom_name}
        success, response = self.make_request("POST", "access-card/request", data)
        
        if success:
            if response.get('ok') == True and response.get('display_name') == custom_name:
                self.log_result("Access Card Request With Display Name", True, 
                              f"Custom name: {custom_name}")
                return True
            else:
                self.log_result("Access Card Request With Display Name", False, 
                              f"Expected name: {custom_name}, got: {response.get('display_name')}")
        else:
            self.log_result("Access Card Request With Display Name", False, f"Request failed: {response}")
        return False

    def test_access_card_request_idempotency(self):
        """Test that calling /api/access-card/request twice for same email returns same accreditation"""
        if not self.test_accreditation:
            self.log_result("Access Card Request Idempotency", False, "No test accreditation from previous test")
            return False
        
        # Make second request with same email
        data = {"email": self.test_email}
        success, response = self.make_request("POST", "access-card/request", data)
        
        if success:
            if response.get('accreditation_number') == self.test_accreditation:
                self.log_result("Access Card Request Idempotency", True, 
                              f"Same accred returned: {self.test_accreditation}")
                return True
            else:
                self.log_result("Access Card Request Idempotency", False, 
                              f"Different accred: expected {self.test_accreditation}, got {response.get('accreditation_number')}")
        else:
            self.log_result("Access Card Request Idempotency", False, f"Request failed: {response}")
        return False

    def test_access_card_request_blacklisted_email(self):
        """Test POST /api/access-card/request with blacklisted email returns 403"""
        # First blacklist a test email
        blacklist_email = f"blacklisted{int(time.time())}@example.com"
        blacklist_data = {"email": blacklist_email, "reason": "test blacklist"}
        self.make_request("POST", "admin/blacklist", blacklist_data, headers=self.get_auth_headers())
        
        # Now try to request access card for blacklisted email
        data = {"email": blacklist_email}
        success, response = self.make_request("POST", "access-card/request", data, expected_status=403)
        
        if success:
            self.log_result("Access Card Request Blacklisted Email", True, "Correctly returned 403")
            return True
        else:
            self.log_result("Access Card Request Blacklisted Email", False, f"Expected 403, got: {response}")
        return False

    def test_access_card_verify_valid(self):
        """Test POST /api/access-card/verify with valid accreditation_number"""
        if not self.test_accreditation:
            self.log_result("Access Card Verify Valid", False, "No test accreditation available")
            return False
        
        data = {"accreditation_number": self.test_accreditation}
        success, response = self.make_request("POST", "access-card/verify", data)
        
        if success:
            required_fields = ['ok', 'session_token', 'expires_at']
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                if response.get('ok') == True:
                    # Check session token format (should be long hex string)
                    token = response.get('session_token', '')
                    if len(token) >= 32:
                        # Check expires_at is ~24h in future
                        try:
                            expires_str = response.get('expires_at', '')
                            expires_dt = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                            now = datetime.now(timezone.utc)
                            delta = expires_dt - now
                            
                            # Should be between 23-25 hours in future
                            if timedelta(hours=23) <= delta <= timedelta(hours=25):
                                self.test_session_token = token
                                self.log_result("Access Card Verify Valid", True, 
                                              f"Token length: {len(token)}, Expires in: {delta}")
                                return True
                            else:
                                self.log_result("Access Card Verify Valid", False, 
                                              f"Invalid expiry delta: {delta}")
                        except Exception as e:
                            self.log_result("Access Card Verify Valid", False, f"Date parse error: {e}")
                    else:
                        self.log_result("Access Card Verify Valid", False, f"Token too short: {len(token)}")
                else:
                    self.log_result("Access Card Verify Valid", False, "ok field is not True")
            else:
                self.log_result("Access Card Verify Valid", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Access Card Verify Valid", False, f"Request failed: {response}")
        return False

    def test_access_card_verify_invalid(self):
        """Test POST /api/access-card/verify with invalid accreditation_number"""
        fake_accred = "DS-02-FAKE-FAKE-XX"
        data = {"accreditation_number": fake_accred}
        success, response = self.make_request("POST", "access-card/verify", data)
        
        if success:
            if response.get('ok') == False:
                message = response.get('message', '').lower()
                if 'accreditation not recognized' in message or 'not recognized' in message:
                    self.log_result("Access Card Verify Invalid", True, f"Message: {response.get('message')}")
                    return True
                else:
                    self.log_result("Access Card Verify Invalid", False, f"Wrong error message: {response.get('message')}")
            else:
                self.log_result("Access Card Verify Invalid", False, "Should return ok:false for invalid accred")
        else:
            self.log_result("Access Card Verify Invalid", False, f"Request failed: {response}")
        return False

    def test_access_card_status_valid_token(self):
        """Test GET /api/access-card/status with valid X-Session-Token"""
        if not self.test_session_token:
            self.log_result("Access Card Status Valid Token", False, "No test session token available")
            return False
        
        headers = {"X-Session-Token": self.test_session_token}
        success, response = self.make_request("GET", "access-card/status", headers=headers)
        
        if success:
            required_fields = ['ok', 'accreditation_number', 'display_name']
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                if response.get('ok') == True:
                    if response.get('accreditation_number') == self.test_accreditation:
                        self.log_result("Access Card Status Valid Token", True, 
                                      f"Accred: {response.get('accreditation_number')}, Name: {response.get('display_name')}")
                        return True
                    else:
                        self.log_result("Access Card Status Valid Token", False, 
                                      f"Wrong accreditation returned: {response.get('accreditation_number')}")
                else:
                    self.log_result("Access Card Status Valid Token", False, "ok field is not True")
            else:
                self.log_result("Access Card Status Valid Token", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Access Card Status Valid Token", False, f"Request failed: {response}")
        return False

    def test_access_card_status_invalid_token(self):
        """Test GET /api/access-card/status with missing/invalid token"""
        # Test with no token
        success1, response1 = self.make_request("GET", "access-card/status")
        
        # Test with invalid token
        headers = {"X-Session-Token": "invalid-token-12345"}
        success2, response2 = self.make_request("GET", "access-card/status", headers=headers)
        
        both_failed_correctly = True
        
        if success1:
            if response1.get('ok') != False:
                self.log_result("Access Card Status No Token", False, f"Should return ok:false, got: {response1}")
                both_failed_correctly = False
            else:
                self.log_result("Access Card Status No Token", True, "Correctly returned ok:false")
        else:
            self.log_result("Access Card Status No Token", False, f"Request failed: {response1}")
            both_failed_correctly = False
        
        if success2:
            if response2.get('ok') != False:
                self.log_result("Access Card Status Invalid Token", False, f"Should return ok:false, got: {response2}")
                both_failed_correctly = False
            else:
                self.log_result("Access Card Status Invalid Token", True, "Correctly returned ok:false")
        else:
            self.log_result("Access Card Status Invalid Token", False, f"Request failed: {response2}")
            both_failed_correctly = False
        
        return both_failed_correctly

    def test_access_card_image_valid(self):
        """Test GET /api/access-card/image/{accreditation_number} returns PNG"""
        if not self.test_accreditation:
            self.log_result("Access Card Image Valid", False, "No test accreditation available")
            return False
        
        success, response = self.make_request("GET", f"access-card/image/{self.test_accreditation}", 
                                            response_type="raw")
        
        if success:
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'image/png' in content_type:
                # Check content length (should be > few KB for rendered image)
                content_length = len(response.content)
                if content_length > 5000:  # > 5KB suggests it's a real rendered image
                    self.log_result("Access Card Image Valid", True, 
                                  f"PNG returned, size: {content_length} bytes")
                    return True
                else:
                    self.log_result("Access Card Image Valid", False, 
                                  f"Image too small: {content_length} bytes (might be error image)")
            else:
                self.log_result("Access Card Image Valid", False, f"Wrong content type: {content_type}")
        else:
            self.log_result("Access Card Image Valid", False, f"Request failed: {response}")
        return False

    def test_access_card_image_invalid(self):
        """Test GET /api/access-card/image/{accreditation_number} with unknown accred returns 404"""
        fake_accred = "DS-02-FAKE-FAKE-XX"
        success, response = self.make_request("GET", f"access-card/image/{fake_accred}", 
                                            expected_status=404, response_type="raw")
        
        if success:
            self.log_result("Access Card Image Invalid", True, "Correctly returned 404")
            return True
        else:
            self.log_result("Access Card Image Invalid", False, f"Expected 404, got: {response}")
        return False

    def test_email_flow_verification(self):
        """Test that access card request triggers email sending"""
        # Wait a moment for email to be processed
        time.sleep(3)
        
        # Query admin email events to verify email was sent
        success, response = self.make_request("GET", "admin/email-events?limit=10", 
                                            headers=self.get_auth_headers())
        
        if success:
            events = response.get('items', [])
            
            # Look for access_card.sent or email.sent events for our test email
            relevant_events = [
                e for e in events 
                if e.get('recipient') == self.test_email.lower() or 
                   e.get('type') in ['access_card.sent', 'email.sent', 'email.delivered']
            ]
            
            if relevant_events:
                event_types = [e.get('type') for e in relevant_events]
                self.log_result("Email Flow Verification", True, 
                              f"Found {len(relevant_events)} events: {event_types}")
                return True
            else:
                self.log_result("Email Flow Verification", False, 
                              f"No email events found for {self.test_email}")
        else:
            self.log_result("Email Flow Verification", False, f"Failed to query email events: {response}")
        return False

    def test_regression_vault_state_public(self):
        """Test that public /api/vault/state still hides admin fields but shows public dex fields"""
        success, response = self.make_request("GET", "vault/state")
        
        if success:
            # Fields that should NOT be in public response
            forbidden_fields = [
                'target_combination', 'dex_token_address', 'dex_last_price_usd',
                'dex_last_h24_buys', 'dex_last_h24_sells', 'dex_last_h24_volume_usd',
                'dex_carry_tokens', 'dex_error'
            ]
            
            # Fields that SHOULD be in public response
            required_public_fields = ['dex_mode', 'dex_label', 'dex_pair_symbol']
            
            exposed_fields = [f for f in forbidden_fields if f in response]
            missing_public_fields = [f for f in required_public_fields if f not in response]
            
            if not exposed_fields and not missing_public_fields:
                self.log_result("Regression Vault State Public", True, 
                              f"Dex mode: {response.get('dex_mode')}")
                return True
            else:
                issues = []
                if exposed_fields:
                    issues.append(f"Admin fields exposed: {exposed_fields}")
                if missing_public_fields:
                    issues.append(f"Public fields missing: {missing_public_fields}")
                self.log_result("Regression Vault State Public", False, "; ".join(issues))
        else:
            self.log_result("Regression Vault State Public", False, f"Request failed: {response}")
        return False

    def test_regression_existing_endpoints(self):
        """Test that existing endpoints still work"""
        endpoints_to_test = [
            ("POST", "whitelist", {"email": f"regression-test-{int(time.time())}@example.com"}, 200),
            ("GET", "prophecy", None, 200),
            ("GET", "stats", None, 200),
            ("GET", "public/stats", None, 200),
            ("GET", "admin/whitelist", None, 200, True),  # Requires auth
            ("GET", "admin/chat-logs", None, 200, True),  # Requires auth
        ]
        
        all_working = True
        
        for test_data in endpoints_to_test:
            if len(test_data) == 5:
                method, endpoint, data, expected_status, requires_auth = test_data
            else:
                method, endpoint, data, expected_status = test_data
                requires_auth = False
            
            headers = self.get_auth_headers() if requires_auth else {}
            
            success, response = self.make_request(method, endpoint, data, headers=headers, 
                                                expected_status=expected_status)
            
            if success:
                self.log_result(f"Regression {method} {endpoint}", True, f"Status {expected_status}")
            else:
                self.log_result(f"Regression {method} {endpoint}", False, f"Expected {expected_status}, got error")
                all_working = False
        
        return all_working

    def run_all_tests(self):
        """Run all Access Card system tests"""
        print("🚀 Starting DEEPOTUS Access Card System Testing...")
        print(f"Testing against: {self.base_url}")
        print(f"Test email: {self.test_email}")
        print("=" * 60)
        
        # Initial admin login
        if not self.admin_login():
            print("❌ Failed to login as admin - stopping tests")
            return False
        
        print("✅ Admin login successful")
        
        # Test access card request endpoints
        print("\n🎫 Testing Access Card Request...")
        self.test_access_card_request_basic()
        self.test_access_card_request_with_display_name()
        self.test_access_card_request_idempotency()
        self.test_access_card_request_blacklisted_email()
        
        # Test access card verify endpoints
        print("\n🔐 Testing Access Card Verify...")
        self.test_access_card_verify_valid()
        self.test_access_card_verify_invalid()
        
        # Test access card status endpoints
        print("\n📋 Testing Access Card Status...")
        self.test_access_card_status_valid_token()
        self.test_access_card_status_invalid_token()
        
        # Test access card image endpoints
        print("\n🖼️ Testing Access Card Image...")
        self.test_access_card_image_valid()
        self.test_access_card_image_invalid()
        
        # Test email flow
        print("\n📧 Testing Email Flow...")
        self.test_email_flow_verification()
        
        # Test regression
        print("\n🔄 Testing Regression...")
        self.test_regression_vault_state_public()
        self.test_regression_existing_endpoints()
        
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
    tester = AccessCardAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)