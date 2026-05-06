#!/usr/bin/env python3
"""
Backend API Testing for DEEPOTUS Accreditation Deep-Link Flow
Tests the vault and access-card endpoints used by the #accreditation feature.
"""

import requests
import sys
import time
import random
from datetime import datetime

class AccreditationAPITester:
    def __init__(self, base_url="https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        
    def generate_unique_email(self):
        """Generate unique email for testing"""
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        return f"test-{timestamp}-{random_num}@example.com"
    
    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json', 'Accept-Language': 'fr'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                except:
                    pass
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            return success, response.json() if response.content else {}
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_vault_state(self):
        """Test GET /api/vault/state"""
        success, response = self.run_test(
            "Vault State",
            "GET", 
            "vault/state",
            200
        )
        
        if success:
            stage = response.get('stage', 'UNKNOWN')
            print(f"   Vault stage: {stage}")
            return response
        return {}

    def test_vault_classified_status(self):
        """Test GET /api/vault/classified-status"""
        success, response = self.run_test(
            "Vault Classified Status",
            "GET",
            "vault/classified-status",
            200
        )
        
        if success:
            sealed = response.get('sealed', False)
            mint_live = response.get('mint_live', False)
            print(f"   Sealed: {sealed}, Mint live: {mint_live}")
            return response
        return {}

    def test_whitelist_post(self, email):
        """Test POST /api/whitelist"""
        success, response = self.run_test(
            "Whitelist Subscription",
            "POST",
            "whitelist",
            200,
            data={
                "email": email,
                "lang": "fr"
            }
        )
        
        if success:
            position = response.get('position', 0)
            print(f"   Position: {position}")
            return response
        return {}

    def test_access_card_request(self, email):
        """Test POST /api/access-card/request"""
        success, response = self.run_test(
            "Access Card Request",
            "POST",
            "access-card/request",
            200,
            data={
                "email": email,
                "display_name": "Test Agent"
            }
        )
        
        if success:
            accred_number = response.get('accreditation_number', 'N/A')
            print(f"   Accreditation: {accred_number}")
            return response
        return {}

    def test_access_card_verify(self, accred_number):
        """Test POST /api/access-card/verify"""
        success, response = self.run_test(
            "Access Card Verify",
            "POST",
            "access-card/verify",
            200,
            data={
                "accreditation_number": accred_number
            }
        )
        
        if success:
            ok = response.get('ok', False)
            print(f"   Verification OK: {ok}")
            return response
        return {}

    def test_genesis_broadcast(self, email):
        """Test POST /api/access-card/genesis-broadcast"""
        success, response = self.run_test(
            "Genesis Broadcast Subscription",
            "POST",
            "access-card/genesis-broadcast",
            200,
            data={
                "email": email,
                "display_name": "Test Genesis Agent",
                "lang": "fr"
            }
        )
        
        if success:
            ok = response.get('ok', False)
            position = response.get('position', 0)
            print(f"   OK: {ok}, Position: {position}")
            return response
        return {}

def main():
    print("🚀 Starting DEEPOTUS Accreditation Deep-Link API Tests")
    print("=" * 60)
    
    tester = AccreditationAPITester()
    
    # Generate unique test data
    email1 = tester.generate_unique_email()
    email2 = tester.generate_unique_email()
    email3 = tester.generate_unique_email()
    
    print(f"Test email 1: {email1}")
    print(f"Test email 2: {email2}")
    print(f"Test email 3: {email3}")
    
    # Test vault endpoints
    vault_state = tester.test_vault_state()
    vault_status = tester.test_vault_classified_status()
    
    # Test whitelist endpoint
    whitelist_result = tester.test_whitelist_post(email1)
    
    # Test access card request
    access_card = tester.test_access_card_request(email2)
    
    # If we got an accreditation number, test verification
    if access_card and access_card.get('accreditation_number'):
        accred_number = access_card['accreditation_number']
        tester.test_access_card_verify(accred_number)
    
    # Test genesis broadcast (pre-launch subscription)
    tester.test_genesis_broadcast(email3)
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend API tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
