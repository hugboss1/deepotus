#!/usr/bin/env python3
"""
Backend testing for Phase 2 (Prophet Studio LLM) + Phase 6 (Admin Dashboard) bot fleet functionality.
Tests all bot-related endpoints and functionality.
"""

import requests
import json
import sys
import time
from datetime import datetime

class BotFleetTester:
    def __init__(self, base_url="https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
        if self.admin_token:
            test_headers['Authorization'] = f'Bearer {self.admin_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, {}

    def admin_login(self):
        """Login as admin to get JWT token"""
        print("\n🔐 Admin Login...")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "api/admin/login",
            200,
            data={"password": "deepotus2026"}
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"✅ Admin token obtained")
            return True
        print(f"❌ Admin login failed")
        return False

    def test_bot_config_endpoints(self):
        """Test bot configuration endpoints"""
        print("\n📋 Testing Bot Configuration Endpoints...")
        
        # GET /api/admin/bots/config
        success, config = self.run_test(
            "GET /api/admin/bots/config",
            "GET",
            "api/admin/bots/config",
            200
        )
        
        if success:
            # Verify config has required fields
            required_fields = ['kill_switch_active', 'platforms', 'content_modes', 'llm']
            for field in required_fields:
                if field not in config:
                    print(f"❌ Missing required field: {field}")
                    self.failed_tests.append(f"Config missing field: {field}")
                else:
                    print(f"✅ Config has {field}")
            
            # Verify LLM block is present
            if 'llm' in config and 'provider' in config['llm'] and 'model' in config['llm']:
                print(f"✅ LLM config present: {config['llm']['provider']}/{config['llm']['model']}")
            else:
                print(f"❌ LLM config incomplete")
                self.failed_tests.append("LLM config incomplete")

        return success, config

    def test_content_types_endpoint(self):
        """Test content types endpoint"""
        print("\n📝 Testing Content Types Endpoint...")
        
        success, content_types = self.run_test(
            "GET /api/admin/bots/content-types",
            "GET",
            "api/admin/bots/content-types",
            200
        )
        
        if success:
            expected_types = ['prophecy', 'market_commentary', 'vault_update', 'kol_reply']
            found_types = [ct.get('id') for ct in content_types if isinstance(ct, dict)]
            
            for expected in expected_types:
                if expected in found_types:
                    print(f"✅ Found content type: {expected}")
                else:
                    print(f"❌ Missing content type: {expected}")
                    self.failed_tests.append(f"Missing content type: {expected}")
            
            # Check for FR/EN labels
            for ct in content_types:
                if isinstance(ct, dict):
                    if 'label_fr' in ct and 'label_en' in ct:
                        print(f"✅ Content type {ct.get('id')} has FR/EN labels")
                    else:
                        print(f"❌ Content type {ct.get('id')} missing FR/EN labels")
                        self.failed_tests.append(f"Content type {ct.get('id')} missing labels")

        return success

    def test_generate_preview_endpoints(self):
        """Test content generation preview endpoints"""
        print("\n🎭 Testing Content Generation Preview...")
        
        # Test prophecy generation
        success, prophecy = self.run_test(
            "POST /api/admin/bots/generate-preview (prophecy)",
            "POST",
            "api/admin/bots/generate-preview",
            200,
            data={
                "content_type": "prophecy",
                "platform": "x"
            }
        )
        
        if success:
            required_fields = ['content_fr', 'content_en', 'hashtags', 'char_budget']
            for field in required_fields:
                if field in prophecy:
                    print(f"✅ Prophecy has {field}")
                    if field == 'char_budget' and prophecy[field] == 270:
                        print(f"✅ Correct char budget for X: {prophecy[field]}")
                else:
                    print(f"❌ Prophecy missing {field}")
                    self.failed_tests.append(f"Prophecy missing {field}")

        # Test kol_reply without kol_post (should fail)
        success_fail, _ = self.run_test(
            "POST /api/admin/bots/generate-preview (kol_reply without kol_post)",
            "POST",
            "api/admin/bots/generate-preview",
            400,
            data={
                "content_type": "kol_reply",
                "platform": "x"
            }
        )
        
        if success_fail:
            print("✅ Correctly rejected kol_reply without kol_post")
        
        # Test kol_reply with kol_post
        success, kol_reply = self.run_test(
            "POST /api/admin/bots/generate-preview (kol_reply with kol_post)",
            "POST",
            "api/admin/bots/generate-preview",
            200,
            data={
                "content_type": "kol_reply",
                "platform": "x",
                "kol_post": "SOL to $500 soon"
            }
        )
        
        if success:
            print("✅ Successfully generated kol_reply with kol_post")

        return success

    def test_config_updates(self):
        """Test configuration update endpoints"""
        print("\n⚙️ Testing Configuration Updates...")
        
        # Test LLM provider change to OpenAI
        success, updated_config = self.run_test(
            "PUT /api/admin/bots/config (change to OpenAI GPT-4o)",
            "PUT",
            "api/admin/bots/config",
            200,
            data={
                "llm": {
                    "provider": "openai",
                    "model": "gpt-4o"
                }
            }
        )
        
        if success:
            if updated_config.get('llm', {}).get('provider') == 'openai' and updated_config.get('llm', {}).get('model') == 'gpt-4o':
                print("✅ LLM config updated to OpenAI GPT-4o")
            else:
                print("❌ LLM config not properly updated")
                self.failed_tests.append("LLM config update failed")
        
        # Revert to Claude Sonnet 4.5
        success, reverted_config = self.run_test(
            "PUT /api/admin/bots/config (revert to Claude Sonnet 4.5)",
            "PUT",
            "api/admin/bots/config",
            200,
            data={
                "llm": {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-5-20250929"
                }
            }
        )
        
        if success:
            if reverted_config.get('llm', {}).get('provider') == 'anthropic':
                print("✅ LLM config reverted to Claude Sonnet 4.5")
            else:
                print("❌ LLM config revert failed")
                self.failed_tests.append("LLM config revert failed")

        return success

    def test_kill_switch(self):
        """Test kill switch functionality"""
        print("\n🔴 Testing Kill Switch...")
        
        # Test activating kill switch
        success, activated = self.run_test(
            "POST /api/admin/bots/kill-switch (activate)",
            "POST",
            "api/admin/bots/kill-switch",
            200,
            data={"active": True}
        )
        
        if success:
            if activated.get('kill_switch_active') == True:
                print("✅ Kill switch activated")
            else:
                print("❌ Kill switch not activated")
                self.failed_tests.append("Kill switch activation failed")
        
        # Test deactivating kill switch
        success, deactivated = self.run_test(
            "POST /api/admin/bots/kill-switch (deactivate)",
            "POST",
            "api/admin/bots/kill-switch",
            200,
            data={"active": False}
        )
        
        if success:
            if deactivated.get('kill_switch_active') == False:
                print("✅ Kill switch deactivated")
            else:
                print("❌ Kill switch not deactivated")
                self.failed_tests.append("Kill switch deactivation failed")

        return success

    def test_jobs_endpoint(self):
        """Test jobs endpoint"""
        print("\n⏰ Testing Jobs Endpoint...")
        
        success, jobs = self.run_test(
            "GET /api/admin/bots/jobs",
            "GET",
            "api/admin/bots/jobs",
            200
        )
        
        if success:
            if isinstance(jobs, list) and len(jobs) >= 1:
                print(f"✅ Found {len(jobs)} job(s)")
                # Look for heartbeat job
                heartbeat_found = any(job.get('id') == 'heartbeat' for job in jobs)
                if heartbeat_found:
                    print("✅ Heartbeat job found")
                    # Check if it has next_run_time
                    heartbeat_job = next(job for job in jobs if job.get('id') == 'heartbeat')
                    if heartbeat_job.get('next_run_time'):
                        print("✅ Heartbeat job has next_run_time")
                    else:
                        print("❌ Heartbeat job missing next_run_time")
                        self.failed_tests.append("Heartbeat job missing next_run_time")
                else:
                    print("❌ Heartbeat job not found")
                    self.failed_tests.append("Heartbeat job not found")
            else:
                print("❌ No jobs found")
                self.failed_tests.append("No jobs found")

        return success

    def test_posts_endpoint(self):
        """Test posts endpoint"""
        print("\n📊 Testing Posts Endpoint...")
        
        success, posts = self.run_test(
            "GET /api/admin/bots/posts",
            "GET",
            "api/admin/bots/posts",
            200
        )
        
        if success:
            required_fields = ['items', 'total', 'limit', 'skip', 'status_counts']
            for field in required_fields:
                if field in posts:
                    print(f"✅ Posts response has {field}")
                else:
                    print(f"❌ Posts response missing {field}")
                    self.failed_tests.append(f"Posts response missing {field}")
            
            # Check status counts histogram
            if 'status_counts' in posts and isinstance(posts['status_counts'], dict):
                print(f"✅ Status counts: {posts['status_counts']}")
            else:
                print("❌ Status counts not properly formatted")
                self.failed_tests.append("Status counts not properly formatted")

        return success

    def test_admin_auth_required(self):
        """Test that admin auth is required for all bot endpoints"""
        print("\n🔒 Testing Admin Auth Requirements...")
        
        # Save current token
        saved_token = self.admin_token
        self.admin_token = None
        
        endpoints_to_test = [
            "api/admin/bots/config",
            "api/admin/bots/content-types",
            "api/admin/bots/jobs",
            "api/admin/bots/posts"
        ]
        
        auth_tests_passed = 0
        for endpoint in endpoints_to_test:
            success, _ = self.run_test(
                f"Auth required for {endpoint}",
                "GET",
                endpoint,
                401  # Should return 401 without auth
            )
            if success:
                auth_tests_passed += 1
        
        # Restore token
        self.admin_token = saved_token
        
        if auth_tests_passed == len(endpoints_to_test):
            print(f"✅ All {len(endpoints_to_test)} endpoints properly require auth")
        else:
            print(f"❌ Only {auth_tests_passed}/{len(endpoints_to_test)} endpoints require auth")
            self.failed_tests.append(f"Auth not required for all endpoints")

        return auth_tests_passed == len(endpoints_to_test)

    def test_regression_endpoints(self):
        """Test that existing endpoints still work"""
        print("\n🔄 Testing Regression - Existing Endpoints...")
        
        # Test existing prophet chat
        success_chat, _ = self.run_test(
            "POST /api/chat (regression)",
            "POST",
            "api/chat",
            200,
            data={
                "message": "Hello Prophet",
                "session_id": "test-session-123"
            }
        )
        
        # Test stats endpoint
        success_stats, _ = self.run_test(
            "GET /api/stats (regression)",
            "GET",
            "api/stats",
            200
        )
        
        # Test vault state
        success_vault, _ = self.run_test(
            "GET /api/vault/state (regression)",
            "GET",
            "api/vault/state",
            200
        )
        
        # Test prophecy endpoint
        success_prophecy, _ = self.run_test(
            "GET /api/prophecy (regression)",
            "GET",
            "api/prophecy",
            200
        )
        
        # Test helius webhook
        success_webhook, _ = self.run_test(
            "POST /api/webhooks/helius (regression)",
            "POST",
            "api/webhooks/helius",
            200,
            data={"test": "data"}
        )
        
        regression_tests = [success_chat, success_stats, success_vault, success_prophecy, success_webhook]
        passed_regression = sum(regression_tests)
        
        print(f"✅ Regression tests: {passed_regression}/5 passed")
        
        return passed_regression >= 4  # Allow one failure

def main():
    print("🤖 Starting Bot Fleet Backend Testing...")
    print("=" * 60)
    
    tester = BotFleetTester()
    
    # Admin login first
    if not tester.admin_login():
        print("❌ Cannot proceed without admin access")
        return 1
    
    # Run all tests
    test_results = []
    
    test_results.append(tester.test_bot_config_endpoints())
    test_results.append(tester.test_content_types_endpoint())
    test_results.append(tester.test_generate_preview_endpoints())
    test_results.append(tester.test_config_updates())
    test_results.append(tester.test_kill_switch())
    test_results.append(tester.test_jobs_endpoint())
    test_results.append(tester.test_posts_endpoint())
    test_results.append(tester.test_admin_auth_required())
    test_results.append(tester.test_regression_endpoints())
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 BACKEND TEST RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ Failed tests:")
        for failure in tester.failed_tests:
            print(f"   - {failure}")
    
    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "failed_tests": tester.failed_tests,
        "success_rate": f"{(tester.tests_passed/tester.tests_run)*100:.1f}%"
    }
    
    with open("/tmp/bot_backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())