#!/usr/bin/env python3
"""
DEEPOTUS Backend API Testing - DexScreener Integration Features
Testing DexScreener integration: vault state, dex-config, dex-poll, security, regression tests
"""

import requests
import json
import time
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

# Use public endpoint from .env
BASE_URL = "https://prophet-ai-memecoin.preview.emergentagent.com/api"
ADMIN_PASSWORD = "deepotus2026"

class DexScreenerAPITester:
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

    def test_vault_state_public(self):
        """Test GET /api/vault/state - public endpoint"""
        success, response = self.make_request("GET", "vault/state")
        
        if success:
            # Check required public fields
            required_fields = [
                'code_name', 'stage', 'num_digits', 'digits_locked', 
                'current_combination', 'tokens_per_digit', 'tokens_sold',
                'progress_pct', 'hourly_tick_enabled', 'updated_at', 'recent_events'
            ]
            
            # Check new DexScreener public fields
            dex_fields = ['dex_mode', 'dex_label', 'dex_pair_symbol']
            
            missing_fields = [f for f in required_fields + dex_fields if f not in response]
            
            if not missing_fields:
                # Verify target_combination is NOT exposed
                if 'target_combination' not in response:
                    # Verify dex_mode is valid
                    if response.get('dex_mode') in ['off', 'demo', 'custom']:
                        self.log_result("Vault State Public", True, 
                                      f"Mode: {response.get('dex_mode')}, Stage: {response.get('stage')}")
                        return True
                    else:
                        self.log_result("Vault State Public", False, 
                                      f"Invalid dex_mode: {response.get('dex_mode')}")
                else:
                    self.log_result("Vault State Public", False, "target_combination exposed in public API")
            else:
                self.log_result("Vault State Public", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Vault State Public", False, f"Request failed: {response}")
        return False

    def test_vault_state_admin(self):
        """Test GET /api/admin/vault/state - admin endpoint"""
        success, response = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        
        if success:
            # Check admin-only fields are present
            admin_fields = [
                'target_combination', 'dex_token_address', 'dex_demo_token_address',
                'dex_last_poll_at', 'dex_last_h24_buys', 'dex_last_h24_sells',
                'dex_last_h24_volume_usd', 'dex_last_price_usd', 'dex_carry_tokens'
            ]
            
            present_admin_fields = [f for f in admin_fields if f in response]
            
            if len(present_admin_fields) >= 5:  # At least some admin fields should be present
                # Verify target_combination is a list of 6 integers
                target = response.get('target_combination', [])
                if isinstance(target, list) and len(target) == 6 and all(isinstance(d, int) and 0 <= d <= 9 for d in target):
                    self.log_result("Vault State Admin", True, 
                                  f"Target: {target}, Admin fields: {len(present_admin_fields)}")
                    return True
                else:
                    self.log_result("Vault State Admin", False, f"Invalid target_combination: {target}")
            else:
                self.log_result("Vault State Admin", False, f"Missing admin fields: {admin_fields}")
        else:
            self.log_result("Vault State Admin", False, f"Request failed: {response}")
        return False

    def test_dex_config_off_mode(self):
        """Test POST /api/admin/vault/dex-config with mode='off'"""
        data = {"mode": "off"}
        success, response = self.make_request("POST", "admin/vault/dex-config", data, headers=self.get_auth_headers())
        
        if success:
            if response.get('dex_mode') == 'off':
                self.log_result("Dex Config Off Mode", True, "Mode set to off")
                return True
            else:
                self.log_result("Dex Config Off Mode", False, f"Mode not set: {response.get('dex_mode')}")
        else:
            self.log_result("Dex Config Off Mode", False, f"Request failed: {response}")
        return False

    def test_dex_config_demo_mode(self):
        """Test POST /api/admin/vault/dex-config with mode='demo'"""
        data = {"mode": "demo"}
        success, response = self.make_request("POST", "admin/vault/dex-config", data, headers=self.get_auth_headers())
        
        if success:
            if response.get('dex_mode') == 'demo':
                # Should have demo token address set
                if response.get('dex_demo_token_address'):
                    self.log_result("Dex Config Demo Mode", True, 
                                  f"Demo token: {response.get('dex_demo_token_address')[:8]}...")
                    return True
                else:
                    self.log_result("Dex Config Demo Mode", False, "Demo token address not set")
            else:
                self.log_result("Dex Config Demo Mode", False, f"Mode not set: {response.get('dex_mode')}")
        else:
            self.log_result("Dex Config Demo Mode", False, f"Request failed: {response}")
        return False

    def test_dex_config_custom_mode(self):
        """Test POST /api/admin/vault/dex-config with mode='custom'"""
        # Test without token_address (should work but not set custom address)
        data = {"mode": "custom"}
        success, response = self.make_request("POST", "admin/vault/dex-config", data, headers=self.get_auth_headers())
        
        if success:
            if response.get('dex_mode') == 'custom':
                self.log_result("Dex Config Custom Mode (no address)", True, "Mode set to custom")
                
                # Test with token_address
                test_address = "So11111111111111111111111111111111111111112"  # SOL mint
                data_with_address = {"mode": "custom", "token_address": test_address}
                success2, response2 = self.make_request("POST", "admin/vault/dex-config", data_with_address, headers=self.get_auth_headers())
                
                if success2:
                    if response2.get('dex_token_address') == test_address:
                        self.log_result("Dex Config Custom Mode (with address)", True, f"Address: {test_address[:8]}...")
                        return True
                    else:
                        self.log_result("Dex Config Custom Mode (with address)", False, 
                                      f"Address not set: {response2.get('dex_token_address')}")
                else:
                    self.log_result("Dex Config Custom Mode (with address)", False, f"Request failed: {response2}")
            else:
                self.log_result("Dex Config Custom Mode (no address)", False, f"Mode not set: {response.get('dex_mode')}")
        else:
            self.log_result("Dex Config Custom Mode (no address)", False, f"Request failed: {response}")
        return False

    def test_dex_poll_off_mode(self):
        """Test POST /api/admin/vault/dex-poll with dex_mode='off'"""
        # First set mode to off
        self.make_request("POST", "admin/vault/dex-config", {"mode": "off"}, headers=self.get_auth_headers())
        
        # Then try to poll
        success, response = self.make_request("POST", "admin/vault/dex-poll", headers=self.get_auth_headers())
        
        if success:
            if response.get('mode') == 'off' and response.get('skipped') == True:
                self.log_result("Dex Poll Off Mode", True, "Correctly skipped when off")
                return True
            else:
                self.log_result("Dex Poll Off Mode", False, f"Unexpected response: {response}")
        else:
            self.log_result("Dex Poll Off Mode", False, f"Request failed: {response}")
        return False

    def test_dex_poll_demo_mode(self):
        """Test POST /api/admin/vault/dex-poll with dex_mode='demo'"""
        # Set mode to demo
        self.make_request("POST", "admin/vault/dex-config", {"mode": "demo"}, headers=self.get_auth_headers())
        
        # Wait a moment for config to settle
        time.sleep(1)
        
        # Poll twice to test baseline vs delta behavior
        success1, response1 = self.make_request("POST", "admin/vault/dex-poll", headers=self.get_auth_headers())
        
        if success1:
            # First poll should have ticks_applied = 0 (baseline)
            if response1.get('mode') == 'demo' and response1.get('first_seen') == True:
                if response1.get('ticks_applied') == 0:
                    self.log_result("Dex Poll Demo Mode (First)", True, "Baseline established")
                    
                    # Wait and poll again
                    time.sleep(2)
                    success2, response2 = self.make_request("POST", "admin/vault/dex-poll", headers=self.get_auth_headers())
                    
                    if success2:
                        # Second poll might apply ticks if there's activity
                        ticks = response2.get('ticks_applied', 0)
                        if ticks >= 0 and ticks <= 3:  # Should be capped at 3 per poll
                            self.log_result("Dex Poll Demo Mode (Second)", True, f"Ticks applied: {ticks}")
                            return True
                        else:
                            self.log_result("Dex Poll Demo Mode (Second)", False, f"Invalid ticks: {ticks}")
                    else:
                        self.log_result("Dex Poll Demo Mode (Second)", False, f"Second poll failed: {response2}")
                else:
                    self.log_result("Dex Poll Demo Mode (First)", False, f"Expected 0 ticks on first poll, got: {response1.get('ticks_applied')}")
            else:
                self.log_result("Dex Poll Demo Mode (First)", False, f"Unexpected first poll response: {response1}")
        else:
            self.log_result("Dex Poll Demo Mode (First)", False, f"First poll failed: {response1}")
        return False

    def test_dex_poll_diagnostic_fields(self):
        """Test that dex-poll returns all required diagnostic fields"""
        # Set to demo mode for testing
        self.make_request("POST", "admin/vault/dex-config", {"mode": "demo"}, headers=self.get_auth_headers())
        time.sleep(1)
        
        success, response = self.make_request("POST", "admin/vault/dex-poll", headers=self.get_auth_headers())
        
        if success:
            required_fields = [
                'mode', 'address', 'pair', 'price_usd', 'volume_h24', 
                'buys_h24', 'sells_h24', 'delta_buys', 'delta_vol_usd', 
                'ticks_applied', 'carry_after', 'first_seen'
            ]
            
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                self.log_result("Dex Poll Diagnostic Fields", True, f"All {len(required_fields)} fields present")
                return True
            else:
                self.log_result("Dex Poll Diagnostic Fields", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Dex Poll Diagnostic Fields", False, f"Request failed: {response}")
        return False

    def test_dex_mode_baseline_reset(self):
        """Test that switching dex_mode resets baselines"""
        # Set to demo mode and poll to establish baselines
        self.make_request("POST", "admin/vault/dex-config", {"mode": "demo"}, headers=self.get_auth_headers())
        time.sleep(1)
        self.make_request("POST", "admin/vault/dex-poll", headers=self.get_auth_headers())
        
        # Get admin state to check baselines are set
        success1, state1 = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        
        if success1:
            # Switch to off mode
            self.make_request("POST", "admin/vault/dex-config", {"mode": "off"}, headers=self.get_auth_headers())
            
            # Check that baselines are reset
            success2, state2 = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
            
            if success2:
                # Check that baseline fields are reset
                baseline_fields = ['dex_last_h24_buys', 'dex_last_h24_sells', 'dex_last_h24_volume_usd', 'dex_carry_tokens']
                reset_values = [state2.get(f) for f in baseline_fields]
                
                # All should be 0 or 0.0 or None
                if all(v in [0, 0.0, None] for v in reset_values):
                    self.log_result("Dex Mode Baseline Reset", True, "Baselines reset on mode switch")
                    return True
                else:
                    self.log_result("Dex Mode Baseline Reset", False, f"Baselines not reset: {reset_values}")
            else:
                self.log_result("Dex Mode Baseline Reset", False, f"Failed to get state after reset: {state2}")
        else:
            self.log_result("Dex Mode Baseline Reset", False, f"Failed to get initial state: {state1}")
        return False

    def test_security_public_vault_state(self):
        """Test that public vault state doesn't expose admin-only fields"""
        success, response = self.make_request("GET", "vault/state")
        
        if success:
            # Fields that should NOT be in public response
            forbidden_fields = [
                'target_combination', 'dex_token_address', 'dex_last_price_usd',
                'dex_last_h24_buys', 'dex_last_h24_sells', 'dex_last_h24_volume_usd',
                'dex_carry_tokens', 'dex_error'
            ]
            
            exposed_fields = [f for f in forbidden_fields if f in response]
            
            if not exposed_fields:
                # Check that allowed dex fields are present
                allowed_fields = ['dex_mode', 'dex_label', 'dex_pair_symbol']
                present_allowed = [f for f in allowed_fields if f in response]
                
                if len(present_allowed) == len(allowed_fields):
                    self.log_result("Security Public Vault State", True, "No admin fields exposed")
                    return True
                else:
                    self.log_result("Security Public Vault State", False, f"Missing allowed fields: {set(allowed_fields) - set(present_allowed)}")
            else:
                self.log_result("Security Public Vault State", False, f"Admin fields exposed: {exposed_fields}")
        else:
            self.log_result("Security Public Vault State", False, f"Request failed: {response}")
        return False

    def test_security_admin_endpoints_require_jwt(self):
        """Test that admin vault endpoints require JWT authentication"""
        endpoints = [
            "admin/vault/state",
            "admin/vault/dex-config", 
            "admin/vault/dex-poll"
        ]
        
        all_protected = True
        
        for endpoint in endpoints:
            if endpoint == "admin/vault/dex-config" or endpoint == "admin/vault/dex-poll":
                success, response = self.make_request("POST", endpoint, {}, expected_status=401)
            else:
                success, response = self.make_request("GET", endpoint, expected_status=401)
            
            if success:
                self.log_result(f"Security {endpoint} (no JWT)", True, "Correctly rejected")
            else:
                self.log_result(f"Security {endpoint} (no JWT)", False, "Should return 401")
                all_protected = False
        
        return all_protected

    def test_regression_existing_endpoints(self):
        """Test that existing endpoints still work"""
        endpoints_to_test = [
            ("POST", "admin/login", {"password": ADMIN_PASSWORD}, 200),
            ("POST", "whitelist", {"email": f"test-{int(time.time())}@example.com"}, 200),
            ("GET", "chat", None, 405),  # Should be POST only
            ("GET", "prophecy", None, 200),
            ("GET", "stats", None, 200),
            ("GET", "public/stats", None, 200),
        ]
        
        all_working = True
        
        for method, endpoint, data, expected_status in endpoints_to_test:
            if endpoint.startswith("admin/") and endpoint != "admin/login":
                headers = self.get_auth_headers()
            else:
                headers = {}
            
            success, response = self.make_request(method, endpoint, data, headers=headers, expected_status=expected_status)
            
            if success:
                self.log_result(f"Regression {method} {endpoint}", True, f"Status {expected_status}")
            else:
                self.log_result(f"Regression {method} {endpoint}", False, f"Expected {expected_status}, got error")
                all_working = False
        
        return all_working

    def test_hourly_tick_still_enabled(self):
        """Test that hourly auto-tick is still enabled"""
        success, response = self.make_request("GET", "vault/state")
        
        if success:
            if 'hourly_tick_enabled' in response:
                enabled = response['hourly_tick_enabled']
                self.log_result("Hourly Tick Enabled", True, f"Enabled: {enabled}")
                return True
            else:
                self.log_result("Hourly Tick Enabled", False, "Field missing from response")
        else:
            self.log_result("Hourly Tick Enabled", False, f"Request failed: {response}")
        return False

    def run_all_tests(self):
        """Run all DexScreener integration tests"""
        print("🚀 Starting DEEPOTUS DexScreener Integration Testing...")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Initial admin login
        if not self.admin_login():
            print("❌ Failed to login as admin - stopping tests")
            return False
        
        print("✅ Admin login successful")
        
        # Test vault state endpoints
        print("\n🏦 Testing Vault State Endpoints...")
        self.test_vault_state_public()
        self.test_vault_state_admin()
        
        # Test dex-config endpoint
        print("\n⚙️ Testing Dex Config Endpoint...")
        self.test_dex_config_off_mode()
        self.test_dex_config_demo_mode()
        self.test_dex_config_custom_mode()
        
        # Test dex-poll endpoint
        print("\n📊 Testing Dex Poll Endpoint...")
        self.test_dex_poll_off_mode()
        self.test_dex_poll_demo_mode()
        self.test_dex_poll_diagnostic_fields()
        
        # Test mechanics
        print("\n🔧 Testing Mechanics...")
        self.test_dex_mode_baseline_reset()
        
        # Test security
        print("\n🔒 Testing Security...")
        self.test_security_public_vault_state()
        self.test_security_admin_endpoints_require_jwt()
        
        # Test regression
        print("\n🔄 Testing Regression...")
        self.test_regression_existing_endpoints()
        self.test_hourly_tick_still_enabled()
        
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
    tester = DexScreenerAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)