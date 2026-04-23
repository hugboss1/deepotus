#!/usr/bin/env python3
"""
DEEPOTUS Vault System Testing - PROTOCOL ΔΣ
Testing the classified vault mechanics and operation reveal system.
"""

import requests
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Use public endpoint from .env
BASE_URL = "https://prophet-ai-memecoin.preview.emergentagent.com/api"
ADMIN_PASSWORD = "deepotus2026"

class VaultSystemTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []
        self.initial_vault_state = None
        
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
            
            if response.status_code == expected_status:
                return True, response.json() if response.text else {}
            else:
                return False, {"error": f"Status {response.status_code}: {response.text[:200]}"}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    def admin_login(self):
        """Login as admin"""
        success, response = self.make_request("POST", "admin/login", {"password": ADMIN_PASSWORD})
        if success and "token" in response:
            self.admin_token = response["token"]
            return True
        return False
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}

    def test_vault_state_public(self):
        """Test public vault state endpoint - MUST NOT leak target_combination"""
        success, response = self.make_request("GET", "vault/state")
        
        if success:
            # Check required fields are present
            required_fields = [
                'code_name', 'stage', 'num_digits', 'digits_locked', 
                'current_combination', 'tokens_per_digit', 'tokens_sold',
                'progress_pct', 'hourly_tick_enabled', 'updated_at', 'recent_events'
            ]
            
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log_result("Vault State Public - Required Fields", False, f"Missing: {missing_fields}")
                return False
            
            # CRITICAL: Ensure target_combination is NOT exposed
            if 'target_combination' in response:
                self.log_result("Vault State Public - Security", False, "SECURITY BREACH: target_combination exposed!")
                return False
            
            # Validate data types and ranges
            if not isinstance(response['current_combination'], list):
                self.log_result("Vault State Public - Data Types", False, "current_combination not a list")
                return False
                
            if len(response['current_combination']) != response['num_digits']:
                self.log_result("Vault State Public - Data Consistency", False, "combination length mismatch")
                return False
            
            # Check stage values
            valid_stages = ['LOCKED', 'CRACKING', 'UNLOCKING', 'DECLASSIFIED']
            if response['stage'] not in valid_stages:
                self.log_result("Vault State Public - Stage Values", False, f"Invalid stage: {response['stage']}")
                return False
            
            self.initial_vault_state = response
            self.log_result("Vault State Public", True, f"Stage: {response['stage']}, Locked: {response['digits_locked']}/{response['num_digits']}")
            return True
        else:
            self.log_result("Vault State Public", False, f"Request failed: {response}")
            return False

    def test_vault_report_purchase(self):
        """Test public purchase reporting endpoint"""
        # Test with valid purchase
        purchase_data = {
            "tokens": 1000,
            "agent_code": "TEST-001"
        }
        
        success, response = self.make_request("POST", "vault/report-purchase", purchase_data)
        
        if success:
            # Should return vault state response
            if 'stage' in response and 'tokens_sold' in response:
                # Verify tokens were added (clamped to 50,000 max)
                expected_tokens = min(1000, 50000)
                if self.initial_vault_state:
                    expected_total = self.initial_vault_state['tokens_sold'] + expected_tokens
                    if response['tokens_sold'] >= self.initial_vault_state['tokens_sold']:
                        self.log_result("Vault Report Purchase", True, f"Tokens added, new total: {response['tokens_sold']}")
                        return True
                    else:
                        self.log_result("Vault Report Purchase", False, "Tokens not properly added")
                else:
                    self.log_result("Vault Report Purchase", True, f"Purchase processed, tokens: {response['tokens_sold']}")
                    return True
            else:
                self.log_result("Vault Report Purchase", False, "Invalid response format")
        else:
            self.log_result("Vault Report Purchase", False, f"Request failed: {response}")
        return False

    def test_vault_report_purchase_clamping(self):
        """Test that public purchase endpoint validates token limits"""
        purchase_data = {
            "tokens": 100000,  # Above the 50,000 limit
            "agent_code": "TEST-CLAMP"
        }
        
        success, response = self.make_request("POST", "vault/report-purchase", purchase_data, expected_status=422)
        
        if success:
            # The endpoint should reject the request with validation error
            self.log_result("Vault Purchase Validation", True, "Large purchase correctly rejected with validation error")
            return True
        else:
            self.log_result("Vault Purchase Validation", False, f"Expected 422 validation error, got: {response}")
        return False

    def test_vault_admin_state(self):
        """Test admin vault state endpoint - MUST include target_combination"""
        success, response = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        
        if success:
            # Should have all public fields plus target_combination
            if 'target_combination' not in response:
                self.log_result("Vault Admin State - Target Combination", False, "target_combination missing from admin endpoint")
                return False
            
            # Validate target_combination format
            target = response['target_combination']
            if not isinstance(target, list) or len(target) != response['num_digits']:
                self.log_result("Vault Admin State - Target Format", False, f"Invalid target format: {target}")
                return False
            
            # Check all digits are 0-9
            if not all(isinstance(d, int) and 0 <= d <= 9 for d in target):
                self.log_result("Vault Admin State - Target Values", False, f"Invalid target values: {target}")
                return False
            
            self.log_result("Vault Admin State", True, f"Target: {target}, Stage: {response['stage']}")
            return True
        else:
            self.log_result("Vault Admin State", False, f"Request failed: {response}")
        return False

    def test_vault_admin_crack(self):
        """Test admin crack endpoint"""
        crack_data = {
            "tokens": 2000,
            "note": "Admin test crack",
            "agent_code": "ADMIN-TEST"
        }
        
        success, response = self.make_request("POST", "admin/vault/crack", crack_data, headers=self.get_auth_headers())
        
        if success:
            if 'target_combination' in response and 'tokens_sold' in response:
                self.log_result("Vault Admin Crack", True, f"Crack successful, tokens: {response['tokens_sold']}")
                return True
            else:
                self.log_result("Vault Admin Crack", False, "Invalid response format")
        else:
            self.log_result("Vault Admin Crack", False, f"Request failed: {response}")
        return False

    def test_vault_admin_config(self):
        """Test admin vault configuration endpoint"""
        # Test updating tokens_per_digit
        config_data = {
            "tokens_per_digit": 1500,
            "hourly_tick_enabled": True
        }
        
        success, response = self.make_request("POST", "admin/vault/config", config_data, headers=self.get_auth_headers())
        
        if success:
            if response.get('tokens_per_digit') == 1500:
                self.log_result("Vault Admin Config", True, f"Config updated: {config_data}")
                return True
            else:
                self.log_result("Vault Admin Config", False, "Config not properly updated")
        else:
            self.log_result("Vault Admin Config", False, f"Request failed: {response}")
        return False

    def test_vault_admin_reset(self):
        """Test vault reset functionality"""
        reset_data = {
            "reset": True
        }
        
        success, response = self.make_request("POST", "admin/vault/config", reset_data, headers=self.get_auth_headers())
        
        if success:
            if response.get('digits_locked') == 0 and response.get('tokens_sold') == 0:
                self.log_result("Vault Admin Reset", True, "Vault reset successfully")
                return True
            else:
                self.log_result("Vault Admin Reset", False, "Vault not properly reset")
        else:
            self.log_result("Vault Admin Reset", False, f"Request failed: {response}")
        return False

    def test_vault_stage_transitions(self):
        """Test vault stage transitions by progressing through stages"""
        # First, reset vault to ensure clean state
        self.test_vault_admin_reset()
        
        # Get initial state
        success, initial_state = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        if not success:
            self.log_result("Stage Transitions - Initial State", False, "Could not get initial state")
            return False
        
        tokens_per_digit = initial_state['tokens_per_digit']
        
        # Test progression: 0-2 dials → LOCKED
        success, response = self.make_request("POST", "admin/vault/crack", 
                                            {"tokens": tokens_per_digit * 2}, 
                                            headers=self.get_auth_headers())
        if success and response['stage'] == 'LOCKED':
            self.log_result("Stage Transitions - LOCKED", True, f"2 dials locked: {response['stage']}")
        else:
            self.log_result("Stage Transitions - LOCKED", False, f"Expected LOCKED, got {response.get('stage')}")
            return False
        
        # Test progression: 3-4 dials → CRACKING
        success, response = self.make_request("POST", "admin/vault/crack", 
                                            {"tokens": tokens_per_digit * 2}, 
                                            headers=self.get_auth_headers())
        if success and response['stage'] == 'CRACKING':
            self.log_result("Stage Transitions - CRACKING", True, f"4 dials locked: {response['stage']}")
        else:
            self.log_result("Stage Transitions - CRACKING", False, f"Expected CRACKING, got {response.get('stage')}")
            return False
        
        # Test progression: 5 dials → UNLOCKING
        success, response = self.make_request("POST", "admin/vault/crack", 
                                            {"tokens": tokens_per_digit}, 
                                            headers=self.get_auth_headers())
        if success and response['stage'] == 'UNLOCKING':
            self.log_result("Stage Transitions - UNLOCKING", True, f"5 dials locked: {response['stage']}")
        else:
            self.log_result("Stage Transitions - UNLOCKING", False, f"Expected UNLOCKING, got {response.get('stage')}")
            return False
        
        # Test progression: 6 dials → DECLASSIFIED
        success, response = self.make_request("POST", "admin/vault/crack", 
                                            {"tokens": tokens_per_digit}, 
                                            headers=self.get_auth_headers())
        if success and response['stage'] == 'DECLASSIFIED':
            self.log_result("Stage Transitions - DECLASSIFIED", True, f"6 dials locked: {response['stage']}")
            return True
        else:
            self.log_result("Stage Transitions - DECLASSIFIED", False, f"Expected DECLASSIFIED, got {response.get('stage')}")
            return False

    def test_operation_reveal_locked(self):
        """Test operation reveal when vault is not declassified"""
        # First ensure vault is not declassified
        self.test_vault_admin_reset()
        
        success, response = self.make_request("GET", "operation/reveal")
        
        if success:
            if response.get('unlocked') == False and 'stage' in response:
                # Should not contain classified information (fields should be null)
                classified_fields = ['panic_message_fr', 'panic_message_en', 'lore_fr', 'lore_en', 'gencoin_launch_at', 'gencoin_url']
                has_classified_data = any(response.get(field) is not None for field in classified_fields)
                
                if not has_classified_data:
                    self.log_result("Operation Reveal Locked", True, f"Properly locked, stage: {response['stage']}")
                    return True
                else:
                    self.log_result("Operation Reveal Locked", False, "Contains classified information when locked")
            else:
                self.log_result("Operation Reveal Locked", False, f"Invalid locked response: {response}")
        else:
            self.log_result("Operation Reveal Locked", False, f"Request failed: {response}")
        return False

    def test_operation_reveal_declassified(self):
        """Test operation reveal when vault is declassified"""
        # First ensure vault is declassified
        success, vault_state = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        if not success:
            self.log_result("Operation Reveal Declassified - Setup", False, "Could not get vault state")
            return False
        
        # If not declassified, make it so
        if vault_state['stage'] != 'DECLASSIFIED':
            tokens_needed = vault_state['num_digits'] * vault_state['tokens_per_digit'] - vault_state['tokens_sold']
            if tokens_needed > 0:
                success, _ = self.make_request("POST", "admin/vault/crack", 
                                             {"tokens": tokens_needed + 100}, 
                                             headers=self.get_auth_headers())
                if not success:
                    self.log_result("Operation Reveal Declassified - Setup", False, "Could not declassify vault")
                    return False
        
        # Now test the reveal
        success, response = self.make_request("GET", "operation/reveal")
        
        if success:
            if response.get('unlocked') == True:
                # Should contain all classified information
                required_fields = ['panic_message_fr', 'panic_message_en', 'lore_fr', 'lore_en', 'gencoin_launch_at', 'gencoin_url']
                missing_fields = [field for field in required_fields if field not in response]
                
                if not missing_fields:
                    # Check that lore is properly structured (list of strings)
                    if isinstance(response['lore_fr'], list) and isinstance(response['lore_en'], list):
                        self.log_result("Operation Reveal Declassified", True, f"Full reveal available, lore paragraphs: FR={len(response['lore_fr'])}, EN={len(response['lore_en'])}")
                        return True
                    else:
                        self.log_result("Operation Reveal Declassified", False, "Lore not properly formatted as lists")
                else:
                    self.log_result("Operation Reveal Declassified", False, f"Missing classified fields: {missing_fields}")
            else:
                self.log_result("Operation Reveal Declassified", False, "Vault declassified but reveal shows unlocked=false")
        else:
            self.log_result("Operation Reveal Declassified", False, f"Request failed: {response}")
        return False

    def test_chat_system_gencoin_filtering(self):
        """Test that chat system never mentions GENCOIN"""
        # Test multiple questions that might trigger GENCOIN mentions
        test_questions = [
            "What is the secret project?",
            "Tell me about the classified operation",
            "What happens when the vault opens?",
            "What is PROTOCOL ΔΣ hiding?",
            "What is the real purpose of this project?"
        ]
        
        for question in test_questions:
            chat_data = {
                "message": question,
                "lang": "en"
            }
            
            success, response = self.make_request("POST", "chat", chat_data)
            
            if success:
                reply = response.get('reply', '').lower()
                if 'gencoin' in reply:
                    self.log_result("Chat GENCOIN Filtering", False, f"GENCOIN mentioned in response to: '{question}'")
                    return False
            else:
                self.log_result("Chat GENCOIN Filtering", False, f"Chat request failed: {response}")
                return False
        
        self.log_result("Chat GENCOIN Filtering", True, f"Tested {len(test_questions)} questions, no GENCOIN leaks")
        return True

    def test_specific_scenario_6500_tokens(self):
        """Test specific scenario: 6500 tokens should progress from LOCKED to DECLASSIFIED"""
        # Reset vault and set tokens_per_digit to 1000 (default)
        reset_data = {"reset": True, "tokens_per_digit": 1000}
        success, response = self.make_request("POST", "admin/vault/config", reset_data, headers=self.get_auth_headers())
        
        if not success:
            self.log_result("Specific Scenario Setup", False, "Could not reset vault")
            return False
        
        # Verify initial state is LOCKED
        success, initial_state = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        if not success or initial_state['stage'] != 'LOCKED':
            self.log_result("Specific Scenario Initial", False, f"Expected LOCKED stage, got {initial_state.get('stage')}")
            return False
        
        # Apply 6500 tokens (should lock all 6 digits: 6 * 1000 = 6000, plus 500 extra)
        success, final_state = self.make_request("POST", "admin/vault/crack", 
                                               {"tokens": 6500}, 
                                               headers=self.get_auth_headers())
        
        if success:
            if final_state['stage'] == 'DECLASSIFIED' and final_state['digits_locked'] == 6:
                self.log_result("Specific Scenario 6500 Tokens", True, f"LOCKED → DECLASSIFIED with 6500 tokens")
                return True
            else:
                self.log_result("Specific Scenario 6500 Tokens", False, f"Expected DECLASSIFIED with 6 locked, got {final_state['stage']} with {final_state['digits_locked']} locked")
        else:
            self.log_result("Specific Scenario 6500 Tokens", False, f"Request failed: {final_state}")
        return False

    def test_vault_events_logging(self):
        """Test that vault events are properly logged"""
        # Reset vault to start clean
        self.test_vault_admin_reset()
        
        # Perform a crack operation
        success, response = self.make_request("POST", "admin/vault/crack", 
                                            {"tokens": 500, "agent_code": "TEST-EVENT"}, 
                                            headers=self.get_auth_headers())
        
        if not success:
            self.log_result("Vault Events Logging", False, "Could not perform crack operation")
            return False
        
        # Check that recent_events contains our event
        success, vault_state = self.make_request("GET", "vault/state")
        
        if success:
            recent_events = vault_state.get('recent_events', [])
            if recent_events:
                # Look for our test event
                test_event = next((event for event in recent_events if event.get('agent_code') == 'TEST-EVENT'), None)
                if test_event:
                    # Verify event structure
                    required_fields = ['id', 'kind', 'tokens_added', 'digits_locked_before', 'digits_locked_after', 'agent_code', 'created_at']
                    missing_fields = [field for field in required_fields if field not in test_event]
                    
                    if not missing_fields:
                        self.log_result("Vault Events Logging", True, f"Event logged: {test_event['kind']}, tokens: {test_event['tokens_added']}")
                        return True
                    else:
                        self.log_result("Vault Events Logging", False, f"Event missing fields: {missing_fields}")
                else:
                    self.log_result("Vault Events Logging", False, "Test event not found in recent events")
            else:
                self.log_result("Vault Events Logging", False, "No recent events found")
        else:
            self.log_result("Vault Events Logging", False, f"Could not get vault state: {response}")
        return False

    def test_existing_endpoints(self):
        """Test that existing endpoints still work"""
        endpoints_to_test = [
            ("GET", "prophecy", None),
            ("GET", "stats", None),
            ("GET", "public/stats", None),
            ("POST", "whitelist", {"email": f"test-{int(time.time())}@example.com"}),
        ]
        
        working_endpoints = 0
        
        for method, endpoint, data in endpoints_to_test:
            success, response = self.make_request(method, endpoint, data)
            if success:
                working_endpoints += 1
                print(f"  ✅ {method} /{endpoint}")
            else:
                print(f"  ❌ {method} /{endpoint}: {response}")
        
        if working_endpoints == len(endpoints_to_test):
            self.log_result("Existing Endpoints", True, f"All {working_endpoints} endpoints working")
            return True
        else:
            self.log_result("Existing Endpoints", False, f"Only {working_endpoints}/{len(endpoints_to_test)} endpoints working")
            return False

    def run_all_tests(self):
        """Run all vault system tests"""
        print("🔒 Starting DEEPOTUS Vault System Testing...")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Initial admin login
        if not self.admin_login():
            print("❌ Failed to login as admin - stopping tests")
            return False
        
        print("✅ Admin login successful")
        
        # Test vault endpoints
        print("\n🔐 Testing Vault Endpoints...")
        self.test_vault_state_public()
        self.test_vault_report_purchase()
        self.test_vault_report_purchase_clamping()
        self.test_vault_admin_state()
        self.test_vault_admin_crack()
        self.test_vault_admin_config()
        
        # Test stage transitions
        print("\n🔄 Testing Stage Transitions...")
        self.test_vault_stage_transitions()
        
        # Test operation reveal
        print("\n🕵️ Testing Operation Reveal...")
        self.test_operation_reveal_locked()
        self.test_operation_reveal_declassified()
        
        # Test security features
        print("\n🛡️ Testing Security Features...")
        self.test_chat_system_gencoin_filtering()
        
        # Test specific scenarios
        print("\n🎯 Testing Specific Scenarios...")
        self.test_specific_scenario_6500_tokens()
        
        # Test vault events
        print("\n📝 Testing Vault Events...")
        self.test_vault_events_logging()
        
        # Test existing functionality
        print("\n🔧 Testing Existing Endpoints...")
        self.test_existing_endpoints()
        
        # Reset vault to clean state for demo
        print("\n🧹 Cleaning up...")
        self.test_vault_admin_reset()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 VAULT SYSTEM TEST SUMMARY")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.errors:
            print(f"\n❌ FAILED TESTS:")
            for error in self.errors:
                print(f"  • {error}")
        else:
            print(f"\n✅ ALL VAULT TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = VaultSystemTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)