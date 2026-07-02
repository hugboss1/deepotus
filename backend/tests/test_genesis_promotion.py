"""Unit tests — Genesis subscribers → Level 02 promotion (Mail #2 backfill).

Mail #1 (sent while the classified vault was SEALED) promises the Level 02
accreditation card will be "auto-sent at mint". These tests pin the module
that delivers on that promise:

  * ``core.genesis_promotion.build_genesis_subscriber_doc`` — the document
    shape inserted by /api/access-card/genesis-broadcast. Must carry
    ``email_hash`` + ``source`` so it coexists with the ecosystem Genesis
    list unique index ``(email_hash, source)`` (previously the vault flow
    inserted neither field → the second sealed signup hit a duplicate-key
    error on the (null, null) pair).
  * ``core.genesis_promotion.promote_pending`` — iterates un-promoted
    subscribers, generates their access card, sends Mail #2 and marks
    ``promoted_to_accreditation: true``. Sealed-guarded, dry-runnable,
    blacklist-aware, failure-tolerant.

Offline, no Mongo, no Resend — everything is injected fakes, async driven
via ``asyncio.run`` (consistent with the rest of the suite).
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Dict, List, Optional

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "deepotus_test")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import genesis_promotion as gp  # noqa: E402
from core.genesis import _hash_email  # noqa: E402


# =====================================================================
# Fakes — minimal Motor-ish surface
# =====================================================================
def _matches(doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
    for key, cond in query.items():
        if isinstance(cond, dict) and "$exists" in cond:
            if (key in doc) != bool(cond["$exists"]):
                return False
        elif doc.get(key) != cond:
            return False
    return True


class FakeCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = list(docs)

    def sort(self, field: str, direction: int) -> "FakeCursor":
        self._docs.sort(
            key=lambda d: d.get(field) or 0, reverse=(direction < 0)
        )
        return self

    def limit(self, n: int) -> "FakeCursor":
        if n:
            self._docs = self._docs[:n]
        return self

    def __aiter__(self):
        self._it = iter(list(self._docs))
        return self

    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration


class FakeCollection:
    def __init__(self, docs: Optional[List[Dict[str, Any]]] = None):
        self.docs = docs or []
        self.updates: List[Any] = []

    def find(self, query: Dict[str, Any]):
        return FakeCursor([d for d in self.docs if _matches(d, query)])

    async def find_one(self, query: Dict[str, Any]):
        for d in self.docs:
            if _matches(d, query):
                return d
        return None

    async def count_documents(self, query: Dict[str, Any]) -> int:
        return len([d for d in self.docs if _matches(d, query)])

    async def update_one(self, flt: Dict[str, Any], update: Dict[str, Any]):
        self.updates.append((flt, update))
        for d in self.docs:
            if _matches(d, flt):
                for k, v in update.get("$set", {}).items():
                    d[k] = v
                break


class FakeDB:
    def __init__(
        self,
        *,
        subscribers: Optional[List[Dict[str, Any]]] = None,
        blacklist: Optional[List[Dict[str, Any]]] = None,
        whitelist: Optional[List[Dict[str, Any]]] = None,
        vault_state: Optional[Dict[str, Any]] = None,
    ):
        self.genesis_subscribers = FakeCollection(subscribers)
        self.blacklist = FakeCollection(blacklist)
        self.whitelist = FakeCollection(whitelist)
        self.vault_state = FakeCollection(
            [vault_state] if vault_state else []
        )


LIVE_VAULT = {
    "_id": "protocol_delta_sigma",
    "dex_token_address": "MiNt111111111111111111111111111111111111111",
    "dex_mode": "helius",
    "helius_demo_mode": False,
}

SEALED_VAULT = {"_id": "protocol_delta_sigma"}  # auto-rule → sealed


def _sub(email: str, position: int, **extra: Any) -> Dict[str, Any]:
    doc = {
        "_id": f"id-{email}",
        "email": email,
        "display_name": email.split("@")[0],
        "position": position,
        "lang": "fr",
        "promoted_to_accreditation": False,
    }
    doc.update(extra)
    return doc


class Recorder:
    """Injectable create_card / send_email fakes with call capture."""

    def __init__(self, send_ok: Any = True):
        self.created: List[str] = []
        self.sent: List[Any] = []
        self._send_ok = send_ok

    async def create_card(self, *, email: str, display_name: str, whitelisted: bool):
        self.created.append(email)
        return {
            "accreditation_number": f"DS-{email.split('@')[0].upper()}",
            "display_name": display_name,
            "card_path": "/tmp/fake-card.png",
            "issued_at": "2026-07-02T10:00:00+00:00",
            "expires_at": "2026-10-02T10:00:00+00:00",
        }

    async def send_email(self, *, email: str, lang: str, card_doc: Dict[str, Any]):
        self.sent.append((email, lang, card_doc["accreditation_number"]))
        if callable(self._send_ok):
            return self._send_ok(email)
        return self._send_ok


def _run(db: FakeDB, rec: Recorder, **kw: Any) -> Dict[str, Any]:
    return asyncio.run(
        gp.promote_pending(
            db, create_card=rec.create_card, send_email=rec.send_email, **kw
        )
    )


# =====================================================================
# build_genesis_subscriber_doc — index-collision fix
# =====================================================================
class TestBuildSubscriberDoc:
    def test_doc_carries_email_hash_and_source(self) -> None:
        doc = gp.build_genesis_subscriber_doc(
            email="Agent@Example.COM ", display_name="Agent", position=4, lang="en"
        )
        assert doc["email"] == "agent@example.com"
        assert doc["email_hash"] == _hash_email("agent@example.com")
        assert doc["source"] == "vault_terminal"
        assert doc["position"] == 4
        assert doc["lang"] == "en"
        assert doc["promoted_to_accreditation"] is False
        assert doc["vault_status_at_signup"] == "sealed"
        assert doc["_id"]

    def test_optional_request_metadata(self) -> None:
        doc = gp.build_genesis_subscriber_doc(
            email="a@b.c", display_name="a", position=1, lang="fr",
            ip="1.2.3.4", ua="UA" * 200,
        )
        assert doc["ip"] == "1.2.3.4"
        assert len(doc["ua"]) <= 240


# =====================================================================
# promote_pending — seal guard
# =====================================================================
class TestSealGuard:
    def test_sealed_vault_blocks_promotion(self) -> None:
        db = FakeDB(subscribers=[_sub("a@x.io", 1)], vault_state=SEALED_VAULT)
        rec = Recorder()
        out = _run(db, rec)
        assert out["ok"] is False
        assert out["code"] == "VAULT_SEALED"
        assert rec.created == [] and rec.sent == []
        assert db.genesis_subscribers.updates == []

    def test_force_overrides_seal(self) -> None:
        db = FakeDB(subscribers=[_sub("a@x.io", 1)], vault_state=SEALED_VAULT)
        rec = Recorder()
        out = _run(db, rec, force=True)
        assert out["ok"] is True
        assert out["promoted"] == 1


# =====================================================================
# promote_pending — nominal flow
# =====================================================================
class TestPromotion:
    def test_promotes_pending_in_arrival_order_and_marks(self) -> None:
        ecosystem_doc = {  # Sprint 20 Genesis list doc — must be ignored
            "_id": "eco-1",
            "email": "eco@x.io",
            "email_hash": _hash_email("eco@x.io"),
            "source": "genesis_roman",
        }
        db = FakeDB(
            subscribers=[
                _sub("second@x.io", 2),
                _sub("first@x.io", 1),
                _sub("done@x.io", 0, promoted_to_accreditation=True),
                ecosystem_doc,
            ],
            vault_state=LIVE_VAULT,
        )
        rec = Recorder()
        out = _run(db, rec)

        assert out["ok"] is True
        assert out["scanned"] == 2
        assert out["promoted"] == 2
        assert out["failed"] == 0
        assert rec.created == ["first@x.io", "second@x.io"]  # position order
        assert [s[0] for s in rec.sent] == ["first@x.io", "second@x.io"]

        first = asyncio.run(db.genesis_subscribers.find_one({"email": "first@x.io"}))
        assert first["promoted_to_accreditation"] is True
        assert first["accreditation_number"] == "DS-FIRST"
        assert first["promoted_at"]

    def test_whitelisted_flag_propagates_to_card(self) -> None:
        calls: List[bool] = []

        class Spy(Recorder):
            async def create_card(self, *, email, display_name, whitelisted):
                calls.append(whitelisted)
                return await super().create_card(
                    email=email, display_name=display_name, whitelisted=whitelisted
                )

        db = FakeDB(
            subscribers=[_sub("wl@x.io", 1), _sub("nowl@x.io", 2)],
            whitelist=[{"email": "wl@x.io"}],
            vault_state=LIVE_VAULT,
        )
        rec = Spy()
        _run(db, rec)
        assert calls == [True, False]

    def test_dry_run_touches_nothing(self) -> None:
        db = FakeDB(
            subscribers=[_sub("a@x.io", 1), _sub("b@x.io", 2)],
            vault_state=LIVE_VAULT,
        )
        rec = Recorder()
        out = _run(db, rec, dry_run=True)
        assert out["ok"] is True
        assert out["dry_run"] is True
        assert out["scanned"] == 2
        assert out["promoted"] == 0
        assert rec.created == [] and rec.sent == []
        assert db.genesis_subscribers.updates == []

    def test_limit_caps_processing(self) -> None:
        db = FakeDB(
            subscribers=[_sub("a@x.io", 1), _sub("b@x.io", 2)],
            vault_state=LIVE_VAULT,
        )
        rec = Recorder()
        out = _run(db, rec, limit=1)
        assert out["promoted"] == 1
        assert rec.created == ["a@x.io"]

    def test_blacklisted_skipped_and_flagged(self) -> None:
        db = FakeDB(
            subscribers=[_sub("bad@x.io", 1), _sub("good@x.io", 2)],
            blacklist=[{"email": "bad@x.io"}],
            vault_state=LIVE_VAULT,
        )
        rec = Recorder()
        out = _run(db, rec)
        assert out["promoted"] == 1
        assert out["skipped_blacklisted"] == 1
        assert rec.created == ["good@x.io"]

        bad = asyncio.run(db.genesis_subscribers.find_one({"email": "bad@x.io"}))
        assert bad["promoted_to_accreditation"] is False
        assert bad["promotion_skipped_reason"] == "blacklisted"
        # A later run must not re-scan the flagged doc
        out2 = _run(db, Recorder())
        assert out2["scanned"] == 0

    def test_send_failure_leaves_doc_unpromoted_and_continues(self) -> None:
        db = FakeDB(
            subscribers=[_sub("boom@x.io", 1), _sub("ok@x.io", 2)],
            vault_state=LIVE_VAULT,
        )
        rec = Recorder(send_ok=lambda email: email != "boom@x.io")
        out = _run(db, rec)
        assert out["failed"] == 1
        assert out["promoted"] == 1

        boom = asyncio.run(db.genesis_subscribers.find_one({"email": "boom@x.io"}))
        assert boom["promoted_to_accreditation"] is False
        ok = asyncio.run(db.genesis_subscribers.find_one({"email": "ok@x.io"}))
        assert ok["promoted_to_accreditation"] is True


# =====================================================================
# Router wiring — admin endpoints exist
# =====================================================================
class TestAdminRouterWiring:
    def test_admin_router_exposes_promotion_routes(self) -> None:
        import routers.access_card as ac

        assert hasattr(ac, "admin_router"), "admin_router missing on routers.access_card"
        routes = {
            (r.path, m) for r in ac.admin_router.routes for m in r.methods
        }
        assert ("/api/admin/access-card/genesis/promote", "POST") in routes
        assert ("/api/admin/access-card/genesis/pending", "GET") in routes

    def test_admin_router_registered_on_app(self) -> None:
        import server

        paths = {r.path for r in server.app.routes}
        assert "/api/admin/access-card/genesis/promote" in paths
