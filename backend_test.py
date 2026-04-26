#!/usr/bin/env python3
"""
Backend regression test for DEEPOTUS admin endpoints.
Tests the code quality review changes to ensure no functionality was broken.
"""

import requests
import sys
import json
from datetime import datetime

class DeepotusAdminTester:
    def __init__(self, base_url="https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_password = "deepotus2026"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login and get token"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "api/admin/login",
            200,
            data={"password": self.admin_password}
        )
        if success and isinstance(response, dict) and 'token' in response:
            self.token = response['token']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_bots_config_get(self):
        """Test GET /api/admin/bots/config"""
        success, response = self.run_test(
            "Get Bots Config",
            "GET",
            "api/admin/bots/config",
            200
        )
        if success and isinstance(response, dict):
            # Verify expected structure
            required_keys = ['loyalty', 'news_repost', 'kill_switch_active']
            for key in required_keys:
                if key not in response:
                    print(f"   ❌ Missing key: {key}")
                    return False
            
            # Check loyalty sub-document
            loyalty = response.get('loyalty', {})
            if not isinstance(loyalty, dict):
                print(f"   ❌ loyalty is not a dict: {type(loyalty)}")
                return False
            
            # Check news_repost sub-document  
            news_repost = response.get('news_repost', {})
            if not isinstance(news_repost, dict):
                print(f"   ❌ news_repost is not a dict: {type(news_repost)}")
                return False
                
            print(f"   ✅ Config structure valid")
            print(f"   loyalty.hints_enabled: {loyalty.get('hints_enabled')}")
            print(f"   news_repost.enabled_for: {news_repost.get('enabled_for')}")
            return True
        return False

    def test_bots_config_patch_loyalty(self):
        """Test PUT /api/admin/bots/config with loyalty patch"""
        success, response = self.run_test(
            "Patch Loyalty Config",
            "PUT",
            "api/admin/bots/config",
            200,
            data={"loyalty": {"hints_enabled": True}}
        )
        if success and isinstance(response, dict):
            loyalty = response.get('loyalty', {})
            if loyalty.get('hints_enabled') == True:
                print(f"   ✅ loyalty.hints_enabled updated to True")
                return True
            else:
                print(f"   ❌ loyalty.hints_enabled not updated: {loyalty.get('hints_enabled')}")
        return False

    def test_bots_config_patch_news_repost(self):
        """Test PUT /api/admin/bots/config with news_repost patch"""
        success, response = self.run_test(
            "Patch News Repost Config",
            "PUT", 
            "api/admin/bots/config",
            200,
            data={
                "news_repost": {
                    "enabled_for": {"telegram": True},
                    "interval_minutes": 15
                }
            }
        )
        if success and isinstance(response, dict):
            news_repost = response.get('news_repost', {})
            enabled_for = news_repost.get('enabled_for', {})
            interval_minutes = news_repost.get('interval_minutes')
            
            if enabled_for.get('telegram') == True and interval_minutes == 15:
                print(f"   ✅ news_repost config updated correctly")
                return True
            else:
                print(f"   ❌ news_repost not updated correctly")
                print(f"      telegram: {enabled_for.get('telegram')}, interval: {interval_minutes}")
        return False

    def test_news_repost_status(self):
        """Test GET /api/admin/bots/news-repost/status"""
        success, response = self.run_test(
            "Get News Repost Status",
            "GET",
            "api/admin/bots/news-repost/status",
            200
        )
        if success and isinstance(response, dict):
            required_keys = ['config', 'queue_preview']
            for key in required_keys:
                if key not in response:
                    print(f"   ❌ Missing key: {key}")
                    return False
            
            queue_preview = response.get('queue_preview', {})
            if isinstance(queue_preview, dict):
                for platform in ['x', 'telegram']:
                    if platform in queue_preview:
                        items = queue_preview[platform]
                        print(f"   ✅ {platform} queue has {len(items)} items")
                return True
        return False

    def test_news_repost_test_send(self):
        """Test POST /api/admin/bots/news-repost/test-send"""
        success, response = self.run_test(
            "Test News Repost Send",
            "POST",
            "api/admin/bots/news-repost/test-send",
            200,
            data={"platform": "telegram", "lang": "fr"}
        )
        if success and isinstance(response, dict):
            status = response.get('status')
            preview_text = response.get('preview_text')
            
            if status in ['dry_run', 'sent'] and preview_text:
                print(f"   ✅ Test send status: {status}")
                print(f"   Preview: {preview_text[:50]}...")
                return True
            else:
                print(f"   ❌ Unexpected response: status={status}, preview={bool(preview_text)}")
        return False

    def test_loyalty_endpoints(self):
        """Test loyalty endpoints"""
        # Test GET /api/admin/bots/loyalty
        success, response = self.run_test(
            "Get Loyalty Status",
            "GET",
            "api/admin/bots/loyalty",
            200
        )
        if not success:
            return False
            
        # Test GET /api/admin/bots/loyalty/email-stats
        success, response = self.run_test(
            "Get Loyalty Email Stats",
            "GET", 
            "api/admin/bots/loyalty/email-stats",
            200
        )
        if success and isinstance(response, dict):
            required_keys = ['total_sent', 'pending_now']
            for key in required_keys:
                if key not in response:
                    print(f"   ❌ Missing key: {key}")
                    return False
            print(f"   ✅ Email stats: sent={response.get('total_sent')}, pending={response.get('pending_now')}")
            return True
        return False

    def test_loyalty_test_send(self):
        """Test POST /api/admin/bots/loyalty/test-send"""
        success, response = self.run_test(
            "Test Loyalty Email Send",
            "POST",
            "api/admin/bots/loyalty/test-send",
            200,
            data={"email": "qa-test@example.com"}
        )
        if success and isinstance(response, dict):
            status = response.get('status')
            if status in ['sent', 'skipped_no_resend_key']:
                print(f"   ✅ Test send status: {status}")
                return True
            else:
                print(f"   ❌ Unexpected status: {status}")
        return False

    def test_bots_jobs(self):
        """Test GET /api/admin/bots/jobs"""
        success, response = self.run_test(
            "Get Bot Jobs",
            "GET",
            "api/admin/bots/jobs",
            200
        )
        if success and isinstance(response, list):
            expected_jobs = ['heartbeat', 'news_refresh', 'loyalty_email', 'news_repost']
            job_ids = [job.get('id') for job in response]
            
            missing_jobs = [job for job in expected_jobs if job not in job_ids]
            if not missing_jobs:
                print(f"   ✅ All expected jobs found: {job_ids}")
                return True
            else:
                print(f"   ❌ Missing jobs: {missing_jobs}")
                print(f"   Found jobs: {job_ids}")
        return False

    def test_vault_state(self):
        """Test GET /api/vault/state"""
        success, response = self.run_test(
            "Get Vault State",
            "GET",
            "api/vault/state",
            200
        )
        if success and isinstance(response, dict):
            tokens_per_micro = response.get('tokens_per_micro')
            if tokens_per_micro == 100000:
                print(f"   ✅ tokens_per_micro unchanged: {tokens_per_micro}")
                return True
            else:
                print(f"   ❌ tokens_per_micro changed: {tokens_per_micro}")
        return False

def main():
    print("🚀 Starting DEEPOTUS Backend Regression Tests")
    print("=" * 60)
    
    tester = DeepotusAdminTester()
    
    # Test sequence
    tests = [
        ("Admin Login", tester.test_admin_login),
        ("Get Bots Config", tester.test_bots_config_get),
        ("Patch Loyalty Config", tester.test_bots_config_patch_loyalty),
        ("Patch News Repost Config", tester.test_bots_config_patch_news_repost),
        ("Get News Repost Status", tester.test_news_repost_status),
        ("Test News Repost Send", tester.test_news_repost_test_send),
        ("Test Loyalty Endpoints", tester.test_loyalty_endpoints),
        ("Test Loyalty Send", tester.test_loyalty_test_send),
        ("Get Bot Jobs", tester.test_bots_jobs),
        ("Get Vault State", tester.test_vault_state),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                print(f"\n❌ {test_name} FAILED - stopping tests")
                break
        except Exception as e:
            print(f"\n💥 {test_name} CRASHED: {e}")
            break
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED - No regressions detected!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Regressions detected!")
        return 1

if __name__ == "__main__":
    sys.exit(main())