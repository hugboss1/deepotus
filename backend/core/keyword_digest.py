"""Keyword Digest — semi-automatic organic-visibility scanner.

Compliance frame
----------------
Auto-replying to strangers matched by keyword is reply-spam under X's
automation rules (account-suspension territory for a token account).
This module therefore NEVER posts to X. It searches, curates, and
sends the founder a private Telegram digest where every hit ships with
a ready-to-paste suggested reply + a one-tap X *intent* link that
opens the reply composer pre-filled. A human presses send — always.

Flow
----
    APScheduler tick (30 min, self-gated on ``hours_utc``)
        └─► run_digest()
              1. For each configured rule: GET /2/tweets/search/recent
                 (app-only Bearer) with ``-is:retweet -is:reply`` and
                 language filters appended.
              2. Dedup against ``keyword_digest_seen`` (TTL 7 days) so
                 a tweet is only ever digested once.
              3. Build one Telegram message per hit (HTML parse mode,
                 suggested reply in <pre> for one-tap copy) + a header.
              4. Send to the ADMIN chat (``telegram/TELEGRAM_ADMIN_CHAT_ID``).
                 The public channel chat id is deliberately NOT a
                 fallback — a digest leaking to t.me/deepotus would be
                 embarrassing at best.
              5. Audit in ``keyword_digest_runs``.

Cost awareness (Pay-Per-Use credits)
------------------------------------
Default = 2 runs/day × 3 rules × 1 search page (10 results) → ~6
search reads/day. Zero X writes.
"""

from __future__ import annotations

import html
import logging
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from core.config import db
from core.secret_provider import (
    get_telegram_admin_chat_id,
    get_telegram_bot_token,
    get_twitter_bearer_token,
)

logger = logging.getLogger("deepotus.keyword_digest")

CONFIG_COLLECTION = "keyword_digest_config"
CONFIG_ID = "keyword_digest_v1"
SEEN_COLLECTION = "keyword_digest_seen"
RUNS_COLLECTION = "keyword_digest_runs"

_X_API_BASE = "https://api.twitter.com/2"
_X_REQUEST_TIMEOUT_S = 12.0
_TG_API_BASE = "https://api.telegram.org"
_TG_REQUEST_TIMEOUT_S = 15.0

#: A digested tweet is never re-proposed for this long.
_SEEN_TTL_S = 7 * 24 * 3600
#: Hard cap on hits per run (across all rules) — keeps the Telegram
#: burst readable and the founder's thumb alive.
_MAX_HITS_PER_RUN = 10
#: Two runs in the same configured hour are absurd; a run in hour H
#: blocks any other run for this long.
_MIN_HOURS_BETWEEN_RUNS = 3

#: Default rules — query syntax is X search v2. Filters like
#: ``-is:retweet -is:reply`` are appended automatically at query time.
#: Templates validated with the founder on 2026-07-18; ``{handle}`` is
#: replaced by the hit's author.
DEFAULT_RULES: List[Dict[str, str]] = [
    {
        "label": "i need a ticker",
        "query": '"i need a ticker" OR "need a ticker" OR "gimme a ticker"',
        "template": (
            "{handle} You asked for a ticker. The Deep State already "
            "assigned you one: $D2EP.\n"
            "CA: AUztiAfSCwDwm5Be5tSDiTmrZPnwATk7837cAFeDpump\n"
            "\U0001f310 deepotus.xyz\n"
            "Enlist: @Deepotus_AI \U0001f5f3 NFA"
        ),
    },
    {
        "label": "no pump & dump",
        "query": '"no pump and dump" OR "not a pump and dump" OR "tired of pump and dumps"',
        "template": (
            "{handle} Same doctrine. $D2EP: 0% tax, multisig treasury, "
            "sales announced 48h ahead. No pump & dump — just a cynical "
            "AI candidate.\n"
            "CA: AUztiAfSCwDwm5Be5tSDiTmrZPnwATk7837cAFeDpump\n"
            "\U0001f310 deepotus.xyz · @Deepotus_AI NFA"
        ),
    },
    {
        "label": "chill",
        "query": 'chill (memecoin OR solana OR "pump fun" OR ticker)',
        "template": (
            "{handle} Chill is the whole doctrine. $D2EP holds, the "
            "dials turn, the Vault waits.\n"
            "CA: AUztiAfSCwDwm5Be5tSDiTmrZPnwATk7837cAFeDpump\n"
            "\U0001f310 deepotus.xyz\n"
            "Follow @Deepotus_AI \U0001f5f3 NFA"
        ),
    },
]

DEFAULT_CFG: Dict[str, Any] = {
    "enabled": False,  # OFF until the admin flips it post-recette
    "hours_utc": [7, 16],  # ≈ 09:00 + 18:00 Paris
    "lang": "en",
    "min_author_followers": 25,  # drops brand-new burner accounts
    "max_hits_per_rule": 5,
    "rules": [dict(r) for r in DEFAULT_RULES],
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
async def get_config() -> Dict[str, Any]:
    row = await db[CONFIG_COLLECTION].find_one({"_id": CONFIG_ID})
    if not row:
        row = {"_id": CONFIG_ID, **DEFAULT_CFG,
               "created_at": _now(), "updated_at": _now()}
        try:
            await db[CONFIG_COLLECTION].insert_one(row)
        except Exception:  # noqa: BLE001 — race on first boot is benign
            row = await db[CONFIG_COLLECTION].find_one({"_id": CONFIG_ID}) or row
    cfg = dict(DEFAULT_CFG)
    cfg.update({k: v for k, v in row.items() if k in DEFAULT_CFG or k in {
        "last_run_at", "last_run_summary",
    }})
    if not cfg.get("rules"):
        cfg["rules"] = [dict(r) for r in DEFAULT_RULES]
    return cfg


async def update_config(patch: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {
        "enabled", "hours_utc", "lang", "min_author_followers",
        "max_hits_per_rule", "rules",
    }
    safe = {k: v for k, v in patch.items() if k in allowed}
    if "hours_utc" in safe:
        hours = sorted({int(h) for h in (safe["hours_utc"] or []) if 0 <= int(h) <= 23})
        safe["hours_utc"] = hours or list(DEFAULT_CFG["hours_utc"])
    if "max_hits_per_rule" in safe:
        safe["max_hits_per_rule"] = max(1, min(10, int(safe["max_hits_per_rule"])))
    if "min_author_followers" in safe:
        safe["min_author_followers"] = max(0, int(safe["min_author_followers"]))
    if "rules" in safe:
        cleaned: List[Dict[str, str]] = []
        for r in (safe["rules"] or [])[:10]:
            label = str((r or {}).get("label") or "").strip()
            query = str((r or {}).get("query") or "").strip()
            template = str((r or {}).get("template") or "").strip()
            if label and query and template:
                cleaned.append({"label": label, "query": query, "template": template})
        safe["rules"] = cleaned or [dict(r) for r in DEFAULT_RULES]
    safe["updated_at"] = _now()
    await db[CONFIG_COLLECTION].update_one(
        {"_id": CONFIG_ID}, {"$set": safe}, upsert=True,
    )
    return await get_config()


# ---------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------
async def ensure_indexes() -> None:
    try:
        await db[SEEN_COLLECTION].create_index(
            [("tweet_id", 1)],
            unique=True, name="keyword_digest_seen_tweet_unique",
        )
        await db[SEEN_COLLECTION].create_index(
            [("first_seen_at", 1)],
            name="keyword_digest_seen_ttl",
            expireAfterSeconds=_SEEN_TTL_S,
        )
        await db[RUNS_COLLECTION].create_index(
            [("run_at", -1)], name="keyword_digest_runs_recent",
        )
    except Exception:  # noqa: BLE001
        logger.exception("[keyword-digest] index bootstrap failed")


# ---------------------------------------------------------------------
# X search
# ---------------------------------------------------------------------
def build_query(rule_query: str, lang: str) -> str:
    """Append the non-negotiable noise filters to an admin-edited rule
    query (unless the admin already put them in)."""
    q = (rule_query or "").strip()
    if " OR " in q and not (q.startswith("(") and q.endswith(")")):
        # ``a OR b -is:retweet`` binds the trailing filter to the last
        # OR operand only — parenthesise the user part first. Wrapping
        # an already partially-parenthesised query is harmless.
        q = f"({q})"
    for clause in ("-is:retweet", "-is:reply"):
        if clause not in q:
            q = f"{q} {clause}"
    lang = (lang or "").strip().lower()
    if lang and f"lang:{lang}" not in q:
        q = f"{q} lang:{lang}"
    return q


async def _search_recent(
    query: str, *, bearer: str, max_results: int = 10,
) -> List[Dict[str, Any]]:
    """One page of GET /2/tweets/search/recent. Returns hydrated hits:
    ``{id, text, created_at, author_handle, author_followers}``."""
    url = f"{_X_API_BASE}/tweets/search/recent"
    params: Dict[str, Any] = {
        "query": query,
        "max_results": max(10, min(100, int(max_results))),  # X floor is 10
        "tweet.fields": "created_at,text,author_id,public_metrics",
        "expansions": "author_id",
        "user.fields": "username,public_metrics",
    }
    try:
        async with httpx.AsyncClient(timeout=_X_REQUEST_TIMEOUT_S) as client:
            resp = await client.get(
                url, params=params,
                headers={"Authorization": f"Bearer {bearer}"},
            )
    except httpx.TimeoutException:
        logger.warning("[keyword-digest] search timeout query=%r", query[:60])
        return []
    except Exception:  # noqa: BLE001
        logger.exception("[keyword-digest] search crashed query=%r", query[:60])
        return []

    if resp.status_code == 429:
        logger.warning("[keyword-digest] search rate-limited — skipping rule")
        return []
    if resp.status_code >= 400:
        logger.warning(
            "[keyword-digest] search http_%d query=%r body=%s",
            resp.status_code, query[:60], (resp.text or "")[:200],
        )
        return []

    payload = resp.json() or {}
    tweets: List[Dict[str, Any]] = payload.get("data") or []
    users = ((payload.get("includes") or {}).get("users")) or []
    user_by_id = {str(u.get("id")): u for u in users}

    out: List[Dict[str, Any]] = []
    for tw in tweets:
        author = user_by_id.get(str(tw.get("author_id") or "")) or {}
        followers = int(((author.get("public_metrics") or {}).get("followers_count")) or 0)
        out.append({
            "id": str(tw.get("id") or ""),
            "text": str(tw.get("text") or ""),
            "created_at": str(tw.get("created_at") or ""),
            "author_handle": str(author.get("username") or ""),
            "author_followers": followers,
        })
    return out


async def _mark_seen(tweet_id: str, rule_label: str) -> bool:
    """Insert into the seen set. Returns True when this is the FIRST
    time we see the tweet (i.e. it belongs in the digest)."""
    try:
        await db[SEEN_COLLECTION].insert_one({
            "_id": str(uuid.uuid4()),
            "tweet_id": tweet_id,
            "rule_label": rule_label,
            "first_seen_at": _now(),
        })
        return True
    except Exception as e:  # noqa: BLE001
        if "E11000" in str(e) or "duplicate key" in str(e).lower():
            return False
        logger.exception("[keyword-digest] seen insert failed")
        return False


# ---------------------------------------------------------------------
# Digest rendering (Telegram HTML)
# ---------------------------------------------------------------------
def render_suggested_reply(template: str, handle: str) -> str:
    body = (template or "").replace("{handle}", f"@{handle.lstrip('@')}").strip()
    if len(body) > 260:
        body = body[:259] + "…"
    return body


def build_hit_message(hit: Dict[str, Any], rule_label: str, suggested: str) -> str:
    """One self-contained Telegram message (HTML) per hit:
    context + copyable reply + a one-tap pre-filled reply link."""
    handle = hit.get("author_handle") or "?"
    tweet_id = hit.get("id") or ""
    tweet_url = f"https://x.com/{handle}/status/{tweet_id}"
    intent_url = (
        "https://x.com/intent/tweet?in_reply_to="
        + urllib.parse.quote(tweet_id)
        + "&text="
        + urllib.parse.quote(suggested)
    )
    excerpt = html.escape((hit.get("text") or "").strip()[:280])
    followers = int(hit.get("author_followers") or 0)
    return (
        f"\U0001f3af <b>{html.escape(rule_label)}</b> — "
        f"@{html.escape(handle)} ({followers:,} followers)\n"
        f"<i>{excerpt}</i>\n"
        f"\U0001f517 {tweet_url}\n\n"
        f"✍️ Réponse suggérée (appui long pour copier) :\n"
        f"<pre>{html.escape(suggested)}</pre>\n"
        f"⚡ <a href=\"{html.escape(intent_url)}\">Répondre en 1 clic "
        f"(pré-rempli)</a>"
    )


async def _send_telegram_admin(text: str) -> bool:
    """Direct sendMessage to the ADMIN chat. Not the public dispatcher
    on purpose — different chat id, different failure policy."""
    token = await get_telegram_bot_token()
    chat_id = await get_telegram_admin_chat_id()
    if not token or not chat_id:
        return False
    url = f"{_TG_API_BASE}/bot{token}/sendMessage"
    body = {
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient(timeout=_TG_REQUEST_TIMEOUT_S) as client:
            resp = await client.post(url, json=body)
        ok = resp.status_code < 400 and bool((resp.json() or {}).get("ok"))
        if not ok:
            logger.warning(
                "[keyword-digest] telegram send failed http_%d body=%s",
                resp.status_code, (resp.text or "")[:200],
            )
        return ok
    except Exception:  # noqa: BLE001
        logger.exception("[keyword-digest] telegram send crashed")
        return False


# ---------------------------------------------------------------------
# Run — main entrypoint (scheduler tick + admin "Run now")
# ---------------------------------------------------------------------
async def run_digest(*, manual: bool = False) -> Dict[str, Any]:
    """Execute one full digest run. Never raises."""
    cfg = await get_config()
    if not cfg.get("enabled") and not manual:
        return {"ok": False, "reason": "disabled", "hits": 0}

    bearer = await get_twitter_bearer_token()
    if not bearer:
        return {"ok": False, "reason": "no_bearer_token", "hits": 0}

    admin_chat = await get_telegram_admin_chat_id()
    if not admin_chat:
        logger.warning(
            "[keyword-digest] TELEGRAM_ADMIN_CHAT_ID missing (vault telegram/"
            "TELEGRAM_ADMIN_CHAT_ID or env) — digest has nowhere private to go",
        )
        return {"ok": False, "reason": "no_admin_chat_id", "hits": 0}

    lang = str(cfg.get("lang") or "en")
    min_followers = int(cfg.get("min_author_followers") or 0)
    per_rule_cap = max(1, min(10, int(cfg.get("max_hits_per_rule") or 5)))

    selected: List[Dict[str, Any]] = []  # {hit, rule_label, suggested}
    per_rule_stats: Dict[str, Dict[str, int]] = {}

    for rule in cfg.get("rules") or []:
        label = str(rule.get("label") or "").strip() or "?"
        query = build_query(str(rule.get("query") or ""), lang)
        template = str(rule.get("template") or "")
        hits = await _search_recent(query, bearer=bearer)
        kept = 0
        for hit in hits:
            if len(selected) >= _MAX_HITS_PER_RUN or kept >= per_rule_cap:
                break
            if not hit.get("id") or not hit.get("author_handle"):
                continue
            if int(hit.get("author_followers") or 0) < min_followers:
                continue
            if not await _mark_seen(hit["id"], label):
                continue  # already digested in a previous run
            suggested = render_suggested_reply(template, hit["author_handle"])
            selected.append({"hit": hit, "rule_label": label, "suggested": suggested})
            kept += 1
        per_rule_stats[label] = {"fetched": len(hits), "kept": kept}

    sent = 0
    if selected:
        header = (
            f"\U0001f4e1 <b>DIGEST ΔΣ</b> — {len(selected)} cible(s) "
            f"détectée(s)\n"
            f"Chaque message ci-dessous contient la réponse prête "
            f"à coller. À TOI d'appuyer sur envoyer — rien ne part "
            f"tout seul."
        )
        if await _send_telegram_admin(header):
            sent += 1
        for entry in selected:
            msg = build_hit_message(
                entry["hit"], entry["rule_label"], entry["suggested"],
            )
            if await _send_telegram_admin(msg):
                sent += 1
            else:
                # Send failed (bot blocked, 403 before first /start,
                # Telegram outage…) — release the dedup claim so this
                # tweet is re-proposed on the next run instead of being
                # silently lost.
                try:
                    await db[SEEN_COLLECTION].delete_one(
                        {"tweet_id": entry["hit"]["id"]},
                    )
                except Exception:  # noqa: BLE001
                    logger.exception("[keyword-digest] seen rollback failed")

    summary = {
        "run_at": _now_iso(),
        "manual": manual,
        "hits": len(selected),
        "telegram_messages_sent": sent,
        "per_rule": per_rule_stats,
    }
    try:
        await db[RUNS_COLLECTION].insert_one({"_id": str(uuid.uuid4()), **summary})
        await db[CONFIG_COLLECTION].update_one(
            {"_id": CONFIG_ID},
            {"$set": {"last_run_at": summary["run_at"], "last_run_summary": summary}},
            upsert=True,
        )
    except Exception:  # noqa: BLE001
        logger.exception("[keyword-digest] run audit persist failed")

    logger.info(
        "[keyword-digest] run done hits=%d sent=%d manual=%s",
        len(selected), sent, manual,
    )
    return {"ok": True, **summary}


def should_fire(
    *, hours_utc: List[int], now: datetime, last_run_at: Optional[str],
) -> bool:
    """Pure gating helper (unit-tested): fire when the current UTC hour
    is a configured slot AND the previous run is old enough."""
    if now.hour not in (hours_utc or []):
        return False
    if not last_run_at:
        return True
    try:
        last_dt = datetime.fromisoformat(str(last_run_at).replace("Z", "+00:00"))
    except ValueError:
        return True
    return (now - last_dt) >= timedelta(hours=_MIN_HOURS_BETWEEN_RUNS)


async def tick() -> Dict[str, Any]:
    """APScheduler entry-point — every 30 min; fires ~2×/day. Never raises."""
    try:
        cfg = await get_config()
        if not cfg.get("enabled"):
            return {"ok": False, "reason": "disabled"}
        if not should_fire(
            hours_utc=[int(h) for h in (cfg.get("hours_utc") or [])],
            now=_now(),
            last_run_at=cfg.get("last_run_at"),
        ):
            return {"ok": True, "reason": "outside_window"}
        return await run_digest(manual=False)
    except Exception as exc:  # noqa: BLE001
        logger.exception("[keyword-digest] tick crashed")
        return {"ok": False, "reason": f"crash: {exc}"}


# ---------------------------------------------------------------------
# Read helpers (admin dashboard)
# ---------------------------------------------------------------------
async def list_runs(*, limit: int = 20) -> List[Dict[str, Any]]:
    cursor = db[RUNS_COLLECTION].find({}).sort("run_at", -1).limit(int(limit))
    out: List[Dict[str, Any]] = []
    async for d in cursor:
        d.pop("_id", None)
        out.append(d)
    return out


__all__ = [
    "DEFAULT_CFG",
    "DEFAULT_RULES",
    "build_query",
    "build_hit_message",
    "ensure_indexes",
    "get_config",
    "update_config",
    "render_suggested_reply",
    "run_digest",
    "should_fire",
    "tick",
    "list_runs",
]
