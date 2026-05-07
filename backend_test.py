#!/usr/bin/env python3
"""Backend API tests for Sprint 17.5 — Cabinet Expansion.

Tests:
  1. POST /api/access-card/request with optional x_handle
  2. Production mode bootstrap (dispatch_enabled=true, dispatch_dry_run=false)
  3. GET /api/admin/propaganda/welcome-signal
  4. PATCH /api/admin/propaganda/welcome-signal (requires 2FA)
  5. POST /api/admin/propaganda/welcome-signal/fire-now (requires 2FA)
  6. GET /api/admin/propaganda/interaction-bot
  7. PATCH /api/admin/propaganda/interaction-bot (requires 2FA)
  8. POST /api/admin/propaganda/interaction-bot/fire-now (requires 2FA)
"""

import sys
import requests
from datetime import datetime

# Public endpoint from frontend/.env
BASE_URL = "https://prophet-ai-memecoin.preview.emergentagent.com"
ADMIN_PASSWORD = "deepotus2026"

class CabinetExpansionTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_email = f"test_cabinet_{datetime.now().strftime('%H%M%S')}@example.com"

    def log(self, msg, status="INFO"):
        prefix = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🔍"
        print(f"{prefix} {msg}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        h = headers or {}
        
        self.tests_run += 1
        self.log(f"Testing {name}...", "INFO")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=h, params=params, timeout=15)
            elif method == "POST":
                response = requests.post(url, json=data, headers=h, params=params, timeout=15)
            elif method == "PATCH":
                response = requests.patch(url, json=data, headers=h, timeout=15)
            else:
                self.log(f"Unknown method {method}", "FAIL")
                return False, {}

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"PASS - {name} (status: {response.status_code})", "PASS")
            else:
                self.log(f"FAIL - {name} (expected {expected_status}, got {response.status_code})", "FAIL")
                if response.text:
                    self.log(f"  Response: {response.text[:200]}", "INFO")

            try:
                return success, response.json() if response.text else {}
            except:
                return success, {}

        except Exception as e:
            self.log(f"FAIL - {name} (error: {str(e)})", "FAIL")
            return False, {}

    def admin_login(self):
        """Login as admin to get JWT token"""
        self.log("Logging in as admin...", "INFO")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/api/admin/login",
            200,
            data={"password": ADMIN_PASSWORD}
        )
        if success and response.get("token"):
            self.admin_token = response["token"]
            self.log("Admin login successful", "PASS")
            return True
        self.log("Admin login failed", "FAIL")
        return False

    def test_access_card_with_x_handle(self):
        """Test POST /api/access-card/request with x_handle field"""
        self.log("\n=== Testing Access Card with X Handle ===", "INFO")
        
        # Test 1: Submit with x_handle
        success, response = self.run_test(
            "Access Card Request with X Handle",
            "POST",
            "/api/access-card/request",
            200,
            data={
                "email": self.test_email,
                "display_name": "Test Agent",
                "x_handle": "@test_handle_123"
            }
        )
        
        if success:
            self.log(f"  Email: {response.get('email')}", "INFO")
            self.log(f"  Display Name: {response.get('display_name')}", "INFO")
            self.log(f"  Message: {response.get('message')}", "INFO")
        
        # Test 2: Submit without x_handle (legacy path)
        test_email_2 = f"test_no_handle_{datetime.now().strftime('%H%M%S')}@example.com"
        success2, response2 = self.run_test(
            "Access Card Request without X Handle (legacy)",
            "POST",
            "/api/access-card/request",
            200,
            data={
                "email": test_email_2,
                "display_name": "Test Agent No Handle"
            }
        )
        
        return success and success2

    def test_propaganda_settings(self):
        """Test that production mode is enabled"""
        self.log("\n=== Testing Production Mode Bootstrap ===", "INFO")
        
        if not self.admin_token:
            self.log("Skipping - no admin token", "FAIL")
            return False
        
        success, response = self.run_test(
            "Get Propaganda Settings",
            "GET",
            "/api/admin/propaganda/settings",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success:
            dispatch_enabled = response.get("dispatch_enabled")
            dispatch_dry_run = response.get("dispatch_dry_run")
            
            self.log(f"  dispatch_enabled: {dispatch_enabled}", "INFO")
            self.log(f"  dispatch_dry_run: {dispatch_dry_run}", "INFO")
            
            # Production mode should have dispatch_enabled=True
            if dispatch_enabled is True:
                self.log("  Production mode: dispatch_enabled=True ✓", "PASS")
            else:
                self.log("  Production mode: dispatch_enabled not True", "FAIL")
                
        return success

    def test_welcome_signal_endpoints(self):
        """Test Welcome Signal admin endpoints"""
        self.log("\n=== Testing Welcome Signal Endpoints ===", "INFO")
        
        if not self.admin_token:
            self.log("Skipping - no admin token", "FAIL")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: GET welcome-signal
        success1, response1 = self.run_test(
            "GET Welcome Signal Settings",
            "GET",
            "/api/admin/propaganda/welcome-signal",
            200,
            headers=headers
        )
        
        if success1:
            settings = response1.get("settings", {})
            self.log(f"  enabled: {settings.get('enabled')}", "INFO")
            self.log(f"  hour_utc: {settings.get('hour_utc')}", "INFO")
            self.log(f"  min_handles: {settings.get('min_handles')}", "INFO")
            self.log(f"  max_handles: {settings.get('max_handles')}", "INFO")
            self.log(f"  eligible_count: {response1.get('eligible_count')}", "INFO")
        
        # Test 2: PATCH welcome-signal (will fail without 2FA, which is expected)
        success2, response2 = self.run_test(
            "PATCH Welcome Signal (expect 403 without 2FA)",
            "PATCH",
            "/api/admin/propaganda/welcome-signal",
            403,  # Expected to fail without 2FA
            data={"hour_utc": 14},
            headers=headers
        )
        
        if success2:
            self.log("  Correctly requires 2FA for PATCH", "PASS")
        
        # Test 3: POST fire-now (will fail without 2FA, which is expected)
        success3, response3 = self.run_test(
            "POST Welcome Signal Fire Now (expect 403 without 2FA)",
            "POST",
            "/api/admin/propaganda/welcome-signal/fire-now",
            403,  # Expected to fail without 2FA
            headers=headers
        )
        
        if success3:
            self.log("  Correctly requires 2FA for POST fire-now", "PASS")
        
        return success1 and success2 and success3

    def test_interaction_bot_endpoints(self):
        """Test Interaction Bot admin endpoints"""
        self.log("\n=== Testing Interaction Bot Endpoints ===", "INFO")
        
        if not self.admin_token:
            self.log("Skipping - no admin token", "FAIL")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: GET interaction-bot
        success1, response1 = self.run_test(
            "GET Interaction Bot Settings",
            "GET",
            "/api/admin/propaganda/interaction-bot",
            200,
            headers=headers
        )
        
        if success1:
            settings = response1.get("settings", {})
            self.log(f"  enabled: {settings.get('enabled')}", "INFO")
            self.log(f"  max_replies_per_hour: {settings.get('max_replies_per_hour')}", "INFO")
            self.log(f"  min_replies_per_hour: {settings.get('min_replies_per_hour')}", "INFO")
            self.log(f"  per_handle_cooldown_hours: {settings.get('per_handle_cooldown_hours')}", "INFO")
            self.log(f"  total_replies_lifetime: {settings.get('total_replies_lifetime')}", "INFO")
        
        # Test 2: PATCH interaction-bot (will fail without 2FA, which is expected)
        success2, response2 = self.run_test(
            "PATCH Interaction Bot (expect 403 without 2FA)",
            "PATCH",
            "/api/admin/propaganda/interaction-bot",
            403,  # Expected to fail without 2FA
            data={"max_replies_per_hour": 3},
            headers=headers
        )
        
        if success2:
            self.log("  Correctly requires 2FA for PATCH", "PASS")
        
        # Test 3: POST fire-now with dry_run (will fail without 2FA, which is expected)
        success3, response3 = self.run_test(
            "POST Interaction Bot Fire Now (expect 403 without 2FA)",
            "POST",
            "/api/admin/propaganda/interaction-bot/fire-now",
            403,  # Expected to fail without 2FA
            params={"dry_run": "true"},
            headers=headers
        )
        
        if success3:
            self.log("  Correctly requires 2FA for POST fire-now", "PASS")
        
        return success1 and success2 and success3

    def test_regression_endpoints(self):
        """Test that existing endpoints still work"""
        self.log("\n=== Testing Regression (Existing Endpoints) ===", "INFO")
        
        # Test 1: Whitelist endpoint
        success1, _ = self.run_test(
            "POST Whitelist (existing endpoint)",
            "POST",
            "/api/whitelist",
            200,
            data={"email": f"whitelist_{datetime.now().strftime('%H%M%S')}@example.com"}
        )
        
        # Test 2: Vault status
        success2, _ = self.run_test(
            "GET Vault Classified Status",
            "GET",
            "/api/vault/classified-status",
            200
        )
        
        # Test 3: Propaganda triggers (admin)
        if self.admin_token:
            success3, _ = self.run_test(
                "GET Propaganda Triggers",
                "GET",
                "/api/admin/propaganda/triggers",
                200,
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
        else:
            success3 = False
        
        return success1 and success2 and success3

    def run_all_tests(self):
        """Run all tests"""
        self.log("=" * 60, "INFO")
        self.log("Cabinet Expansion Backend Tests (Sprint 17.5)", "INFO")
        self.log(f"Base URL: {self.base_url}", "INFO")
        self.log("=" * 60, "INFO")
        
        # Login first
        if not self.admin_login():
            self.log("\nCannot proceed without admin login", "FAIL")
            return 1
        
        # Run all test suites
        self.test_access_card_with_x_handle()
        self.test_propaganda_settings()
        self.test_welcome_signal_endpoints()
        self.test_interaction_bot_endpoints()
        self.test_regression_endpoints()
        
        # Print summary
        self.log("\n" + "=" * 60, "INFO")
        self.log(f"Tests passed: {self.tests_passed}/{self.tests_run}", "INFO")
        self.log("=" * 60, "INFO")
        
        return 0 if self.tests_passed == self.tests_run else 1

def main():
    tester = CabinetExpansionTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
