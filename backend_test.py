"""Sprint 17.5 follow-up — Backend API testing for:
  * POST /api/admin/bots/preview/push (Real Dispatcher enqueue)
  * POST /api/admin/bots/release-now (dual-mode Release button)
  * POST /api/admin/bots/generate-preview (ASGI hardening regression)
  * Regression: Cabinet endpoints (welcome-signal, interaction-bot)
"""

import requests
import sys
from datetime import datetime

# Public endpoint from frontend/.env
BASE_URL = "https://prophet-ai-memecoin.preview.emergentagent.com"
ADMIN_PASSWORD = "deepotus2026"


class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data=None, headers=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        if headers is None:
            headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print(f"   {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            else:
                print(f"❌ Unsupported method: {method}")
                return False, {}

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def admin_login(self):
        """Get admin JWT token"""
        print("\n🔐 Admin Login")
        success, response = self.run_test(
            "Admin login",
            "POST",
            "/api/admin/login",
            200,
            data={"password": ADMIN_PASSWORD}
        )
        if success and 'token' in response:
            self.token = response['token']
            print(f"   Token acquired: {self.token[:20]}...")
            return True
        print("   ❌ Login failed")
        return False


def main():
    tester = APITester(BASE_URL)
    
    print("=" * 70)
    print("Sprint 17.5 Follow-up — Backend API Testing")
    print("=" * 70)
    
    # ---- Admin auth ----
    if not tester.admin_login():
        print("\n❌ Cannot proceed without admin token")
        return 1

    # ---- Test 1: GET /api/admin/bots/config (baseline) ----
    success, config = tester.run_test(
        "Get bot config (baseline)",
        "GET",
        "/api/admin/bots/config",
        200
    )
    if success:
        print(f"   kill_switch_active: {config.get('kill_switch_active')}")
        print(f"   llm: {config.get('llm', {}).get('provider')}/{config.get('llm', {}).get('model')}")

    # ---- Test 2: POST /api/admin/bots/generate-preview (ASGI hardening) ----
    # This should NOT crash even if the LLM returns partial/surplus fields
    success, preview = tester.run_test(
        "Generate preview (ASGI hardening check)",
        "POST",
        "/api/admin/bots/generate-preview",
        200,
        data={
            "content_type": "prophecy",
            "platform": "x",
            "include_image": False,
            "use_news_context": False,
            "use_v2": False
        },
        timeout=45
    )
    if success:
        print(f"   content_fr length: {len(preview.get('content_fr', ''))}")
        print(f"   content_en length: {len(preview.get('content_en', ''))}")
        print(f"   hashtags: {preview.get('hashtags', [])}")
        print(f"   primary_emoji: {preview.get('primary_emoji', '')}")
        # Store for push test
        preview_content_fr = preview.get('content_fr', '')
        preview_content_en = preview.get('content_en', '')
    else:
        # Fallback for push test
        preview_content_fr = "Le Cabinet observe. Les marchés tremblent. #DeepState"
        preview_content_en = "The Cabinet watches. Markets tremble. #DeepState"

    # ---- Test 3: POST /api/admin/bots/generate-preview with V2 ----
    success, preview_v2 = tester.run_test(
        "Generate preview with V2 templates",
        "POST",
        "/api/admin/bots/generate-preview",
        200,
        data={
            "content_type": "prophecy",  # ignored on V2 path
            "platform": "x",
            "include_image": False,
            "use_v2": True,
            "force_template_v2": "lore"
        },
        timeout=45
    )
    if success:
        print(f"   template_used: {preview_v2.get('template_used')}")
        print(f"   template_label: {preview_v2.get('template_label')}")

    # ---- Test 4: POST /api/admin/bots/preview/push (requires non-panic) ----
    # First check propaganda settings
    success, prop_settings = tester.run_test(
        "Get propaganda settings",
        "GET",
        "/api/admin/propaganda/settings",
        200
    )
    
    panic_active = prop_settings.get('panic', False) if success else False
    
    if panic_active:
        print("\n⚠️  Propaganda PANIC is active — skipping push test")
        print("   (The endpoint correctly rejects with 409 when panic=true)")
    else:
        # Test push with minimal payload
        success, push_result = tester.run_test(
            "Push preview to X/Telegram (Real Dispatcher)",
            "POST",
            "/api/admin/bots/preview/push",
            200,
            data={
                "content_fr": preview_content_fr,
                "content_en": preview_content_en,
                "platforms": ["x"],
                "lang": "en"
            }
        )
        if success:
            items = push_result.get('items', [])
            print(f"   items enqueued: {len(items)}")
            for item in items:
                print(f"     - {item.get('platform')}: {item.get('status')} (id={item.get('queue_item_id')})")
            print(f"   dispatch_dry_run: {push_result.get('dispatch_dry_run')}")
            print(f"   rendered_lang: {push_result.get('rendered_lang')}")

    # ---- Test 5: POST /api/admin/bots/preview/push validation (empty platforms) ----
    success, _ = tester.run_test(
        "Push preview with empty platforms (should reject 400)",
        "POST",
        "/api/admin/bots/preview/push",
        400,
        data={
            "content_fr": "test",
            "content_en": "test",
            "platforms": [],
            "lang": "en"
        }
    )

    # ---- Test 6: POST /api/admin/bots/preview/push validation (invalid lang) ----
    success, _ = tester.run_test(
        "Push preview with invalid lang (should reject 422)",
        "POST",
        "/api/admin/bots/preview/push",
        422,
        data={
            "content_fr": "test",
            "content_en": "test",
            "platforms": ["x"],
            "lang": "es"  # not in enum
        }
    )

    # ---- Test 7: POST /api/admin/bots/preview/push without admin auth ----
    # Temporarily clear token
    saved_token = tester.token
    tester.token = None
    success, _ = tester.run_test(
        "Push preview without admin auth (should reject 403)",
        "POST",
        "/api/admin/bots/preview/push",
        403,
        data={
            "content_fr": "test",
            "content_en": "test",
            "platforms": ["x"],
            "lang": "en"
        }
    )
    tester.token = saved_token

    # ---- Test 8: POST /api/admin/bots/release-now (kill-switch OFF path) ----
    # First ensure kill-switch is OFF
    if config.get('kill_switch_active'):
        print("\n⚙️  Releasing kill-switch for release-now test...")
        tester.run_test(
            "Release kill-switch",
            "POST",
            "/api/admin/bots/kill-switch",
            200,
            data={"active": False}
        )
    
    success, release_result = tester.run_test(
        "Release-now (kill-switch OFF — should trigger jobs)",
        "POST",
        "/api/admin/bots/release-now",
        200
    )
    if success:
        triggered = release_result.get('triggered', [])
        skipped = release_result.get('skipped', [])
        print(f"   triggered: {len(triggered)} job(s)")
        for job in triggered[:5]:  # show first 5
            print(f"     - {job.get('id')} at {job.get('forced_at')}")
        print(f"   skipped: {len(skipped)} job(s)")
        print(f"   kill_switch_active: {release_result.get('kill_switch_active')}")

    # ---- Test 9: POST /api/admin/bots/release-now (kill-switch ON path) ----
    print("\n⚙️  Arming kill-switch for release-now test...")
    tester.run_test(
        "Arm kill-switch",
        "POST",
        "/api/admin/bots/kill-switch",
        200,
        data={"active": True}
    )
    
    success, release_result_killed = tester.run_test(
        "Release-now (kill-switch ON — should skip all jobs)",
        "POST",
        "/api/admin/bots/release-now",
        200
    )
    if success:
        triggered = release_result_killed.get('triggered', [])
        skipped = release_result_killed.get('skipped', [])
        print(f"   triggered: {len(triggered)} job(s) (should be 0)")
        print(f"   skipped: {len(skipped)} job(s)")
        if skipped:
            print(f"     - first skip reason: {skipped[0].get('reason')}")
        print(f"   kill_switch_active: {release_result_killed.get('kill_switch_active')}")

    # ---- Test 10: POST /api/admin/bots/release-now without admin auth ----
    saved_token = tester.token
    tester.token = None
    success, _ = tester.run_test(
        "Release-now without admin auth (should reject 403)",
        "POST",
        "/api/admin/bots/release-now",
        403
    )
    tester.token = saved_token

    # ---- Test 11: Regression — Cabinet endpoints ----
    success, welcome_settings = tester.run_test(
        "Regression: GET /api/admin/propaganda/welcome-signal",
        "GET",
        "/api/admin/propaganda/welcome-signal",
        200
    )
    if success:
        print(f"   enabled: {welcome_settings.get('enabled')}")
        print(f"   hour_utc: {welcome_settings.get('hour_utc')}")

    success, interaction_settings = tester.run_test(
        "Regression: GET /api/admin/propaganda/interaction-bot",
        "GET",
        "/api/admin/propaganda/interaction-bot",
        200
    )
    if success:
        print(f"   enabled: {interaction_settings.get('enabled')}")
        print(f"   replies_per_tick: {interaction_settings.get('replies_per_tick')}")

    # ---- Test 12: GET /api/admin/bots/jobs (regression) ----
    success, jobs = tester.run_test(
        "Regression: GET /api/admin/bots/jobs",
        "GET",
        "/api/admin/bots/jobs",
        200
    )
    if success:
        print(f"   jobs count: {len(jobs)}")
        for job in jobs[:3]:
            print(f"     - {job.get('id')}: next_run={job.get('next_run_time')}")

    # ---- Test 13: GET /api/admin/bots/posts (regression) ----
    success, posts = tester.run_test(
        "Regression: GET /api/admin/bots/posts",
        "GET",
        "/api/admin/bots/posts?limit=5",
        200
    )
    if success:
        print(f"   total posts: {posts.get('total')}")
        print(f"   returned: {len(posts.get('items', []))}")

    # ---- Restore kill-switch to original state ----
    if config.get('kill_switch_active'):
        print("\n⚙️  Restoring kill-switch to original state (ON)...")
        tester.run_test(
            "Restore kill-switch",
            "POST",
            "/api/admin/bots/kill-switch",
            200,
            data={"active": True}
        )

    # ---- Summary ----
    print("\n" + "=" * 70)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 70)
    
    return 0 if tester.tests_passed == tester.tests_run else 1


if __name__ == "__main__":
    sys.exit(main())
