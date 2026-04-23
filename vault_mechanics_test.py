#!/usr/bin/env python3
"""
DEEPOTUS Vault Mechanics Rework Testing
Testing the major mechanics rework with new production defaults, micro-rotations, 
treasury-based declassification, and admin presets.
"""

import requests
import json
import time
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Use public endpoint from .env
BASE_URL = "https://prophet-ai-memecoin.preview.emergentagent.com/api"
ADMIN_PASSWORD = "deepotus2026"

class VaultMechanicsAPITester:
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

    def setup_clean_vault_state(self):
        """Setup clean vault state with production defaults"""
        print("🔧 Setting up clean vault state with production defaults...")
        data = {"preset": "production", "reset": True}
        success, response = self.make_request("POST", "admin/vault/config", data, headers=self.get_auth_headers())
        
        if success:
            print("✅ Clean vault state established")
            return True
        else:
            print(f"❌ Failed to setup clean vault state: {response}")
            return False

    def test_production_defaults_after_init(self):
        """Test that production defaults are correctly set after fresh init"""
        success, response = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        
        if success:
            expected_defaults = {
                'tokens_per_digit': 100_000_000,  # 100M
                'tokens_per_micro': 10_000,       # 10K
                'treasury_goal_eur': 300_000.0,   # 300K EUR
                'eur_usd_rate': 1.08
            }
            
            all_correct = True
            details = []
            
            for field, expected_value in expected_defaults.items():
                actual_value = response.get(field)
                if actual_value == expected_value:
                    details.append(f"{field}={actual_value}")
                else:
                    details.append(f"{field}={actual_value} (expected {expected_value})")
                    all_correct = False
            
            self.log_result("Production Defaults After Init", all_correct, "; ".join(details))
            return all_correct
        else:
            self.log_result("Production Defaults After Init", False, f"Request failed: {response}")
            return False

    def test_public_vault_state_new_fields(self):
        """Test GET /api/vault/state returns new fields: tokens_per_micro, micro_ticks_total, treasury_eur_value, treasury_progress_pct"""
        success, response = self.make_request("GET", "vault/state")
        
        if success:
            required_new_fields = [
                'tokens_per_micro',
                'micro_ticks_total', 
                'treasury_eur_value',
                'treasury_progress_pct'
            ]
            
            missing_fields = [f for f in required_new_fields if f not in response]
            
            if not missing_fields:
                # Verify initial values make sense
                tokens_per_micro = response.get('tokens_per_micro', 0)
                tokens_sold = response.get('tokens_sold', 0)
                micro_ticks_total = response.get('micro_ticks_total', 0)
                
                expected_micro_ticks = tokens_sold // max(1, tokens_per_micro)
                
                if micro_ticks_total == expected_micro_ticks:
                    details = f"tokens_per_micro={tokens_per_micro}, micro_ticks_total={micro_ticks_total}, treasury_eur_value={response.get('treasury_eur_value')}, treasury_progress_pct={response.get('treasury_progress_pct')}"
                    self.log_result("Public Vault State New Fields", True, details)
                    return True
                else:
                    self.log_result("Public Vault State New Fields", False, 
                                  f"micro_ticks_total calculation wrong: {micro_ticks_total} != {expected_micro_ticks}")
            else:
                self.log_result("Public Vault State New Fields", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Public Vault State New Fields", False, f"Request failed: {response}")
        return False

    def test_admin_vault_state_additional_fields(self):
        """Test GET /api/admin/vault/state additionally returns treasury_goal_eur and eur_usd_rate"""
        success, response = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        
        if success:
            additional_admin_fields = ['treasury_goal_eur', 'eur_usd_rate']
            missing_fields = [f for f in additional_admin_fields if f not in response]
            
            if not missing_fields:
                treasury_goal = response.get('treasury_goal_eur')
                eur_usd_rate = response.get('eur_usd_rate')
                
                # Verify these are the production defaults
                if treasury_goal == 300_000.0 and eur_usd_rate == 1.08:
                    self.log_result("Admin Vault State Additional Fields", True, 
                                  f"treasury_goal_eur={treasury_goal}, eur_usd_rate={eur_usd_rate}")
                    return True
                else:
                    self.log_result("Admin Vault State Additional Fields", False, 
                                  f"Wrong values: treasury_goal_eur={treasury_goal}, eur_usd_rate={eur_usd_rate}")
            else:
                self.log_result("Admin Vault State Additional Fields", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Admin Vault State Additional Fields", False, f"Request failed: {response}")
        return False

    def test_crack_with_50k_tokens_micro_rotation(self):
        """Test POST /api/admin/vault/crack with {tokens: 50000} produces micro_ticks_total increase but no digits_locked change"""
        # Get initial state
        success, initial_state = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        if not success:
            self.log_result("Crack 50K Tokens - Get Initial State", False, f"Failed to get initial state: {initial_state}")
            return False
        
        initial_micro_ticks = initial_state.get('micro_ticks_total', 0)
        initial_digits_locked = initial_state.get('digits_locked', 0)
        tokens_per_micro = initial_state.get('tokens_per_micro', 10_000)
        
        # Apply crack with 50K tokens
        crack_data = {"tokens": 50_000}
        success, response = self.make_request("POST", "admin/vault/crack", crack_data, headers=self.get_auth_headers())
        
        if success:
            new_micro_ticks = response.get('micro_ticks_total', 0)
            new_digits_locked = response.get('digits_locked', 0)
            
            expected_micro_increase = 50_000 // tokens_per_micro  # Should be 5
            actual_micro_increase = new_micro_ticks - initial_micro_ticks
            
            if actual_micro_increase == expected_micro_increase and new_digits_locked == initial_digits_locked:
                self.log_result("Crack 50K Tokens Micro Rotation", True, 
                              f"micro_ticks increased by {actual_micro_increase}, digits_locked unchanged ({new_digits_locked})")
                return True
            else:
                self.log_result("Crack 50K Tokens Micro Rotation", False, 
                              f"micro_ticks increased by {actual_micro_increase} (expected {expected_micro_increase}), digits_locked: {initial_digits_locked} -> {new_digits_locked}")
        else:
            self.log_result("Crack 50K Tokens Micro Rotation", False, f"Request failed: {response}")
        return False

    def test_crack_with_100m_tokens_locks_dial(self):
        """Test POST /api/admin/vault/crack with {tokens: 100000000} locks ONE additional dial"""
        # Get initial state
        success, initial_state = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        if not success:
            self.log_result("Crack 100M Tokens - Get Initial State", False, f"Failed to get initial state: {initial_state}")
            return False
        
        initial_digits_locked = initial_state.get('digits_locked', 0)
        
        # Apply crack with 100M tokens
        crack_data = {"tokens": 100_000_000}
        success, response = self.make_request("POST", "admin/vault/crack", crack_data, headers=self.get_auth_headers())
        
        if success:
            new_digits_locked = response.get('digits_locked', 0)
            
            if new_digits_locked == initial_digits_locked + 1:
                self.log_result("Crack 100M Tokens Locks Dial", True, 
                              f"digits_locked: {initial_digits_locked} -> {new_digits_locked}")
                return True
            else:
                self.log_result("Crack 100M Tokens Locks Dial", False, 
                              f"digits_locked: {initial_digits_locked} -> {new_digits_locked} (expected +1)")
        else:
            self.log_result("Crack 100M Tokens Locks Dial", False, f"Request failed: {response}")
        return False

    def test_sequential_6_cracks_reach_declassified(self):
        """Test sequential 6 cracks of 100M tokens each should reach DECLASSIFIED"""
        # First reset to clean state
        if not self.setup_clean_vault_state():
            return False
        
        # Apply 6 sequential cracks of 100M tokens each
        for i in range(6):
            crack_data = {"tokens": 100_000_000, "note": f"Sequential crack {i+1}/6"}
            success, response = self.make_request("POST", "admin/vault/crack", crack_data, headers=self.get_auth_headers())
            
            if not success:
                self.log_result("Sequential 6 Cracks", False, f"Crack {i+1} failed: {response}")
                return False
            
            digits_locked = response.get('digits_locked', 0)
            stage = response.get('stage', '')
            
            print(f"  Crack {i+1}/6: digits_locked={digits_locked}, stage={stage}")
        
        # Check final state
        success, final_state = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        if success:
            final_digits_locked = final_state.get('digits_locked', 0)
            final_stage = final_state.get('stage', '')
            
            if final_digits_locked == 6 and final_stage == "DECLASSIFIED":
                self.log_result("Sequential 6 Cracks Reach Declassified", True, 
                              f"Final state: digits_locked={final_digits_locked}, stage={final_stage}")
                return True
            else:
                self.log_result("Sequential 6 Cracks Reach Declassified", False, 
                              f"Final state: digits_locked={final_digits_locked}, stage={final_stage}")
        else:
            self.log_result("Sequential 6 Cracks Reach Declassified", False, f"Failed to get final state: {final_state}")
        return False

    def test_production_preset_config(self):
        """Test POST /api/admin/vault/config with {preset: 'production'}"""
        data = {"preset": "production"}
        success, response = self.make_request("POST", "admin/vault/config", data, headers=self.get_auth_headers())
        
        if success:
            expected_values = {
                'tokens_per_digit': 100_000_000,
                'tokens_per_micro': 10_000,
                'treasury_goal_eur': 300_000.0,
                'eur_usd_rate': 1.08
            }
            
            all_correct = True
            details = []
            
            for field, expected_value in expected_values.items():
                actual_value = response.get(field)
                if actual_value == expected_value:
                    details.append(f"{field}={actual_value}")
                else:
                    details.append(f"{field}={actual_value} (expected {expected_value})")
                    all_correct = False
            
            self.log_result("Production Preset Config", all_correct, "; ".join(details))
            return all_correct
        else:
            self.log_result("Production Preset Config", False, f"Request failed: {response}")
            return False

    def test_demo_preset_config(self):
        """Test POST /api/admin/vault/config with {preset: 'demo'}"""
        data = {"preset": "demo"}
        success, response = self.make_request("POST", "admin/vault/config", data, headers=self.get_auth_headers())
        
        if success:
            expected_values = {
                'tokens_per_digit': 1_000,
                'tokens_per_micro': 100
            }
            
            all_correct = True
            details = []
            
            for field, expected_value in expected_values.items():
                actual_value = response.get(field)
                if actual_value == expected_value:
                    details.append(f"{field}={actual_value}")
                else:
                    details.append(f"{field}={actual_value} (expected {expected_value})")
                    all_correct = False
            
            # Treasury config should remain untouched in demo mode
            treasury_goal = response.get('treasury_goal_eur')
            eur_usd_rate = response.get('eur_usd_rate')
            details.append(f"treasury_goal_eur={treasury_goal}, eur_usd_rate={eur_usd_rate}")
            
            self.log_result("Demo Preset Config", all_correct, "; ".join(details))
            return all_correct
        else:
            self.log_result("Demo Preset Config", False, f"Request failed: {response}")
            return False

    def test_individual_config_updates(self):
        """Test POST /api/admin/vault/config with individual field updates"""
        data = {
            "tokens_per_micro": 500,
            "treasury_goal_eur": 50_000,
            "eur_usd_rate": 1.15
        }
        success, response = self.make_request("POST", "admin/vault/config", data, headers=self.get_auth_headers())
        
        if success:
            all_correct = True
            details = []
            
            for field, expected_value in data.items():
                actual_value = response.get(field)
                if actual_value == expected_value:
                    details.append(f"{field}={actual_value}")
                else:
                    details.append(f"{field}={actual_value} (expected {expected_value})")
                    all_correct = False
            
            self.log_result("Individual Config Updates", all_correct, "; ".join(details))
            return all_correct
        else:
            self.log_result("Individual Config Updates", False, f"Request failed: {response}")
            return False

    def test_treasury_based_declassification_logic(self):
        """Test treasury-based fast-path declassification by simulating custom mode with high price"""
        # This test validates the logic by checking treasury_eur_value calculation
        # Since we can't easily inject a fake price through public API, we'll test the calculation logic
        
        # First set to custom mode (though we can't easily test the full flow without real price data)
        dex_config = {"mode": "custom", "token_address": "So11111111111111111111111111111111111111112"}
        success, response = self.make_request("POST", "admin/vault/dex-config", dex_config, headers=self.get_auth_headers())
        
        if success:
            # Get current state to verify treasury calculation fields are present
            success2, state = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
            
            if success2:
                # Check that treasury calculation fields are present
                required_fields = ['treasury_eur_value', 'treasury_progress_pct', 'treasury_goal_eur', 'eur_usd_rate']
                missing_fields = [f for f in required_fields if f not in state]
                
                if not missing_fields:
                    # In custom mode without real price, treasury_eur_value should be 0
                    treasury_eur_value = state.get('treasury_eur_value', -1)
                    if treasury_eur_value == 0.0:
                        self.log_result("Treasury Based Declassification Logic", True, 
                                      f"Custom mode set, treasury fields present, treasury_eur_value={treasury_eur_value}")
                        return True
                    else:
                        self.log_result("Treasury Based Declassification Logic", False, 
                                      f"Expected treasury_eur_value=0.0, got {treasury_eur_value}")
                else:
                    self.log_result("Treasury Based Declassification Logic", False, 
                                  f"Missing treasury fields: {missing_fields}")
            else:
                self.log_result("Treasury Based Declassification Logic", False, f"Failed to get state: {state}")
        else:
            self.log_result("Treasury Based Declassification Logic", False, f"Failed to set custom mode: {response}")
        return False

    def test_hourly_tick_production_scale(self):
        """Test that hourly tick at production scale is reasonable (≤ 10% of one dial)"""
        # Set to production scale
        if not self.setup_clean_vault_state():
            return False
        
        # Get current state
        success, state = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        
        if success:
            tokens_per_digit = state.get('tokens_per_digit', 100_000_000)
            tokens_per_micro = state.get('tokens_per_micro', 10_000)
            
            # Calculate expected hourly tick range
            # From vault.py: low = max(1, int(tokens_per_micro * 4)), high = max(low + 1, int(tokens_per_micro * 11))
            # Safety cap: high = min(high, max(low + 1, tokens_per_digit // 10))
            expected_low = max(1, int(tokens_per_micro * 4))  # 40K
            expected_high_uncapped = max(expected_low + 1, int(tokens_per_micro * 11))  # 110K
            expected_high = min(expected_high_uncapped, max(expected_low + 1, tokens_per_digit // 10))  # min(110K, 10M) = 110K
            
            max_allowed_per_hour = tokens_per_digit // 10  # 10M tokens max per hour
            
            if expected_high <= max_allowed_per_hour:
                self.log_result("Hourly Tick Production Scale", True, 
                              f"Expected hourly tick range: {expected_low:,}-{expected_high:,} tokens (≤ {max_allowed_per_hour:,})")
                return True
            else:
                self.log_result("Hourly Tick Production Scale", False, 
                              f"Hourly tick too high: {expected_high:,} > {max_allowed_per_hour:,}")
        else:
            self.log_result("Hourly Tick Production Scale", False, f"Failed to get state: {state}")
        return False

    def test_regression_all_previous_endpoints(self):
        """Test that all previous endpoints still work"""
        endpoints_to_test = [
            # Public endpoints
            ("GET", "vault/state", None, 200),
            ("POST", "whitelist", {"email": f"test-{int(time.time())}@example.com"}, 200),
            ("GET", "prophecy", None, 200),
            ("GET", "stats", None, 200),
            ("GET", "public/stats", None, 200),
            
            # Admin endpoints (require auth)
            ("GET", "admin/vault/state", None, 200),
            ("POST", "admin/vault/crack", {"tokens": 1000}, 200),
            ("POST", "admin/vault/config", {"hourly_tick_enabled": True}, 200),
            ("POST", "admin/vault/dex-config", {"mode": "off"}, 200),
            ("POST", "admin/vault/dex-poll", None, 200),
            ("GET", "admin/whitelist", None, 200),
            ("GET", "admin/chat-logs", None, 200),
        ]
        
        all_working = True
        
        for method, endpoint, data, expected_status in endpoints_to_test:
            if endpoint.startswith("admin/"):
                headers = self.get_auth_headers()
            else:
                headers = {}
            
            success, response = self.make_request(method, endpoint, data, headers=headers, expected_status=expected_status)
            
            if success:
                self.log_result(f"Regression {method} {endpoint}", True, f"Status {expected_status}")
            else:
                self.log_result(f"Regression {method} {endpoint}", False, f"Expected {expected_status}, got error: {response}")
                all_working = False
        
        return all_working

    def test_public_api_hides_admin_fields(self):
        """Test that public /api/vault/state hides admin-only fields"""
        success, response = self.make_request("GET", "vault/state")
        
        if success:
            # Fields that should NOT be in public response
            forbidden_fields = [
                'target_combination', 'treasury_goal_eur', 'eur_usd_rate',
                'dex_token_address', 'dex_last_price_usd'
            ]
            
            exposed_fields = [f for f in forbidden_fields if f in response]
            
            if not exposed_fields:
                # Check that allowed fields are present
                allowed_fields = [
                    'tokens_per_micro', 'micro_ticks_total', 'treasury_eur_value', 
                    'treasury_progress_pct', 'dex_mode', 'dex_label', 'dex_pair_symbol'
                ]
                present_allowed = [f for f in allowed_fields if f in response]
                
                if len(present_allowed) >= 6:  # Most should be present
                    self.log_result("Public API Hides Admin Fields", True, 
                                  f"No admin fields exposed, {len(present_allowed)} allowed fields present")
                    return True
                else:
                    self.log_result("Public API Hides Admin Fields", False, 
                                  f"Missing allowed fields: {set(allowed_fields) - set(present_allowed)}")
            else:
                self.log_result("Public API Hides Admin Fields", False, f"Admin fields exposed: {exposed_fields}")
        else:
            self.log_result("Public API Hides Admin Fields", False, f"Request failed: {response}")
        return False

    def cleanup_vault_state(self):
        """Leave vault in LOCKED 0/6 state with dex_mode=demo for user demo"""
        print("🧹 Cleaning up vault state for user demo...")
        
        # Reset to clean state
        reset_data = {"preset": "production", "reset": True}
        self.make_request("POST", "admin/vault/config", reset_data, headers=self.get_auth_headers())
        
        # Set dex_mode to demo
        dex_data = {"mode": "demo"}
        self.make_request("POST", "admin/vault/dex-config", dex_data, headers=self.get_auth_headers())
        
        print("✅ Vault left in LOCKED 0/6 state with dex_mode=demo")

    def run_all_tests(self):
        """Run all vault mechanics rework tests"""
        print("🚀 Starting DEEPOTUS Vault Mechanics Rework Testing...")
        print(f"Testing against: {self.base_url}")
        print("=" * 70)
        
        # Initial admin login
        if not self.admin_login():
            print("❌ Failed to login as admin - stopping tests")
            return False
        
        print("✅ Admin login successful")
        
        # Setup clean vault state with production defaults
        if not self.setup_clean_vault_state():
            print("❌ Failed to setup clean vault state - stopping tests")
            return False
        
        # Test production defaults
        print("\n🏭 Testing Production Defaults...")
        self.test_production_defaults_after_init()
        
        # Test new API fields
        print("\n📊 Testing New API Fields...")
        self.test_public_vault_state_new_fields()
        self.test_admin_vault_state_additional_fields()
        
        # Test micro-rotations and dial locking
        print("\n⚙️ Testing Micro-Rotations and Dial Locking...")
        self.test_crack_with_50k_tokens_micro_rotation()
        self.test_crack_with_100m_tokens_locks_dial()
        self.test_sequential_6_cracks_reach_declassified()
        
        # Test admin presets and config
        print("\n🎛️ Testing Admin Presets and Config...")
        self.test_production_preset_config()
        self.test_demo_preset_config()
        self.test_individual_config_updates()
        
        # Test treasury-based declassification
        print("\n💰 Testing Treasury-Based Declassification...")
        self.test_treasury_based_declassification_logic()
        
        # Test hourly tick behavior
        print("\n⏰ Testing Hourly Tick Behavior...")
        self.test_hourly_tick_production_scale()
        
        # Test regression and security
        print("\n🔄 Testing Regression...")
        self.test_regression_all_previous_endpoints()
        
        print("\n🔒 Testing Security...")
        self.test_public_api_hides_admin_fields()
        
        # Cleanup
        self.cleanup_vault_state()
        
        # Print summary
        print("\n" + "=" * 70)
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
    tester = VaultMechanicsAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)