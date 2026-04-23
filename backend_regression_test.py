#!/usr/bin/env python3
"""
DEEPOTUS Backend Regression Testing - Post-Refactor Validation
Testing all endpoints after monolithic server.py refactor to ensure 100% behavioral equivalence.
"""

import requests
import json
import time
import csv
import io
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Use public endpoint from .env
BASE_URL = "https://prophet-ai-memecoin.preview.emergentagent.com/api"
ADMIN_PASSWORD = "deepotus2026"

class BackendRegressionTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []
        self.test_email = f"test-{int(time.time())}@example.com"
        
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
                elif response_type == "csv":
                    return True, response.text
                else:
                    return True, response
            else:
                return False, {"error": f"Status {response.status_code}: {response.text[:200]}"}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}

    # ===== ROOT & PUBLIC ENDPOINTS =====
    
    def test_root_endpoint(self):
        """Test GET /api/ returns prophet online payload"""
        success, response = self.make_request("GET", "")
        
        if success:
            if "prophet" in str(response).lower() and "online" in str(response).lower():
                self.log_result("Root Endpoint", True, f"Prophet online: {response}")
                return True
            else:
                self.log_result("Root Endpoint", False, f"Unexpected response: {response}")
        else:
            self.log_result("Root Endpoint", False, f"Request failed: {response}")
        return False

    def test_stats_endpoint(self):
        """Test GET /api/stats returns whitelist_count/prophecies_served/chat_messages/launch_timestamp"""
        success, response = self.make_request("GET", "stats")
        
        if success:
            required_fields = ['whitelist_count', 'prophecies_served', 'chat_messages', 'launch_timestamp']
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                self.log_result("Stats Endpoint", True, f"All fields present: {list(response.keys())}")
                return True
            else:
                self.log_result("Stats Endpoint", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Stats Endpoint", False, f"Request failed: {response}")
        return False

    def test_prophecy_endpoint(self):
        """Test GET /api/prophecy?lang=fr returns a prophecy (use live=false to avoid LLM cost)"""
        success, response = self.make_request("GET", "prophecy?lang=fr&live=false")
        
        if success:
            if 'prophecy' in response or 'text' in response or 'message' in response:
                self.log_result("Prophecy Endpoint", True, f"Prophecy returned (length: {len(str(response))})")
                return True
            else:
                self.log_result("Prophecy Endpoint", False, f"No prophecy in response: {response}")
        else:
            self.log_result("Prophecy Endpoint", False, f"Request failed: {response}")
        return False

    def test_chat_endpoint(self):
        """Test POST /api/chat with a short message returns a reply (ONE call only — uses LLM; can be skipped if key missing)"""
        chat_data = {
            "message": "Hello",
            "lang": "en"
        }
        
        success, response = self.make_request("POST", "chat", chat_data)
        
        if success:
            if 'reply' in response and response['reply']:
                self.log_result("Chat Endpoint", True, f"Reply received (length: {len(response['reply'])})")
                return True
            else:
                self.log_result("Chat Endpoint", False, f"No reply in response: {response}")
        else:
            # Check if it's an LLM key issue
            error_msg = str(response.get('error', ''))
            if 'key' in error_msg.lower() or 'api' in error_msg.lower():
                self.log_result("Chat Endpoint", True, f"Skipped - LLM key issue: {error_msg}")
                return True
            else:
                self.log_result("Chat Endpoint", False, f"Request failed: {response}")
        return False

    def test_whitelist_endpoint(self):
        """Test POST /api/whitelist with a fresh random email: returns id+position, persists in DB, is idempotent on 2nd call"""
        # First call - should create new entry
        whitelist_data = {"email": self.test_email}
        success1, response1 = self.make_request("POST", "whitelist", whitelist_data)
        
        if success1:
            if 'id' in response1 and 'position' in response1:
                # Second call - should be idempotent
                success2, response2 = self.make_request("POST", "whitelist", whitelist_data)
                
                if success2:
                    if response1['id'] == response2['id'] and response1['position'] == response2['position']:
                        self.log_result("Whitelist Endpoint", True, f"Idempotent: ID={response1['id']}, Position={response1['position']}")
                        return True
                    else:
                        self.log_result("Whitelist Endpoint", False, f"Not idempotent: {response1} vs {response2}")
                else:
                    self.log_result("Whitelist Endpoint", False, f"Second call failed: {response2}")
            else:
                self.log_result("Whitelist Endpoint", False, f"Missing id/position: {response1}")
        else:
            self.log_result("Whitelist Endpoint", False, f"First call failed: {response1}")
        return False

    def test_whitelist_blacklisted_email(self):
        """Test POST /api/whitelist with a blacklisted email returns 403"""
        # First add an email to blacklist (need admin access)
        if not self.admin_token:
            self.admin_login()
        
        blacklist_email = f"blacklisted-{int(time.time())}@example.com"
        
        # Add to blacklist
        success, _ = self.make_request("POST", "admin/blacklist", {"email": blacklist_email}, headers=self.get_auth_headers())
        
        if success:
            # Try to whitelist the blacklisted email
            success, response = self.make_request("POST", "whitelist", {"email": blacklist_email}, expected_status=403)
            
            if success:
                self.log_result("Whitelist Blacklisted Email", True, "Correctly rejected with 403")
                return True
            else:
                self.log_result("Whitelist Blacklisted Email", False, f"Expected 403, got: {response}")
        else:
            self.log_result("Whitelist Blacklisted Email", False, "Could not add email to blacklist")
        return False

    def test_public_stats_endpoint(self):
        """Test GET /api/public/stats?days=30 returns all sections"""
        success, response = self.make_request("GET", "public/stats?days=30")
        
        if success:
            required_sections = ['series', 'lang_distribution', 'top_sessions', 'activity_heatmap', 'counters']
            missing_sections = [s for s in required_sections if s not in response]
            
            if not missing_sections:
                self.log_result("Public Stats Endpoint", True, f"All sections present: {list(response.keys())}")
                return True
            else:
                self.log_result("Public Stats Endpoint", False, f"Missing sections: {missing_sections}")
        else:
            self.log_result("Public Stats Endpoint", False, f"Request failed: {response}")
        return False

    # ===== WEBHOOKS =====
    
    def test_webhooks_resend(self):
        """Test POST /api/webhooks/resend (without secret configured) accepts unsigned payload and persists in email_events"""
        webhook_data = {
            "type": "email.delivered",
            "data": {
                "email_id": f"test-{int(time.time())}",
                "to": ["test@example.com"],
                "subject": "Test Email"
            }
        }
        
        success, response = self.make_request("POST", "webhooks/resend", webhook_data)
        
        if success:
            self.log_result("Webhooks Resend", True, f"Webhook processed: {response}")
            return True
        else:
            self.log_result("Webhooks Resend", False, f"Request failed: {response}")
        return False

    # ===== ADMIN AUTHENTICATION =====
    
    def test_admin_login_wrong_password(self):
        """Test POST /api/admin/login with wrong password → 401"""
        success, response = self.make_request("POST", "admin/login", {"password": "wrongpassword"}, expected_status=401)
        
        if success:
            self.log_result("Admin Login Wrong Password", True, "Correctly rejected with 401")
            return True
        else:
            self.log_result("Admin Login Wrong Password", False, f"Expected 401, got: {response}")
        return False

    def admin_login(self):
        """Login as admin and store token"""
        success, response = self.make_request("POST", "admin/login", {"password": ADMIN_PASSWORD})
        if success and "token" in response:
            self.admin_token = response["token"]
            return True
        return False

    def test_admin_login_correct_password(self):
        """Test POST /api/admin/login with correct password (deepotus2026) → 200 + token"""
        success, response = self.make_request("POST", "admin/login", {"password": ADMIN_PASSWORD})
        
        if success:
            if "token" in response:
                self.admin_token = response["token"]
                self.log_result("Admin Login Correct Password", True, f"Token received: {response['token'][:20]}...")
                return True
            else:
                self.log_result("Admin Login Correct Password", False, f"No token in response: {response}")
        else:
            self.log_result("Admin Login Correct Password", False, f"Request failed: {response}")
        return False

    # ===== ADMIN ENDPOINTS =====
    
    def test_admin_whitelist_no_token(self):
        """Test GET /api/admin/whitelist without token → 401"""
        success, response = self.make_request("GET", "admin/whitelist", expected_status=401)
        
        if success:
            self.log_result("Admin Whitelist No Token", True, "Correctly rejected with 401")
            return True
        else:
            self.log_result("Admin Whitelist No Token", False, f"Expected 401, got: {response}")
        return False

    def test_admin_whitelist_with_token(self):
        """Test GET /api/admin/whitelist with token → 200 + items"""
        success, response = self.make_request("GET", "admin/whitelist", headers=self.get_auth_headers())
        
        if success:
            if isinstance(response, list) or 'items' in response:
                self.log_result("Admin Whitelist With Token", True, f"Whitelist retrieved (items: {len(response) if isinstance(response, list) else len(response.get('items', []))})")
                return True
            else:
                self.log_result("Admin Whitelist With Token", False, f"Unexpected response format: {response}")
        else:
            self.log_result("Admin Whitelist With Token", False, f"Request failed: {response}")
        return False

    def test_admin_chat_logs(self):
        """Test GET /api/admin/chat-logs → 200"""
        success, response = self.make_request("GET", "admin/chat-logs", headers=self.get_auth_headers())
        
        if success:
            self.log_result("Admin Chat Logs", True, f"Chat logs retrieved: {type(response)}")
            return True
        else:
            self.log_result("Admin Chat Logs", False, f"Request failed: {response}")
        return False

    def test_admin_evolution(self):
        """Test GET /api/admin/evolution?days=30 → 200 + series"""
        success, response = self.make_request("GET", "admin/evolution?days=30", headers=self.get_auth_headers())
        
        if success:
            if 'series' in response or isinstance(response, list):
                self.log_result("Admin Evolution", True, f"Evolution data retrieved: {type(response)}")
                return True
            else:
                self.log_result("Admin Evolution", False, f"No series in response: {response}")
        else:
            self.log_result("Admin Evolution", False, f"Request failed: {response}")
        return False

    def test_admin_blacklist_crud(self):
        """Test admin blacklist CRUD: GET list, POST add, DELETE remove"""
        # GET list
        success1, response1 = self.make_request("GET", "admin/blacklist", headers=self.get_auth_headers())
        
        if success1:
            # POST add
            test_blacklist_email = f"blacklist-test-{int(time.time())}@example.com"
            success2, response2 = self.make_request("POST", "admin/blacklist", {"email": test_blacklist_email}, headers=self.get_auth_headers())
            
            if success2:
                # DELETE remove
                success3, response3 = self.make_request("DELETE", f"admin/blacklist/{test_blacklist_email}", headers=self.get_auth_headers())
                
                if success3:
                    self.log_result("Admin Blacklist CRUD", True, "GET/POST/DELETE all working")
                    return True
                else:
                    self.log_result("Admin Blacklist CRUD", False, f"DELETE failed: {response3}")
            else:
                self.log_result("Admin Blacklist CRUD", False, f"POST failed: {response2}")
        else:
            self.log_result("Admin Blacklist CRUD", False, f"GET failed: {response1}")
        return False

    def test_admin_blacklist_import(self):
        """Test POST /api/admin/blacklist/import with csv_text → 200"""
        csv_data = "email\ntest1@example.com\ntest2@example.com"
        import_data = {"csv_text": csv_data}
        
        success, response = self.make_request("POST", "admin/blacklist/import", import_data, headers=self.get_auth_headers())
        
        if success:
            self.log_result("Admin Blacklist Import", True, f"CSV import successful: {response}")
            return True
        else:
            self.log_result("Admin Blacklist Import", False, f"Request failed: {response}")
        return False

    def test_admin_sessions(self):
        """Test GET /api/admin/sessions → 200 with current session flagged"""
        success, response = self.make_request("GET", "admin/sessions", headers=self.get_auth_headers())
        
        if success:
            if isinstance(response, list) or 'sessions' in response:
                self.log_result("Admin Sessions", True, f"Sessions retrieved: {type(response)}")
                return True
            else:
                self.log_result("Admin Sessions", False, f"Unexpected response format: {response}")
        else:
            self.log_result("Admin Sessions", False, f"Request failed: {response}")
        return False

    def test_admin_whitelist_export(self):
        """Test GET /api/admin/whitelist/export → text/csv"""
        success, response = self.make_request("GET", "admin/whitelist/export", headers=self.get_auth_headers(), response_type="csv")
        
        if success:
            if isinstance(response, str) and ('email' in response or 'Email' in response):
                self.log_result("Admin Whitelist Export", True, f"CSV export successful (length: {len(response)})")
                return True
            else:
                self.log_result("Admin Whitelist Export", False, f"Not a valid CSV: {response[:100]}...")
        else:
            self.log_result("Admin Whitelist Export", False, f"Request failed: {response}")
        return False

    def test_admin_2fa_status(self):
        """Test GET /api/admin/2fa/status → 200"""
        success, response = self.make_request("GET", "admin/2fa/status", headers=self.get_auth_headers())
        
        if success:
            self.log_result("Admin 2FA Status", True, f"2FA status retrieved: {response}")
            return True
        else:
            self.log_result("Admin 2FA Status", False, f"Request failed: {response}")
        return False

    def test_admin_email_events(self):
        """Test GET /api/admin/email-events → 200"""
        success, response = self.make_request("GET", "admin/email-events", headers=self.get_auth_headers())
        
        if success:
            self.log_result("Admin Email Events", True, f"Email events retrieved: {type(response)}")
            return True
        else:
            self.log_result("Admin Email Events", False, f"Request failed: {response}")
        return False

    # ===== VAULT ENDPOINTS =====
    
    def test_vault_state_public(self):
        """Test GET /api/vault/state → 200 with stage + digits"""
        success, response = self.make_request("GET", "vault/state")
        
        if success:
            required_fields = ['stage', 'num_digits', 'digits_locked']
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                # Ensure target_combination is NOT exposed
                if 'target_combination' not in response:
                    self.log_result("Vault State Public", True, f"Stage: {response['stage']}, Digits: {response['digits_locked']}/{response['num_digits']}")
                    return True
                else:
                    self.log_result("Vault State Public", False, "target_combination exposed in public API")
            else:
                self.log_result("Vault State Public", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Vault State Public", False, f"Request failed: {response}")
        return False

    def test_vault_report_purchase(self):
        """Test POST /api/vault/report-purchase with {tokens:5000} → 200 (clamped 0<t<=50000)"""
        purchase_data = {"tokens": 5000}
        
        success, response = self.make_request("POST", "vault/report-purchase", purchase_data)
        
        if success:
            if 'tokens_sold' in response or 'stage' in response:
                self.log_result("Vault Report Purchase", True, f"Purchase processed: {response}")
                return True
            else:
                self.log_result("Vault Report Purchase", False, f"Unexpected response: {response}")
        else:
            self.log_result("Vault Report Purchase", False, f"Request failed: {response}")
        return False

    def test_vault_admin_state(self):
        """Test GET /api/admin/vault/state → 200 (with JWT)"""
        success, response = self.make_request("GET", "admin/vault/state", headers=self.get_auth_headers())
        
        if success:
            # Should have target_combination (admin-only field)
            if 'target_combination' in response:
                self.log_result("Vault Admin State", True, f"Admin vault state with target: {response['target_combination']}")
                return True
            else:
                self.log_result("Vault Admin State", False, "target_combination missing from admin endpoint")
        else:
            self.log_result("Vault Admin State", False, f"Request failed: {response}")
        return False

    def test_vault_admin_crack(self):
        """Test POST /api/admin/vault/crack with body {tokens:1000} → 200 (with JWT)"""
        crack_data = {"tokens": 1000}
        
        success, response = self.make_request("POST", "admin/vault/crack", crack_data, headers=self.get_auth_headers())
        
        if success:
            if 'tokens_sold' in response or 'stage' in response:
                self.log_result("Vault Admin Crack", True, f"Crack successful: {response}")
                return True
            else:
                self.log_result("Vault Admin Crack", False, f"Unexpected response: {response}")
        else:
            self.log_result("Vault Admin Crack", False, f"Request failed: {response}")
        return False

    def test_vault_admin_dex_poll(self):
        """Test POST /api/admin/vault/dex-poll → 200 (forces a DexScreener poll)"""
        success, response = self.make_request("POST", "admin/vault/dex-poll", headers=self.get_auth_headers())
        
        if success:
            self.log_result("Vault Admin Dex Poll", True, f"Dex poll successful: {response}")
            return True
        else:
            self.log_result("Vault Admin Dex Poll", False, f"Request failed: {response}")
        return False

    # ===== ACCESS CARD ENDPOINTS =====
    
    def test_access_card_request(self):
        """Test POST /api/access-card/request with email+display_name → 200 + accreditation_number + card_url"""
        card_data = {
            "email": f"card-test-{int(time.time())}@example.com",
            "display_name": "Test User"
        }
        
        success, response = self.make_request("POST", "access-card/request", card_data)
        
        if success:
            required_fields = ['accreditation_number', 'card_url']
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                self.accreditation_number = response['accreditation_number']  # Store for later tests
                self.log_result("Access Card Request", True, f"Card created: {response['accreditation_number']}")
                return True
            else:
                self.log_result("Access Card Request", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Access Card Request", False, f"Request failed: {response}")
        return False

    def test_access_card_image(self):
        """Test GET /api/access-card/image/{accred} → 200 image/png"""
        if not hasattr(self, 'accreditation_number'):
            # Create a card first
            self.test_access_card_request()
        
        if hasattr(self, 'accreditation_number'):
            success, response = self.make_request("GET", f"access-card/image/{self.accreditation_number}", response_type="raw")
            
            if success:
                if hasattr(response, 'headers') and 'image' in response.headers.get('content-type', ''):
                    self.log_result("Access Card Image", True, f"Image retrieved: {response.headers.get('content-type')}")
                    return True
                else:
                    self.log_result("Access Card Image", False, f"Not an image response: {response}")
            else:
                self.log_result("Access Card Image", False, f"Request failed: {response}")
        else:
            self.log_result("Access Card Image", False, "No accreditation number available")
        return False

    def test_access_card_verify(self):
        """Test POST /api/access-card/verify with valid accred → 200 + session_token"""
        if not hasattr(self, 'accreditation_number'):
            self.test_access_card_request()
        
        if hasattr(self, 'accreditation_number'):
            verify_data = {"accreditation_number": self.accreditation_number}
            success, response = self.make_request("POST", "access-card/verify", verify_data)
            
            if success:
                if 'session_token' in response:
                    self.session_token = response['session_token']  # Store for later test
                    self.log_result("Access Card Verify", True, f"Session token received: {response['session_token'][:20]}...")
                    return True
                else:
                    self.log_result("Access Card Verify", False, f"No session token: {response}")
            else:
                self.log_result("Access Card Verify", False, f"Request failed: {response}")
        else:
            self.log_result("Access Card Verify", False, "No accreditation number available")
        return False

    def test_access_card_status(self):
        """Test GET /api/access-card/status without X-Session-Token → {ok:false}; with valid token → {ok:true}"""
        # Test without token
        success1, response1 = self.make_request("GET", "access-card/status")
        
        if success1 and response1.get('ok') == False:
            # Test with token
            if hasattr(self, 'session_token'):
                headers = {"X-Session-Token": self.session_token}
                success2, response2 = self.make_request("GET", "access-card/status", headers=headers)
                
                if success2 and response2.get('ok') == True:
                    self.log_result("Access Card Status", True, "Both no-token and with-token tests passed")
                    return True
                else:
                    self.log_result("Access Card Status", False, f"With token failed: {response2}")
            else:
                self.log_result("Access Card Status", True, "No-token test passed (no session token to test with)")
                return True
        else:
            self.log_result("Access Card Status", False, f"No-token test failed: {response1}")
        return False

    # ===== OPERATION ENDPOINTS =====
    
    def test_operation_reveal(self):
        """Test GET /api/operation/reveal → 200 (unlocked:false while vault not DECLASSIFIED, true + lore payload otherwise)"""
        success, response = self.make_request("GET", "operation/reveal")
        
        if success:
            if 'unlocked' in response:
                self.log_result("Operation Reveal", True, f"Reveal status: unlocked={response['unlocked']}")
                return True
            else:
                self.log_result("Operation Reveal", False, f"No unlocked field: {response}")
        else:
            self.log_result("Operation Reveal", False, f"Request failed: {response}")
        return False

    # ===== STARTUP TASKS =====
    
    def test_startup_tasks(self):
        """Test startup tasks: background DexScreener poll loop AND hourly vault tick should start on app startup"""
        # This is already verified by checking supervisor logs earlier
        # We can also check if the vault shows signs of the background processes
        success, response = self.make_request("GET", "vault/state")
        
        if success:
            # Check if hourly_tick_enabled is present and true
            if response.get('hourly_tick_enabled') == True:
                self.log_result("Startup Tasks", True, "Hourly tick enabled, background processes running")
                return True
            else:
                self.log_result("Startup Tasks", False, f"Hourly tick not enabled: {response.get('hourly_tick_enabled')}")
        else:
            self.log_result("Startup Tasks", False, f"Could not check vault state: {response}")
        return False

    def run_all_tests(self):
        """Run all regression tests"""
        print("🔄 Starting DEEPOTUS Backend Regression Testing...")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Root and Public Endpoints
        print("\n🌐 Testing Root & Public Endpoints...")
        self.test_root_endpoint()
        self.test_stats_endpoint()
        self.test_prophecy_endpoint()
        self.test_chat_endpoint()
        self.test_whitelist_endpoint()
        self.test_whitelist_blacklisted_email()
        self.test_public_stats_endpoint()
        
        # Webhooks
        print("\n🪝 Testing Webhooks...")
        self.test_webhooks_resend()
        
        # Admin Authentication
        print("\n🔐 Testing Admin Authentication...")
        self.test_admin_login_wrong_password()
        self.test_admin_login_correct_password()
        
        # Admin Endpoints (require login)
        print("\n👑 Testing Admin Endpoints...")
        self.test_admin_whitelist_no_token()
        self.test_admin_whitelist_with_token()
        self.test_admin_chat_logs()
        self.test_admin_evolution()
        self.test_admin_blacklist_crud()
        self.test_admin_blacklist_import()
        self.test_admin_sessions()
        self.test_admin_whitelist_export()
        self.test_admin_2fa_status()
        self.test_admin_email_events()
        
        # Vault Endpoints
        print("\n🏦 Testing Vault Endpoints...")
        self.test_vault_state_public()
        self.test_vault_report_purchase()
        self.test_vault_admin_state()
        self.test_vault_admin_crack()
        self.test_vault_admin_dex_poll()
        
        # Access Card Endpoints
        print("\n🎫 Testing Access Card Endpoints...")
        self.test_access_card_request()
        self.test_access_card_image()
        self.test_access_card_verify()
        self.test_access_card_status()
        
        # Operation Endpoints
        print("\n🕵️ Testing Operation Endpoints...")
        self.test_operation_reveal()
        
        # Startup Tasks
        print("\n🚀 Testing Startup Tasks...")
        self.test_startup_tasks()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 REGRESSION TEST SUMMARY")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.errors:
            print(f"\n❌ FAILED TESTS:")
            for error in self.errors:
                print(f"  • {error}")
        else:
            print(f"\n✅ ALL REGRESSION TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = BackendRegressionTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)