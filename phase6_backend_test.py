#!/usr/bin/env python3
"""
DEEPOTUS Phase 6 Backend API Testing - Focused Test
Tests only the 4 new Phase 6 features:
1. Admin UI for blacklist (view/unblock/manual add)
2. Welcome email via Resend API on whitelist registration
3. Pagination on admin whitelist + chat-logs tables (25 per page)
4. Public read-only stats dashboard at /stats with counters + evolution chart and NO PII
"""

import requests
import sys
import time
import uuid
from datetime import datetime

class Phase6APITester:
    def __init__(self, base_url="https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_email_verified = "olistruss639@gmail.com"  # Verified Resend email
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    self.log(f"   Response: {response.json()}")
                except:
                    self.log(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def admin_login(self):
        """Login as admin and get token"""
        # Use unique X-Forwarded-For to avoid rate limiting
        unique_ip = f"192.168.1.{uuid.uuid4().int % 255}"
        headers = {'X-Forwarded-For': unique_ip}
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "admin/login",
            200,
            data={"password": "deepotus2026"},
            headers=headers
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            self.log(f"✅ Admin token obtained")
            return True
        return False

    def test_phase6_features(self):
        """Test all Phase 6 features"""
        self.log("🚀 Starting Phase 6 Feature Testing")
        
        # 1. Test Public Stats API (no auth required)
        self.log("\n=== Feature 1: Public Stats Dashboard ===")
        
        success1, data1 = self.run_test(
            "Public Stats API",
            "GET",
            "public/stats?days=30",
            200
        )
        
        if success1:
            # Verify required fields
            required_fields = ['whitelist_count', 'chat_messages', 'prophecies_served', 
                             'launch_timestamp', 'generated_at', 'series_days', 'series']
            missing_fields = [f for f in required_fields if f not in data1]
            if missing_fields:
                self.log(f"❌ Missing required fields: {missing_fields}")
            else:
                self.log(f"✅ All required fields present")
            
            # Verify no PII leakage
            data_str = str(data1).lower()
            if '@' in data_str or 'email' in data_str:
                self.log(f"❌ Potential PII leak detected in public stats")
            else:
                self.log(f"✅ No PII detected in public stats")
            
            # Test days clamping
            success_clamp, data_clamp = self.run_test(
                "Public Stats (days=100, should clamp to 90)",
                "GET",
                "public/stats?days=100",
                200
            )
            
            if success_clamp and data_clamp.get('series_days') == 90:
                self.log(f"✅ Days properly clamped to 90")
            else:
                self.log(f"❌ Days not properly clamped")
        
        # Login as admin for remaining tests
        if not self.admin_login():
            self.log("❌ Failed to login as admin, skipping admin features")
            return
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # 2. Test Admin Pagination APIs
        self.log("\n=== Feature 2: Admin Pagination ===")
        
        # Test whitelist pagination
        success2, data2 = self.run_test(
            "Admin Whitelist Pagination",
            "GET",
            "admin/whitelist?limit=5&skip=0",
            200,
            headers=auth_headers
        )
        
        if success2:
            required_fields = ['items', 'total', 'limit', 'skip']
            missing_fields = [f for f in required_fields if f not in data2]
            if missing_fields:
                self.log(f"❌ Missing pagination fields: {missing_fields}")
            else:
                self.log(f"✅ Whitelist pagination structure valid")
                if data2.get('limit') == 5 and data2.get('skip') == 0:
                    self.log(f"✅ Pagination parameters respected")
                else:
                    self.log(f"❌ Pagination parameters not respected")
        
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
                self.log(f"❌ Missing pagination fields: {missing_fields}")
            else:
                self.log(f"✅ Chat-logs pagination structure valid")
        
        # 3. Test Blacklist CRUD APIs
        self.log("\n=== Feature 3: Blacklist Management ===")
        
        test_email = f"blacklist_test_{int(time.time())}@example.com"
        
        # Test GET blacklist
        success4, data4 = self.run_test(
            "Admin Blacklist List",
            "GET",
            "admin/blacklist",
            200,
            headers=auth_headers
        )
        
        if success4:
            required_fields = ['items', 'total']
            missing_fields = [f for f in required_fields if f not in data4]
            if missing_fields:
                self.log(f"❌ Missing fields in blacklist response: {missing_fields}")
            else:
                self.log(f"✅ Blacklist list structure valid")
        
        # Test POST blacklist (add email)
        success5, _ = self.run_test(
            "Admin Blacklist Add",
            "POST",
            "admin/blacklist",
            200,
            data={"email": test_email, "reason": "Phase 6 test"},
            headers=auth_headers
        )
        
        if success5:
            self.log(f"✅ Email {test_email} added to blacklist")
            
            # Verify email was blacklisted
            success6, data6 = self.run_test(
                "Admin Blacklist List (after add)",
                "GET",
                "admin/blacklist",
                200,
                headers=auth_headers
            )
            
            if success6:
                blacklisted_emails = [item.get('email') for item in data6.get('items', [])]
                if test_email in blacklisted_emails:
                    self.log(f"✅ Email {test_email} found in blacklist")
                    
                    # Find entry ID and test DELETE (unblock)
                    blacklist_entry = next((item for item in data6.get('items', []) if item.get('email') == test_email), None)
                    if blacklist_entry:
                        entry_id = blacklist_entry.get('id')
                        success7, _ = self.run_test(
                            "Admin Blacklist Remove",
                            "DELETE",
                            f"admin/blacklist/{entry_id}",
                            200,
                            headers=auth_headers
                        )
                        
                        if success7:
                            self.log(f"✅ Email {test_email} removed from blacklist")
                            
                            # Test regression: after unblock, email can register again
                            success8, _ = self.run_test(
                                "Try to register after unblock",
                                "POST",
                                "whitelist",
                                200,
                                data={"email": test_email, "lang": "en"}
                            )
                            
                            if success8:
                                self.log(f"✅ Email can register again after unblock (regression test passed)")
                else:
                    self.log(f"❌ Email {test_email} not found in blacklist after adding")
        
        # 4. Test Email Functionality
        self.log("\n=== Feature 4: Welcome Email via Resend ===")
        
        # Test with verified email (should succeed)
        success9, response9 = self.run_test(
            "Whitelist Registration (verified email)",
            "POST",
            "whitelist",
            200,
            data={"email": self.test_email_verified, "lang": "en"}
        )
        
        if success9:
            self.log(f"✅ Whitelist registration successful for verified email")
            
            # Wait for background email task
            self.log("⏳ Waiting 5 seconds for email processing...")
            time.sleep(5)
            
            # Check email status via admin API
            success10, data10 = self.run_test(
                "Check Email Status (verified)",
                "GET",
                "admin/whitelist",
                200,
                headers=auth_headers
            )
            
            if success10:
                # Find our entry
                our_entry = None
                for item in data10.get('items', []):
                    if item.get('email') == self.test_email_verified:
                        our_entry = item
                        break
                
                if our_entry:
                    email_sent = our_entry.get('email_sent', False)
                    self.log(f"📧 Email sent status for {self.test_email_verified}: {email_sent}")
                    if email_sent:
                        self.log(f"✅ Email successfully sent to verified address")
                    else:
                        self.log(f"⚠️  Email not sent yet (may still be processing)")
        
        # Test with unverified email (registration should succeed, email should fail gracefully)
        test_email_unverified = f"test_{int(time.time())}@example.com"
        success11, _ = self.run_test(
            "Whitelist Registration (unverified email)",
            "POST",
            "whitelist",
            200,
            data={"email": test_email_unverified, "lang": "en"}
        )
        
        if success11:
            self.log(f"✅ Registration succeeded for unverified email (as expected)")
            
            # Wait and check email status
            time.sleep(3)
            
            success12, data12 = self.run_test(
                "Check Email Status (unverified)",
                "GET",
                "admin/whitelist",
                200,
                headers=auth_headers
            )
            
            if success12:
                # Find our entry
                our_entry = None
                for item in data12.get('items', []):
                    if item.get('email') == test_email_unverified:
                        our_entry = item
                        break
                
                if our_entry:
                    email_sent = our_entry.get('email_sent', False)
                    self.log(f"📧 Email sent status for {test_email_unverified}: {email_sent}")
                    if not email_sent:
                        self.log(f"✅ Email correctly failed for unverified address (expected)")
                    else:
                        self.log(f"⚠️  Email unexpectedly succeeded for unverified address")

    def run_all_tests(self):
        """Run all Phase 6 tests"""
        self.log("🚀 Starting DEEPOTUS Phase 6 API Testing")
        self.log(f"🌐 Base URL: {self.base_url}")
        
        try:
            self.test_phase6_features()
        except Exception as e:
            self.log(f"❌ Test crashed: {e}")
        
        # Print final results
        self.log(f"\n{'='*50}")
        self.log("FINAL RESULTS")
        self.log(f"{'='*50}")
        self.log(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"📈 Success rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = Phase6APITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())