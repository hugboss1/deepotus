#!/usr/bin/env python3
"""
Backend API Testing for DEEPOTUS Proof of Intelligence Flow
Tests the infiltration endpoints that power the riddles terminal.
"""

import requests
import sys
import time
import random
import string
from datetime import datetime

# Base58 alphabet for Solana wallet generation
BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

class ProofOfIntelligenceAPITester:
    def __init__(self, base_url="https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.unique_suffix = int(time.time())
        
    def generate_unique_email(self):
        """Generate unique email for testing (using @example.com as required)"""
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        return f"agent-{timestamp}-{random_num}@example.com"
    
    def generate_unique_wallet(self):
        """Generate unique base58 wallet address (32-44 chars)"""
        length = random.randint(32, 44)
        return ''.join(random.choices(BASE58_ALPHABET, k=length))
    
    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
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

    def test_riddles_list(self):
        """Test fetching riddles list"""
        success, response = self.run_test(
            "List Riddles (FR)",
            "GET", 
            "infiltration/riddles?locale=fr",
            200
        )
        
        if success and response.get('items'):
            print(f"   Found {len(response['items'])} riddles")
            return response['items']
        return []

    def test_riddles_list_en(self):
        """Test fetching riddles list in English"""
        success, response = self.run_test(
            "List Riddles (EN)",
            "GET", 
            "infiltration/riddles?locale=en", 
            200
        )
        return success

    def test_riddle_attempt_correct(self, riddle_slug, email):
        """Test submitting correct answer to first riddle"""
        # Known correct answer for first riddle
        correct_answers = {
            "grand-architecte": "la fed",
            "oeil-invisible": "algorithme", 
            "contrat-social": "banques",
            "verite-de-lagent": "deepotus",
            "ouverture-du-coffre": "produit"
        }
        
        answer = correct_answers.get(riddle_slug, "la fed")
        
        success, response = self.run_test(
            f"Submit Correct Answer ({riddle_slug})",
            "POST",
            f"infiltration/riddles/{riddle_slug}/attempt",
            200,
            data={
                "answer": answer,
                "email": email,
                "locale": "fr"
            }
        )
        
        if success and response.get('correct'):
            print(f"   ✅ Correct answer accepted: {response.get('matched_keyword')}")
            return True
        return False

    def test_riddle_attempt_wrong(self, riddle_slug, email):
        """Test submitting wrong answer"""
        success, response = self.run_test(
            f"Submit Wrong Answer ({riddle_slug})",
            "POST",
            f"infiltration/riddles/{riddle_slug}/attempt", 
            200,
            data={
                "answer": "wrong answer",
                "email": email,
                "locale": "fr"
            }
        )
        
        if success and not response.get('correct'):
            print(f"   ✅ Wrong answer correctly rejected")
            return True
        return False

    def test_clearance_status(self, email):
        """Test getting clearance status"""
        success, response = self.run_test(
            "Get Clearance Status",
            "GET",
            f"infiltration/clearance/{email}",
            200
        )
        
        if success:
            level = response.get('level', 0)
            riddles_solved = response.get('riddles_solved', [])
            print(f"   Level: {level}, Riddles solved: {len(riddles_solved)}")
            return response
        return {}

    def test_link_wallet_valid(self, email, wallet):
        """Test linking valid wallet"""
        success, response = self.run_test(
            "Link Valid Wallet",
            "POST",
            "infiltration/clearance/link-wallet",
            200,
            data={
                "email": email,
                "wallet_address": wallet
            }
        )
        
        if success and response.get('wallet_address') == wallet:
            print(f"   ✅ Wallet linked successfully")
            return True
        return False

    def test_link_wallet_invalid(self, email):
        """Test linking invalid wallet (should fail client-side validation)"""
        success, response = self.run_test(
            "Link Invalid Wallet",
            "POST", 
            "infiltration/clearance/link-wallet",
            400,  # Should return 400 for invalid wallet
            data={
                "email": email,
                "wallet_address": "abc"  # Too short
            }
        )
        
        if success:
            print(f"   ✅ Invalid wallet correctly rejected")
            return True
        return False

    def test_link_wallet_already_linked(self, email1, email2, wallet):
        """Test linking wallet that's already linked to another agent"""
        # First link wallet to email1
        self.test_link_wallet_valid(email1, wallet)
        
        # Try to link same wallet to email2 (should fail)
        success, response = self.run_test(
            "Link Already Linked Wallet",
            "POST",
            "infiltration/clearance/link-wallet", 
            400,  # Should return 400 for already linked wallet
            data={
                "email": email2,
                "wallet_address": wallet
            }
        )
        
        if success:
            print(f"   ✅ Already linked wallet correctly rejected")
            return True
        return False

    def test_vault_status(self):
        """Test vault classified status"""
        success, response = self.run_test(
            "Vault Classified Status",
            "GET",
            "vault/classified-status",
            200
        )
        
        if success:
            sealed = response.get('sealed', False)
            print(f"   Vault sealed: {sealed}")
            return response
        return {}

def main():
    print("🚀 Starting DEEPOTUS Proof of Intelligence API Tests")
    print("=" * 60)
    
    tester = ProofOfIntelligenceAPITester()
    
    # Generate unique test data
    email1 = tester.generate_unique_email()
    email2 = tester.generate_unique_email()
    wallet1 = tester.generate_unique_wallet()
    wallet2 = tester.generate_unique_wallet()
    
    print(f"Test email 1: {email1}")
    print(f"Test email 2: {email2}")
    print(f"Test wallet 1: {wallet1}")
    print(f"Test wallet 2: {wallet2}")
    
    # Test vault status first
    vault_status = tester.test_vault_status()
    
    # Test riddles listing
    riddles = tester.test_riddles_list()
    tester.test_riddles_list_en()
    
    if not riddles:
        print("❌ No riddles found, cannot continue with riddle tests")
        return 1
    
    first_riddle = riddles[0]
    riddle_slug = first_riddle.get('slug')
    
    if not riddle_slug:
        print("❌ No riddle slug found, cannot continue")
        return 1
    
    print(f"\nTesting with riddle: {riddle_slug}")
    
    # Test wrong answer first
    tester.test_riddle_attempt_wrong(riddle_slug, email1)
    
    # Test correct answer
    if tester.test_riddle_attempt_correct(riddle_slug, email1):
        # Check clearance status after correct answer
        clearance = tester.test_clearance_status(email1)
        
        if clearance.get('level') >= 3:
            print("✅ Level 3 clearance achieved!")
            
            # Test wallet linking
            tester.test_link_wallet_valid(email1, wallet1)
            tester.test_link_wallet_invalid(email1)
            tester.test_link_wallet_already_linked(email1, email2, wallet1)
        else:
            print("❌ Level 3 clearance not achieved after correct answer")
    
    # Test clearance status for both emails
    tester.test_clearance_status(email1)
    tester.test_clearance_status(email2)
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())