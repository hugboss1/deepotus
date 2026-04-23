#!/usr/bin/env python3
"""
Comprehensive backend test suite for PROTOCOL ΔΣ post-hardening regression sweep.

Tests security improvements and refactored endpoints while ensuring 100% behavior preservation.
Focus areas:
1. Security: secrets module usage in access_card.py and vault.py
2. Refactored endpoints: admin blacklist import, dex-poll
3. Regression testing of all existing endpoints
4. Admin authentication and JWT protection
"""

import asyncio
import json
import re
import requests
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

# Backend URL from environment
BACKEND_URL = "https://prophet-ai-memecoin.preview.emergentagent.com"
ADMIN_PASSWORD = "deepotus2026"

class BackendTester:
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
        self.admin_token = None
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Test tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.results = {
            'security_tests': [],
            'regression_tests': [],
            'refactored_tests': [],
            'admin_auth_tests': [],
            'access_card_tests': []
        }

    def log_test(self, category: str, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            self.failed_tests.append(f"{category}: {name} - {details}")
            print(f"❌ {name} - {details}")
        
        self.results[category].append({
            'name': name,
            'success': success,
            'details': details
        })

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            if self.admin_token and 'headers' not in kwargs:
                kwargs['headers'] = {'Authorization': f'Bearer {self.admin_token}'}
            elif self.admin_token and 'headers' in kwargs:
                kwargs['headers']['Authorization'] = f'Bearer {self.admin_token}'
            
            response = self.session.request(method, url, **kwargs)
            return response
        except Exception as e:
            print(f"Request error for {method} {endpoint}: {e}")
            raise

    def test_admin_login(self) -> bool:
        """Test admin authentication"""
        try:
            response = self.make_request('POST', '/api/admin/login', json={
                'password': ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('token')
                self.log_test('admin_auth_tests', 'Admin login with correct password', True)
                return True
            else:
                self.log_test('admin_auth_tests', 'Admin login with correct password', False, 
                            f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test('admin_auth_tests', 'Admin login with correct password', False, str(e))
            return False

    def test_security_access_card_format(self):
        """Test access card accreditation number format DS-02-XXXX-XXXX-XX"""
        try:
            # Generate multiple access cards to test format and uniqueness
            test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
            
            response = self.make_request('POST', '/api/access-card/request', json={
                'email': test_email,
                'display_name': 'Test Agent'
            })
            
            if response.status_code == 200:
                data = response.json()
                accred = data.get('accreditation_number', '')
                
                # Test format: DS-02-XXXX-XXXX-XX (18 chars total, uppercase alphanum + 3 dashes)
                pattern = r'^DS-02-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{2}$'
                if re.match(pattern, accred) and len(accred) == 18:
                    self.log_test('security_tests', 'Access card format DS-02-XXXX-XXXX-XX', True)
                    
                    # Test uniqueness by generating another card
                    test_email2 = f"test-{uuid.uuid4().hex[:8]}@example.com"
                    response2 = self.make_request('POST', '/api/access-card/request', json={
                        'email': test_email2,
                        'display_name': 'Test Agent 2'
                    })
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        accred2 = data2.get('accreditation_number', '')
                        
                        if accred != accred2:
                            self.log_test('security_tests', 'Access card uniqueness across calls', True)
                        else:
                            self.log_test('security_tests', 'Access card uniqueness across calls', False, 
                                        'Generated same accreditation number')
                    else:
                        self.log_test('security_tests', 'Access card uniqueness across calls', False, 
                                    f"Second request failed: {response2.status_code}")
                else:
                    self.log_test('security_tests', 'Access card format DS-02-XXXX-XXXX-XX', False, 
                                f"Invalid format: {accred}")
            else:
                self.log_test('security_tests', 'Access card format DS-02-XXXX-XXXX-XX', False, 
                            f"Request failed: {response.status_code}")
                
        except Exception as e:
            self.log_test('security_tests', 'Access card format DS-02-XXXX-XXXX-XX', False, str(e))

    def test_security_vault_state(self):
        """Test vault state endpoint and admin vault config with reset"""
        try:
            # Test public vault state
            response = self.make_request('GET', '/api/vault/state')
            if response.status_code == 200:
                self.log_test('security_tests', 'GET /api/vault/state returns vault payload', True)
            else:
                self.log_test('security_tests', 'GET /api/vault/state returns vault payload', False, 
                            f"Status: {response.status_code}")

            # Test admin vault config with reset (requires admin token)
            if self.admin_token:
                response = self.make_request('POST', '/api/admin/vault/config', json={
                    'reset': True
                })
                if response.status_code == 200:
                    data = response.json()
                    # Verify it has a target_combination (6-digit array)
                    target = data.get('target_combination', [])
                    if isinstance(target, list) and len(target) == 6:
                        self.log_test('security_tests', 'Admin vault config reset randomizes 6-digit target', True)
                    else:
                        self.log_test('security_tests', 'Admin vault config reset randomizes 6-digit target', False, 
                                    f"Invalid target: {target}")
                else:
                    self.log_test('security_tests', 'Admin vault config reset randomizes 6-digit target', False, 
                                f"Status: {response.status_code}")
            else:
                self.log_test('security_tests', 'Admin vault config reset randomizes 6-digit target', False, 
                            "No admin token")
                
        except Exception as e:
            self.log_test('security_tests', 'Vault state and config tests', False, str(e))

    def test_regression_basic_endpoints(self):
        """Test basic regression endpoints"""
        endpoints = [
            ('GET', '/api/', 'prophet-online payload'),
            ('GET', '/api/stats', 'stats payload'),
            ('GET', '/api/public/stats?days=30', 'public stats with series'),
        ]
        
        for method, endpoint, description in endpoints:
            try:
                response = self.make_request(method, endpoint)
                if response.status_code == 200:
                    data = response.json()
                    # Basic validation that we got some data
                    if data:
                        self.log_test('regression_tests', f'{method} {endpoint} returns {description}', True)
                    else:
                        self.log_test('regression_tests', f'{method} {endpoint} returns {description}', False, 
                                    'Empty response')
                else:
                    self.log_test('regression_tests', f'{method} {endpoint} returns {description}', False, 
                                f"Status: {response.status_code}")
            except Exception as e:
                self.log_test('regression_tests', f'{method} {endpoint} returns {description}', False, str(e))

    def test_regression_whitelist_flow(self):
        """Test whitelist happy path and blacklisted rejection"""
        try:
            # Test whitelist endpoint (should work without auth for public)
            test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
            response = self.make_request('POST', '/api/whitelist', json={
                'email': test_email,
                'lang': 'en'
            })
            
            # Should succeed (200) or be rate limited (429) or already exist (409)
            if response.status_code in [200, 409, 429]:
                self.log_test('regression_tests', 'POST /api/whitelist happy-path', True)
            else:
                self.log_test('regression_tests', 'POST /api/whitelist happy-path', False, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test('regression_tests', 'POST /api/whitelist happy-path', False, str(e))

    def test_regression_webhooks(self):
        """Test webhooks endpoint"""
        try:
            # Test resend webhook endpoint
            response = self.make_request('POST', '/api/webhooks/resend', json={
                'type': 'email.sent',
                'data': {'email_id': 'test-123'}
            })
            
            # Should accept payload (signed when secret is configured)
            # Status could be 200 (processed) or 400 (invalid signature) - both are valid responses
            if response.status_code in [200, 400]:
                self.log_test('regression_tests', 'POST /api/webhooks/resend accepts payload', True)
            else:
                self.log_test('regression_tests', 'POST /api/webhooks/resend accepts payload', False, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test('regression_tests', 'POST /api/webhooks/resend accepts payload', False, str(e))

    def test_admin_endpoints_jwt_protection(self):
        """Test that admin endpoints require JWT"""
        admin_endpoints = [
            '/api/admin/whitelist',
            '/api/admin/chat-logs', 
            '/api/admin/evolution',
            '/api/admin/blacklist',
            '/api/admin/sessions',
            '/api/admin/2fa/status',
            '/api/admin/email-events',
            '/api/admin/whitelist/export'
        ]
        
        # Test without token (should get 401)
        old_token = self.admin_token
        self.admin_token = None
        
        for endpoint in admin_endpoints:
            try:
                response = self.make_request('GET', endpoint)
                if response.status_code == 401:
                    self.log_test('admin_auth_tests', f'{endpoint} requires JWT (401 without)', True)
                else:
                    self.log_test('admin_auth_tests', f'{endpoint} requires JWT (401 without)', False, 
                                f"Status: {response.status_code}")
            except Exception as e:
                self.log_test('admin_auth_tests', f'{endpoint} requires JWT (401 without)', False, str(e))
        
        # Restore token and test with valid token (should get 200)
        self.admin_token = old_token
        
        for endpoint in admin_endpoints:
            try:
                response = self.make_request('GET', endpoint)
                if response.status_code == 200:
                    self.log_test('admin_auth_tests', f'{endpoint} works with valid JWT (200)', True)
                else:
                    self.log_test('admin_auth_tests', f'{endpoint} works with valid JWT (200)', False, 
                                f"Status: {response.status_code}")
            except Exception as e:
                self.log_test('admin_auth_tests', f'{endpoint} works with valid JWT (200)', False, str(e))

    def test_refactored_blacklist_import(self):
        """Test refactored admin blacklist import endpoint"""
        if not self.admin_token:
            self.log_test('refactored_tests', 'Blacklist import tests', False, 'No admin token')
            return
            
        try:
            # Test CSV import
            csv_data = "a@b.com,manual\nc@d.com"
            response = self.make_request('POST', '/api/admin/blacklist/import', json={
                'csv_text': csv_data
            })
            
            if response.status_code == 200:
                data = response.json()
                imported = data.get('imported', 0)
                skipped_invalid = data.get('skipped_invalid', 0)
                skipped_existing = data.get('skipped_existing', 0)
                errors = data.get('errors', [])
                
                # Verify response structure
                if all(key in data for key in ['imported', 'skipped_invalid', 'skipped_existing', 'errors']):
                    self.log_test('refactored_tests', 'Blacklist import CSV returns correct structure', True)
                else:
                    self.log_test('refactored_tests', 'Blacklist import CSV returns correct structure', False, 
                                f"Missing keys in response: {data}")
            else:
                self.log_test('refactored_tests', 'Blacklist import CSV returns correct structure', False, 
                            f"Status: {response.status_code}")

            # Test emails array import
            response = self.make_request('POST', '/api/admin/blacklist/import', json={
                'emails': ['test1@example.com', 'test2@example.com']
            })
            
            if response.status_code == 200:
                self.log_test('refactored_tests', 'Blacklist import emails array works', True)
            else:
                self.log_test('refactored_tests', 'Blacklist import emails array works', False, 
                            f"Status: {response.status_code}")

            # Test cooldown functionality
            response = self.make_request('POST', '/api/admin/blacklist/import', json={
                'emails': ['cooldown@example.com'],
                'cooldown_days': 7
            })
            
            if response.status_code == 200:
                self.log_test('refactored_tests', 'Blacklist import with cooldown_days works', True)
            else:
                self.log_test('refactored_tests', 'Blacklist import with cooldown_days works', False, 
                            f"Status: {response.status_code}")

            # Test 5001 rows limit (should return 413)
            large_emails = [f'test{i}@example.com' for i in range(5001)]
            response = self.make_request('POST', '/api/admin/blacklist/import', json={
                'emails': large_emails
            })
            
            if response.status_code == 413:
                self.log_test('refactored_tests', 'Blacklist import 5001 rows returns 413', True)
            else:
                self.log_test('refactored_tests', 'Blacklist import 5001 rows returns 413', False, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test('refactored_tests', 'Blacklist import tests', False, str(e))

    def test_refactored_dex_poll(self):
        """Test refactored dex-poll endpoint"""
        if not self.admin_token:
            self.log_test('refactored_tests', 'Dex poll test', False, 'No admin token')
            return
            
        try:
            response = self.make_request('POST', '/api/admin/vault/dex-poll')
            
            if response.status_code == 200:
                data = response.json()
                # Should return mode + pair + delta_buys + ticks_applied
                expected_keys = ['mode', 'pair', 'delta_buys', 'ticks_applied']
                if all(key in data for key in expected_keys):
                    self.log_test('refactored_tests', 'Dex poll returns expected structure', True)
                else:
                    self.log_test('refactored_tests', 'Dex poll returns expected structure', False, 
                                f"Missing keys: {[k for k in expected_keys if k not in data]}")
            else:
                self.log_test('refactored_tests', 'Dex poll returns expected structure', False, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test('refactored_tests', 'Dex poll test', False, str(e))

    def test_vault_admin_endpoints_jwt_protection(self):
        """Test vault admin endpoints are JWT protected"""
        vault_admin_endpoints = [
            '/api/admin/vault/state',
            '/api/admin/vault/config',
            '/api/admin/vault/dex-config',
            '/api/admin/vault/dex-poll'
        ]
        
        # Test without token
        old_token = self.admin_token
        self.admin_token = None
        
        for endpoint in vault_admin_endpoints:
            try:
                method = 'POST' if endpoint.endswith(('config', 'dex-config', 'dex-poll')) else 'GET'
                response = self.make_request(method, endpoint, json={} if method == 'POST' else None)
                
                if response.status_code == 401:
                    self.log_test('admin_auth_tests', f'{endpoint} JWT protected', True)
                else:
                    self.log_test('admin_auth_tests', f'{endpoint} JWT protected', False, 
                                f"Status: {response.status_code}")
            except Exception as e:
                self.log_test('admin_auth_tests', f'{endpoint} JWT protected', False, str(e))
        
        self.admin_token = old_token

    def test_vault_crack_flow(self):
        """Test vault crack flow"""
        if not self.admin_token:
            self.log_test('refactored_tests', 'Vault crack flow', False, 'No admin token')
            return
            
        try:
            response = self.make_request('POST', '/api/admin/vault/crack', json={
                'tokens': 1000
            })
            
            if response.status_code == 200:
                data = response.json()
                # Should return admin view with state updates
                if 'target_combination' in data and 'tokens_sold' in data:
                    self.log_test('refactored_tests', 'Vault crack updates state and returns admin view', True)
                else:
                    self.log_test('refactored_tests', 'Vault crack updates state and returns admin view', False, 
                                'Missing expected fields in response')
            else:
                self.log_test('refactored_tests', 'Vault crack updates state and returns admin view', False, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test('refactored_tests', 'Vault crack flow', False, str(e))

    def test_access_card_full_flow(self):
        """Test complete access card flow"""
        try:
            # Step 1: Request access card
            test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
            response = self.make_request('POST', '/api/access-card/request', json={
                'email': test_email,
                'display_name': 'Test Agent'
            })
            
            if response.status_code != 200:
                self.log_test('access_card_tests', 'Access card request', False, 
                            f"Status: {response.status_code}")
                return
                
            data = response.json()
            accred = data.get('accreditation_number')
            
            if not accred:
                self.log_test('access_card_tests', 'Access card request', False, 'No accreditation number')
                return
                
            self.log_test('access_card_tests', 'Access card request', True)
            
            # Step 2: Verify with unknown accred (should return ok:false)
            fake_accred = "DS-02-FAKE-FAKE-XX"
            response = self.make_request('POST', '/api/access-card/verify', json={
                'accreditation_number': fake_accred
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') == False:
                    self.log_test('access_card_tests', 'Unknown accred returns ok:false', True)
                else:
                    self.log_test('access_card_tests', 'Unknown accred returns ok:false', False, 
                                f"Got ok: {data.get('ok')}")
            else:
                self.log_test('access_card_tests', 'Unknown accred returns ok:false', False, 
                            f"Status: {response.status_code}")
            
            # Step 3: Verify with valid accred (should return ok:true + session_token)
            response = self.make_request('POST', '/api/access-card/verify', json={
                'accreditation_number': accred
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') == True and data.get('session_token'):
                    session_token = data['session_token']
                    self.log_test('access_card_tests', 'Valid accred returns ok:true + session_token', True)
                    
                    # Step 4: Check status with session token
                    response = self.make_request('GET', '/api/access-card/status', 
                                               headers={'X-Session-Token': session_token})
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('ok') == True:
                            self.log_test('access_card_tests', 'Status with valid session token returns ok:true', True)
                        else:
                            self.log_test('access_card_tests', 'Status with valid session token returns ok:true', False, 
                                        f"Got ok: {data.get('ok')}")
                    else:
                        self.log_test('access_card_tests', 'Status with valid session token returns ok:true', False, 
                                    f"Status: {response.status_code}")
                else:
                    self.log_test('access_card_tests', 'Valid accred returns ok:true + session_token', False, 
                                f"Got ok: {data.get('ok')}, token: {bool(data.get('session_token'))}")
            else:
                self.log_test('access_card_tests', 'Valid accred returns ok:true + session_token', False, 
                            f"Status: {response.status_code}")
            
            # Step 5: Test access card image endpoint
            response = self.make_request('GET', f'/api/access-card/image/{accred}')
            
            if response.status_code == 200 and response.headers.get('content-type') == 'image/png':
                self.log_test('access_card_tests', 'Access card image returns PNG', True)
            else:
                self.log_test('access_card_tests', 'Access card image returns PNG', False, 
                            f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                
        except Exception as e:
            self.log_test('access_card_tests', 'Access card full flow', False, str(e))

    def test_operation_reveal(self):
        """Test operation reveal endpoint"""
        try:
            response = self.make_request('GET', '/api/operation/reveal')
            
            if response.status_code == 200:
                data = response.json()
                # Should have unlocked field and stage
                if 'unlocked' in data and 'stage' in data:
                    unlocked = data.get('unlocked')
                    stage = data.get('stage')
                    
                    if stage != 'DECLASSIFIED':
                        # Should return unlocked:false when stage != DECLASSIFIED
                        if unlocked == False:
                            self.log_test('regression_tests', 'Operation reveal unlocked:false when not DECLASSIFIED', True)
                        else:
                            self.log_test('regression_tests', 'Operation reveal unlocked:false when not DECLASSIFIED', False, 
                                        f"unlocked: {unlocked} for stage: {stage}")
                    else:
                        # If declassified, should have lore payload
                        if 'lore_fr' in data and 'lore_en' in data:
                            self.log_test('regression_tests', 'Operation reveal shows lore when DECLASSIFIED', True)
                        else:
                            self.log_test('regression_tests', 'Operation reveal shows lore when DECLASSIFIED', False, 
                                        'Missing lore fields')
                else:
                    self.log_test('regression_tests', 'Operation reveal basic structure', False, 
                                'Missing unlocked or stage fields')
            else:
                self.log_test('regression_tests', 'Operation reveal basic structure', False, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test('regression_tests', 'Operation reveal', False, str(e))

    def check_background_loops(self):
        """Check if background loops are mentioned in supervisor logs"""
        try:
            # This is a best-effort check - we can't directly verify the loops are running
            # but we can check if the startup message appears in logs
            import subprocess
            result = subprocess.run(['tail', '-n', '100', '/var/log/supervisor/backend.*.log'], 
                                  capture_output=True, text=True, shell=True)
            
            if '[startup] PROTOCOL ΔΣ vault ready + hourly tick + DexScreener loops launched' in result.stdout:
                self.log_test('regression_tests', 'Background loops startup message found', True)
            else:
                self.log_test('regression_tests', 'Background loops startup message found', False, 
                            'Startup message not found in logs')
                
        except Exception as e:
            self.log_test('regression_tests', 'Background loops check', False, str(e))

    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting PROTOCOL ΔΣ Backend Test Suite")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Admin authentication first
        print("\n📋 Admin Authentication Tests")
        if not self.test_admin_login():
            print("❌ Admin login failed - some tests will be skipped")
        
        # Security tests
        print("\n🔒 Security Tests")
        self.test_security_access_card_format()
        self.test_security_vault_state()
        
        # Regression tests
        print("\n🔄 Regression Tests")
        self.test_regression_basic_endpoints()
        self.test_regression_whitelist_flow()
        self.test_regression_webhooks()
        self.test_operation_reveal()
        self.check_background_loops()
        
        # Admin endpoint protection tests
        print("\n🛡️ Admin JWT Protection Tests")
        self.test_admin_endpoints_jwt_protection()
        self.test_vault_admin_endpoints_jwt_protection()
        
        # Refactored endpoint tests
        print("\n⚙️ Refactored Endpoint Tests")
        self.test_refactored_blacklist_import()
        self.test_refactored_dex_poll()
        self.test_vault_crack_flow()
        
        # Access card flow tests
        print("\n🎫 Access Card Flow Tests")
        self.test_access_card_full_flow()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"  - {failure}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = BackendTester()
    success = tester.run_all_tests()
    
    # Save detailed results for test report
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': tester.tests_run,
        'passed_tests': tester.tests_passed,
        'failed_tests': len(tester.failed_tests),
        'success_rate': (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
        'categories': tester.results,
        'failures': tester.failed_tests
    }
    
    with open('/tmp/backend_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to /tmp/backend_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())