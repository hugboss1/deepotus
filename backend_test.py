#!/usr/bin/env python3
"""
DEEPOTUS Backend API Testing - Phase 8 Features
Testing 5 new features: 2FA TOTP, activity heatmap, full whitelist export, email events, cooldown blacklist
"""

import requests
import json
import time
import hashlib
import uuid
import pyotp
import csv
import io
from datetime import datetime, timezone, timedelta
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
        self.twofa_secret = None
        self.backup_codes = []
        
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
                else:
                    return True, response
            else:
                return False, {"error": f"Status {response.status_code}: {response.text[:200]}"}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    def admin_login(self, totp_code=None, backup_code=None):
        """Login as admin"""
        data = {"password": ADMIN_PASSWORD}
        if totp_code:
            data["totp_code"] = totp_code
        if backup_code:
            data["backup_code"] = backup_code
            
        success, response = self.make_request("POST", "admin/login", data)
        if success and "token" in response:
            self.admin_token = response["token"]
            self.admin_jti = response.get("jti")
            return True
        return False
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}

    def test_2fa_status_initial(self):
        """Test 2FA status endpoint - should be disabled initially"""
        success, response = self.make_request(
            "GET", "admin/2fa/status", headers=self.get_auth_headers()
        )
        
        if success:
            required_fields = ['enabled', 'setup_pending', 'backup_codes_remaining']
            if all(field in response for field in required_fields):
                self.log_result("2FA Status Initial", True, f"Status: {response}")
                return True
            else:
                self.log_result("2FA Status Initial", False, f"Missing fields: {response}")
        else:
            self.log_result("2FA Status Initial", False, f"Request failed: {response}")
        return False

    def test_2fa_setup(self):
        """Test 2FA setup endpoint"""
        success, response = self.make_request(
            "POST", "admin/2fa/setup", headers=self.get_auth_headers()
        )
        
        if success:
            required_fields = ['secret', 'otpauth_uri', 'qr_png_base64', 'backup_codes']
            if all(field in response for field in required_fields):
                self.twofa_secret = response['secret']
                self.backup_codes = response['backup_codes']
                
                # Validate otpauth_uri format
                if response['otpauth_uri'].startswith('otpauth://totp/'):
                    self.log_result("2FA Setup", True, f"Secret: {self.twofa_secret[:8]}..., Codes: {len(self.backup_codes)}")
                    return True
                else:
                    self.log_result("2FA Setup", False, f"Invalid otpauth_uri: {response['otpauth_uri']}")
            else:
                self.log_result("2FA Setup", False, f"Missing fields: {response}")
        else:
            self.log_result("2FA Setup", False, f"Request failed: {response}")
        return False

    def test_2fa_verify(self):
        """Test 2FA verification with TOTP code"""
        if not self.twofa_secret:
            self.log_result("2FA Verify", False, "No 2FA secret available")
            return False
            
        # Generate current TOTP code
        totp = pyotp.TOTP(self.twofa_secret)
        current_code = totp.now()
        
        success, response = self.make_request(
            "POST", "admin/2fa/verify", 
            data={"code": current_code}, 
            headers=self.get_auth_headers()
        )
        
        if success:
            self.log_result("2FA Verify", True, f"Code: {current_code}")
            return True
        else:
            self.log_result("2FA Verify", False, f"Verification failed: {response}")
        return False

    def test_2fa_login_flow(self):
        """Test login flow with 2FA enabled"""
        # First, try login with password only (should fail with 2FA required)
        success, response = self.make_request(
            "POST", "admin/login", 
            data={"password": ADMIN_PASSWORD}, 
            expected_status=401
        )
        
        if success:
            self.log_result("2FA Login Password Only", True, "Correctly rejected")
        else:
            self.log_result("2FA Login Password Only", False, "Should have returned 401")
            return False

        # Now try with password + TOTP code
        totp = pyotp.TOTP(self.twofa_secret)
        current_code = totp.now()
        
        success, response = self.make_request(
            "POST", "admin/login", 
            data={"password": ADMIN_PASSWORD, "totp_code": current_code}
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']  # Update token
            self.log_result("2FA Login with TOTP", True, "Login successful")
            return True
        else:
            self.log_result("2FA Login with TOTP", False, f"Login failed: {response}")
        return False

    def test_2fa_backup_code_login(self):
        """Test login with backup code"""
        if not self.backup_codes:
            self.log_result("2FA Backup Code Login", False, "No backup codes available")
            return False
            
        backup_code = self.backup_codes[0]  # Use first backup code
        
        success, response = self.make_request(
            "POST", "admin/login", 
            data={"password": ADMIN_PASSWORD, "backup_code": backup_code}
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            self.log_result("2FA Backup Code Login", True, f"Used code: {backup_code}")
            return True
        else:
            self.log_result("2FA Backup Code Login", False, f"Login failed: {response}")
        return False

    def test_2fa_disable(self):
        """Test disabling 2FA"""
        if not self.twofa_secret:
            self.log_result("2FA Disable", False, "No 2FA secret available")
            return False
            
        totp = pyotp.TOTP(self.twofa_secret)
        current_code = totp.now()
        
        success, response = self.make_request(
            "POST", "admin/2fa/disable", 
            data={"password": ADMIN_PASSWORD, "code": current_code}, 
            headers=self.get_auth_headers()
        )
        
        if success:
            self.log_result("2FA Disable", True, "2FA disabled")
            # Reset 2FA state
            self.twofa_secret = None
            self.backup_codes = []
            return True
        else:
            self.log_result("2FA Disable", False, f"Disable failed: {response}")
        return False

    def test_activity_heatmap(self):
        """Test activity heatmap in public stats"""
        success, response = self.make_request("GET", "public/stats")
        
        if success:
            if 'activity_heatmap' in response:
                heatmap = response['activity_heatmap']
                if isinstance(heatmap, list) and len(heatmap) == 7:
                    # Check if each day has 24 hours
                    valid_structure = all(
                        isinstance(day, list) and len(day) == 24 
                        for day in heatmap
                    )
                    if valid_structure:
                        # Check if all values are integers >= 0
                        valid_values = all(
                            isinstance(hour_val, int) and hour_val >= 0
                            for day in heatmap for hour_val in day
                        )
                        if valid_values:
                            self.log_result("Activity Heatmap", True, "7x24 grid with valid integer values")
                            return True
                        else:
                            self.log_result("Activity Heatmap", False, "Contains invalid values")
                    else:
                        self.log_result("Activity Heatmap", False, f"Invalid structure: {len(heatmap)} days")
                else:
                    self.log_result("Activity Heatmap", False, f"Not a 7-day array: {type(heatmap)}")
            else:
                self.log_result("Activity Heatmap", False, "Missing from public stats")
        else:
            self.log_result("Activity Heatmap", False, f"Request failed: {response}")
        return False

    def test_full_whitelist_export(self):
        """Test full whitelist CSV export"""
        success, response = self.make_request(
            "GET", "admin/whitelist/export", 
            headers=self.get_auth_headers(), 
            response_type="text"
        )
        
        if success:
            # Check if response is CSV format
            try:
                csv_reader = csv.reader(io.StringIO(response))
                rows = list(csv_reader)
                if len(rows) > 0:
                    headers = rows[0]
                    expected_headers = ['position', 'email', 'lang', 'created_at', 'email_sent', 'email_status']
                    if all(header in headers for header in expected_headers):
                        self.log_result("Full Whitelist Export", True, f"{len(rows)-1} entries exported")
                        return True
                    else:
                        self.log_result("Full Whitelist Export", False, f"Missing headers: {headers}")
                else:
                    self.log_result("Full Whitelist Export", False, "Empty CSV response")
            except Exception as e:
                self.log_result("Full Whitelist Export", False, f"CSV parse error: {e}")
        else:
            self.log_result("Full Whitelist Export", False, f"Request failed: {response}")
        return False

    def test_email_events_endpoint(self):
        """Test email events endpoint"""
        success, response = self.make_request(
            "GET", "admin/email-events", 
            headers=self.get_auth_headers()
        )
        
        if success:
            required_fields = ['items', 'total', 'limit', 'skip', 'type_counts']
            if all(field in response for field in required_fields):
                self.log_result("Email Events Basic", True, f"Total: {response['total']}")
                
                # Test with type filter
                success2, response2 = self.make_request(
                    "GET", "admin/email-events?type=email.delivered", 
                    headers=self.get_auth_headers()
                )
                
                if success2:
                    self.log_result("Email Events Type Filter", True, "Filter working")
                    
                    # Test with recipient filter
                    success3, response3 = self.make_request(
                        "GET", "admin/email-events?recipient=test@example.com", 
                        headers=self.get_auth_headers()
                    )
                    
                    if success3:
                        self.log_result("Email Events Recipient Filter", True, "Filter working")
                        return True
                    else:
                        self.log_result("Email Events Recipient Filter", False, f"Filter failed: {response3}")
                else:
                    self.log_result("Email Events Type Filter", False, f"Filter failed: {response2}")
            else:
                self.log_result("Email Events Basic", False, f"Missing fields: {response}")
        else:
            self.log_result("Email Events Basic", False, f"Request failed: {response}")
        return False

    def test_cooldown_blacklist(self):
        """Test cooldown functionality in blacklist"""
        test_email = f"cooldown-test-{int(time.time())}@example.com"
        
        # Add email to blacklist with cooldown
        success, response = self.make_request(
            "POST", "admin/blacklist", 
            data={
                "email": test_email,
                "reason": "cooldown test",
                "cooldown_days": 7
            }, 
            headers=self.get_auth_headers()
        )
        
        if success:
            self.log_result("Blacklist with Cooldown", True, f"Email: {test_email}")
            
            # Check if cooldown_until field is set
            success2, response2 = self.make_request(
                "GET", "admin/blacklist", 
                headers=self.get_auth_headers()
            )
            
            if success2:
                blacklist_items = response2.get('items', [])
                cooldown_item = next((item for item in blacklist_items if item['email'] == test_email), None)
                
                if cooldown_item and cooldown_item.get('cooldown_until'):
                    self.log_result("Blacklist Cooldown Field", True, f"Cooldown: {cooldown_item['cooldown_until']}")
                    
                    # Test that registration is still blocked
                    success3, response3 = self.make_request(
                        "POST", "whitelist", 
                        data={"email": test_email}, 
                        expected_status=403
                    )
                    
                    if success3:
                        self.log_result("Registration Blocked During Cooldown", True, "Correctly blocked")
                        return True
                    else:
                        self.log_result("Registration Blocked During Cooldown", False, "Should be blocked")
                else:
                    self.log_result("Blacklist Cooldown Field", False, "Cooldown field not set")
            else:
                self.log_result("Blacklist Cooldown Field", False, f"Failed to get blacklist: {response2}")
        else:
            self.log_result("Blacklist with Cooldown", False, f"Request failed: {response}")
        return False

    def test_cooldown_import(self):
        """Test cooldown in bulk import"""
        csv_data = "email,reason\ncooldown-bulk1@example.com,bulk test\ncooldown-bulk2@example.com,bulk test"
        
        success, response = self.make_request(
            "POST", "admin/blacklist/import", 
            data={
                "csv_text": csv_data,
                "cooldown_days": 3
            }, 
            headers=self.get_auth_headers()
        )
        
        if success:
            if response.get('imported', 0) > 0:
                self.log_result("Blacklist Import with Cooldown", True, f"Imported: {response['imported']}")
                return True
            else:
                self.log_result("Blacklist Import with Cooldown", False, f"No emails imported: {response}")
        else:
            self.log_result("Blacklist Import with Cooldown", False, f"Request failed: {response}")
        return False

    def test_whitelist_cooldown_endpoint(self):
        """Test whitelist to blacklist with cooldown"""
        # First get a whitelist entry
        success, response = self.make_request(
            "GET", "admin/whitelist?limit=1", 
            headers=self.get_auth_headers()
        )
        
        if success and response.get('items'):
            entry = response['items'][0]
            entry_id = entry['id']
            
            # Blacklist with cooldown
            success2, response2 = self.make_request(
                "POST", f"admin/whitelist/{entry_id}/blacklist?cooldown_days=5", 
                headers=self.get_auth_headers()
            )
            
            if success2:
                self.log_result("Whitelist to Blacklist with Cooldown", True, f"Entry: {entry_id}")
                return True
            else:
                self.log_result("Whitelist to Blacklist with Cooldown", False, f"Request failed: {response2}")
        else:
            self.log_result("Whitelist to Blacklist with Cooldown", False, "No whitelist entries available")
        return False

    def run_all_tests(self):
        """Run all Phase 8 feature tests"""
        print("🚀 Starting DEEPOTUS Phase 8 Feature Testing...")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Initial admin login
        if not self.admin_login():
            print("❌ Failed to login as admin - stopping tests")
            return False
        
        print("✅ Admin login successful")
        
        # Test 2FA features
        print("\n📱 Testing 2FA Features...")
        self.test_2fa_status_initial()
        
        if self.test_2fa_setup():
            self.test_2fa_verify()
            self.test_2fa_login_flow()
            self.test_2fa_backup_code_login()
            self.test_2fa_disable()  # Clean up - disable 2FA for next test runs

        # Test activity heatmap
        print("\n🔥 Testing Activity Heatmap...")
        self.test_activity_heatmap()

        # Test full whitelist export
        print("\n📊 Testing Full Whitelist Export...")
        self.test_full_whitelist_export()

        # Test email events
        print("\n📧 Testing Email Events...")
        self.test_email_events_endpoint()

        # Test cooldown features
        print("\n⏰ Testing Cooldown Features...")
        self.test_cooldown_blacklist()
        self.test_cooldown_import()
        self.test_whitelist_cooldown_endpoint()
        
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