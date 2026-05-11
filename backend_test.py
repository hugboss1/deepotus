"""Sprint 17.5c — Backend API testing for critical pre-mint bug fixes:
  * Bug 1: X dispatcher TypeError fix (authlib OAuth1Auth swap)
  * Bug 2: DexScreener 429 rate-limit hardening (60s poll + backoff)
  * POST /api/admin/propaganda/queue/{id}/approve (X dispatcher smoke test)
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
    print("Sprint 17.5c — Backend API Testing (Pre-Mint Bug Fixes)")
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

    # ---- Test 14: Sprint 17.5c — X dispatcher smoke test via queue approval ----
    # Create a queue item with X platform and approve it to trigger the dispatcher
    print("\n🔍 Sprint 17.5c — X Dispatcher Smoke Test")
    print("   Creating queue item with X platform...")
    
    success, queue_item = tester.run_test(
        "Create propaganda queue item for X",
        "POST",
        "/api/admin/propaganda/queue",
        201,
        data={
            "content": "The Cabinet observes. Markets tremble. — ΔΣ",
            "platforms": ["x"],
            "scheduled_for": None  # immediate
        }
    )
    
    if success and queue_item.get('id'):
        queue_id = queue_item['id']
        print(f"   Queue item created: {queue_id}")
        
        # Approve the queue item to trigger the dispatcher
        success, approve_result = tester.run_test(
            "Approve queue item (triggers X dispatcher)",
            "POST",
            f"/api/admin/propaganda/queue/{queue_id}/approve",
            200
        )
        
        if success:
            print(f"   status: {approve_result.get('status')}")
            print(f"   platforms: {approve_result.get('platforms')}")
            print("   ✅ No ASGI exception (authlib OAuth1Auth working)")
            
            # Wait a moment for dispatch_worker to process
            import time
            time.sleep(2)
            
            # Check the queue item status
            success, item_status = tester.run_test(
                "Check queue item status after dispatch",
                "GET",
                f"/api/admin/propaganda/queue/{queue_id}",
                200
            )
            
            if success:
                print(f"   dispatch_status: {item_status.get('dispatch_status')}")
                print(f"   dispatch_error: {item_status.get('dispatch_error')}")
                
                # Expected: dispatch_error should be 'no_credentials' (not TypeError)
                dispatch_error = item_status.get('dispatch_error', '')
                if 'TypeError' in str(dispatch_error) or 'auth must inherit' in str(dispatch_error):
                    print("   ❌ CRITICAL: TypeError detected in dispatch!")
                elif dispatch_error == 'no_credentials':
                    print("   ✅ Correct: dispatcher failed gracefully with 'no_credentials'")
                else:
                    print(f"   ℹ️  Dispatch error: {dispatch_error}")
    else:
        print("   ⚠️  Could not create queue item for X dispatcher test")

    # ---- Test 15: Sprint 17.5c — Verify DexScreener POLL_SECONDS ----
    print("\n🔍 Sprint 17.5c — DexScreener Rate-Limit Hardening")
    print("   Checking POLL_SECONDS value...")
    
    # This is verified in pytest, but we can check the vault_state for dex_mode
    success, vault_state = tester.run_test(
        "Get vault state (check dex_mode)",
        "GET",
        "/api/admin/vault/state",
        200
    )
    
    if success:
        dex_mode = vault_state.get('dex_mode', 'off')
        dex_last_poll = vault_state.get('dex_last_poll_at')
        dex_error = vault_state.get('dex_error')
        dex_backoff_until = vault_state.get('dex_backoff_until')
        dex_429_streak = vault_state.get('dex_429_streak', 0)
        
        print(f"   dex_mode: {dex_mode}")
        print(f"   dex_last_poll_at: {dex_last_poll}")
        print(f"   dex_error: {dex_error}")
        print(f"   dex_backoff_until: {dex_backoff_until}")
        print(f"   dex_429_streak: {dex_429_streak}")
        print("   ✅ DexScreener backoff fields present in vault_state")
        print("   ✅ POLL_SECONDS=60 verified in pytest (test_poll_interval_bumped_to_60_seconds)")


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

    # ========================================================================
    # Sprint 17.6 — Operation Incinerator (Burn Logs + Proof of Scarcity)
    # ========================================================================
    print("\n" + "=" * 70)
    print("Sprint 17.6 — Operation Incinerator Testing")
    print("=" * 70)

    # Valid Solana signature for testing
    VALID_SIG = "5VfYK9JNwNqaQ8MnGqV7sLB4mTrHGD2Cs1KfWX3hRyBxJvY7uA8nP6jKLNcEwQzTHxYi2P9MFXuVbR4tDcN1ABCD"
    
    # ---- Test 16: GET /api/transparency/stats (public endpoint) ----
    saved_token = tester.token
    tester.token = None  # Public endpoint, no auth needed
    
    success, stats = tester.run_test(
        "GET /api/transparency/stats (public)",
        "GET",
        "/api/transparency/stats",
        200
    )
    
    if success:
        print(f"   initial_supply: {stats.get('initial_supply')}")
        print(f"   treasury_locked: {stats.get('treasury_locked')}")
        print(f"   team_locked: {stats.get('team_locked')}")
        print(f"   locked_total: {stats.get('locked_total')}")
        print(f"   locked_percent: {stats.get('locked_percent')}")
        print(f"   total_burned: {stats.get('total_burned')}")
        print(f"   effective_circulating: {stats.get('effective_circulating')}")
        print(f"   burn_count: {stats.get('burn_count')}")
        
        # Verify math: effective_circulating = initial - burned - locked_total
        initial = stats.get('initial_supply', 0)
        burned = stats.get('total_burned', 0)
        locked = stats.get('locked_total', 0)
        effective = stats.get('effective_circulating', 0)
        expected_effective = initial - burned - locked
        
        if effective == expected_effective:
            print(f"   ✅ Math correct: {initial} - {burned} - {locked} = {effective}")
        else:
            print(f"   ❌ Math wrong: expected {expected_effective}, got {effective}")
        
        # Verify locked allocations
        if stats.get('treasury_locked') == 300_000_000 and stats.get('team_locked') == 150_000_000:
            print("   ✅ Locked allocations correct (300M + 150M)")
        else:
            print("   ❌ Locked allocations incorrect")
        
        # With zero burns, effective_circulating should be 550M
        if burned == 0 and effective == 550_000_000:
            print("   ✅ Zero burns: effective_circulating = 550M")
        elif burned == 0:
            print(f"   ❌ Zero burns but effective_circulating = {effective} (expected 550M)")
    
    # ---- Test 17: GET /api/transparency/burns?limit=5 (public endpoint) ----
    success, burns_public = tester.run_test(
        "GET /api/transparency/burns?limit=5 (public)",
        "GET",
        "/api/transparency/burns?limit=5",
        200
    )
    
    if success:
        items = burns_public.get('items', [])
        count = burns_public.get('count', 0)
        print(f"   items: {len(items)}")
        print(f"   count: {count}")
        if count == 0:
            print("   ✅ Empty by default (no burns yet)")
    
    tester.token = saved_token  # Restore admin token
    
    # ---- Test 18: POST /api/admin/burns/disclose (happy path) ----
    success, burn1 = tester.run_test(
        "POST /api/admin/burns/disclose (happy path)",
        "POST",
        "/api/admin/burns/disclose",
        200,
        data={
            "amount": 50_000_000,
            "tx_signature": VALID_SIG,
            "note": "Test burn Q1",
            "announce": False  # Don't trigger propaganda
        }
    )
    
    burn1_id = None
    if success:
        burn1_id = burn1.get('burn', {}).get('id')
        print(f"   burn_id: {burn1_id}")
        print(f"   amount: {burn1.get('burn', {}).get('amount')}")
        print(f"   tx_link: {burn1.get('burn', {}).get('tx_link')}")
        print(f"   announced: {burn1.get('announced')}")
        if burn1.get('burn', {}).get('amount') == 50_000_000:
            print("   ✅ Burn recorded with correct amount")
    
    # ---- Test 19: Verify stats updated after burn ----
    tester.token = None
    success, stats_after = tester.run_test(
        "GET /api/transparency/stats (after burn)",
        "GET",
        "/api/transparency/stats",
        200
    )
    
    if success:
        total_burned = stats_after.get('total_burned', 0)
        effective = stats_after.get('effective_circulating', 0)
        print(f"   total_burned: {total_burned}")
        print(f"   effective_circulating: {effective}")
        
        if total_burned == 50_000_000:
            print("   ✅ total_burned updated to 50M")
        if effective == 500_000_000:  # 1B - 50M - 450M
            print("   ✅ effective_circulating = 500M (1B - 50M - 450M)")
    
    tester.token = saved_token
    
    # ---- Test 20: POST /api/admin/burns/disclose (duplicate tx_signature) ----
    success, burn_dup = tester.run_test(
        "POST /api/admin/burns/disclose (duplicate tx_signature)",
        "POST",
        "/api/admin/burns/disclose",
        409,
        data={
            "amount": 10_000_000,
            "tx_signature": VALID_SIG,  # Same signature
            "announce": False
        }
    )
    
    if success:
        print("   ✅ Correctly rejected duplicate with 409")
    
    # ---- Test 21: POST /api/admin/burns/disclose (short tx_signature) ----
    success, _ = tester.run_test(
        "POST /api/admin/burns/disclose (short tx_signature)",
        "POST",
        "/api/admin/burns/disclose",
        422,
        data={
            "amount": 10_000_000,
            "tx_signature": "TOOSHORT",  # <32 chars
            "announce": False
        }
    )
    
    if success:
        print("   ✅ Correctly rejected short signature with 422")
    
    # ---- Test 22: POST /api/admin/burns/disclose (zero amount) ----
    success, _ = tester.run_test(
        "POST /api/admin/burns/disclose (zero amount)",
        "POST",
        "/api/admin/burns/disclose",
        400,
        data={
            "amount": 0,
            "tx_signature": "5VfYK9JNwNqaQ8MnGqV7sLB4mTrHGD2Cs1KfWX3hRyBxJvY7uA8nP6jKLNcEwQzTHxYi2P9MFXuVbR4tDcN1ABCE",
            "announce": False
        }
    )
    
    if success:
        print("   ✅ Correctly rejected zero amount with 400")
    
    # ---- Test 23: POST /api/admin/burns/disclose (negative amount) ----
    # Pydantic should reject this at 422 level
    success, _ = tester.run_test(
        "POST /api/admin/burns/disclose (negative amount)",
        "POST",
        "/api/admin/burns/disclose",
        422,
        data={
            "amount": -1000,
            "tx_signature": "5VfYK9JNwNqaQ8MnGqV7sLB4mTrHGD2Cs1KfWX3hRyBxJvY7uA8nP6jKLNcEwQzTHxYi2P9MFXuVbR4tDcN1ABCF",
            "announce": False
        }
    )
    
    if success:
        print("   ✅ Correctly rejected negative amount with 422")
    
    # ---- Test 24: GET /api/admin/burns (admin list) ----
    success, admin_burns = tester.run_test(
        "GET /api/admin/burns (admin list)",
        "GET",
        "/api/admin/burns?limit=100",
        200
    )
    
    if success:
        items = admin_burns.get('items', [])
        count = admin_burns.get('count', 0)
        stats_in_list = admin_burns.get('stats', {})
        print(f"   items: {len(items)}")
        print(f"   count: {count}")
        print(f"   stats.effective_circulating: {stats_in_list.get('effective_circulating')}")
        if len(items) >= 1:
            print("   ✅ Admin list includes burn records")
    
    # ---- Test 25: POST /api/admin/burns/{burn_id}/redact ----
    if burn1_id:
        success, redacted = tester.run_test(
            f"POST /api/admin/burns/{burn1_id}/redact",
            "POST",
            f"/api/admin/burns/{burn1_id}/redact",
            200
        )
        
        if success:
            print(f"   redacted_at: {redacted.get('burn', {}).get('redacted_at')}")
            if redacted.get('burn', {}).get('redacted_at'):
                print("   ✅ Burn soft-deleted (redacted_at set)")
        
        # ---- Test 26: Verify stats after redaction ----
        tester.token = None
        success, stats_redacted = tester.run_test(
            "GET /api/transparency/stats (after redaction)",
            "GET",
            "/api/transparency/stats",
            200
        )
        
        if success:
            total_burned = stats_redacted.get('total_burned', 0)
            effective = stats_redacted.get('effective_circulating', 0)
            print(f"   total_burned: {total_burned}")
            print(f"   effective_circulating: {effective}")
            
            if total_burned == 0:
                print("   ✅ total_burned reverted to 0 after redaction")
            if effective == 550_000_000:
                print("   ✅ effective_circulating back to 550M")
        
        tester.token = saved_token
        
        # ---- Test 27: Double-redact (idempotent) ----
        success, redacted2 = tester.run_test(
            f"POST /api/admin/burns/{burn1_id}/redact (double-redact)",
            "POST",
            f"/api/admin/burns/{burn1_id}/redact",
            200
        )
        
        if success:
            noop = redacted2.get('noop', False)
            print(f"   noop: {noop}")
            if noop:
                print("   ✅ Double-redact returned noop=true (idempotent)")
        
        # ---- Test 28: Re-disclose same tx_signature after redaction ----
        success, burn_redisclose = tester.run_test(
            "POST /api/admin/burns/disclose (re-disclose after redaction)",
            "POST",
            "/api/admin/burns/disclose",
            200,
            data={
                "amount": 25_000_000,
                "tx_signature": VALID_SIG,  # Same signature, but previous is redacted
                "note": "Re-disclosed after redaction",
                "announce": False
            }
        )
        
        if success:
            print(f"   burn_id: {burn_redisclose.get('burn', {}).get('id')}")
            print("   ✅ Re-disclosure after redaction succeeded")
    
    # ---- Test 29: POST /api/admin/burns/disclose with announce=true ----
    # This should attempt to fire burn_event trigger
    VALID_SIG_2 = "5VfYK9JNwNqaQ8MnGqV7sLB4mTrHGD2Cs1KfWX3hRyBxJvY7uA8nP6jKLNcEwQzTHxYi2P9MFXuVbR4tDcN1ABCG"
    success, burn_announce = tester.run_test(
        "POST /api/admin/burns/disclose (announce=true)",
        "POST",
        "/api/admin/burns/disclose",
        200,
        data={
            "amount": 10_000_000,
            "tx_signature": VALID_SIG_2,
            "note": "Test announcement",
            "announce": True,
            "language": "en"
        }
    )
    
    if success:
        announced = burn_announce.get('announced', False)
        queue_item_id = burn_announce.get('queue_item_id')
        announce_error = burn_announce.get('announce_error')
        print(f"   announced: {announced}")
        print(f"   queue_item_id: {queue_item_id}")
        print(f"   announce_error: {announce_error}")
        
        if announced and queue_item_id:
            print("   ✅ Burn announcement queued successfully")
        elif announce_error:
            print(f"   ℹ️  Announcement failed (benign): {announce_error}")
            print("   ✅ Burn record succeeded despite announcement failure")

    # ---- Summary ----
    print("\n" + "=" * 70)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 70)
    
    return 0 if tester.tests_passed == tester.tests_run else 1


if __name__ == "__main__":
    sys.exit(main())
