"""News feed aggregator for the $DEEPOTUS Prophet bot.

Pulls a curated list of free RSS feeds (BBC, Al Jazeera, France 24,
Yahoo Finance, The Economist, etc.), filters by relevance keywords
(geopolitics + macro economics), dedupes, and stores the result in the
`news_items` Mongo collection so the Prophet Studio can inject the
freshest geopolitical / macro headlines as inspiration when generating
posts.

Public API:
    DEFAULT_NEWS_FEEDS, DEFAULT_NEWS_KEYWORDS
    refresh_all(urls, keywords) -> {"added": N, "fetched": M, "skipped": K}
    get_recent_items(hours, limit) -> List[news_item]
    pick_inspiration_headlines(n) -> List[str]
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

import feedparser

from core.config import db, logger

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------
NEWS_COLLECTION = "news_items"
NEWS_TTL_HOURS = 24 * 7  # keep one week of feed history

# Default RSS feed URLs — geopolitics + macro economics, all free, all without API key
DEFAULT_NEWS_FEEDS: List[str] = [
    # ---- Geopolitics / world ----
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.france24.com/en/rss",
    "https://www.france24.com/fr/rss",
    # ---- Macro / business ----
    "http://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.economist.com/the-world-this-week/rss.xml",
    "https://finance.yahoo.com/news/rssindex",
]

# Geopolitics + macro econ default filter keywords (lowercased)
DEFAULT_NEWS_KEYWORDS: List[str] = [
    # Geopolitics
    "war",
    "ukraine",
    "russia",
    "israel",
    "gaza",
    "iran",
    "china",
    "taiwan",
    "sanction",
    "nato",
    "brics",
    "g7",
    "g20",
    "election",
    "treaty",
    "diplomacy",
    "summit",
    "embassy",
    "missile",
    "ceasefire",
    "geopolit",
    # Macro economics
    "fed",
    "ecb",
    "inflation",
    "recession",
    "central bank",
    "tariff",
    "opec",
    "gold",
    "oil",
    "trade",
    "currency",
    "debt",
    "imf",
    "world bank",
    "bond",
    "yields",
    "rate hike",
    "rate cut",
    "stimulus",
    "deficit",
    "macro",
]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _hash_id(source: str, url: str, title: str) -> str:
    """Deterministic ID so the same article isn't stored twice."""
    h = hashlib.sha256()
    h.update(source.encode("utf-8", errors="ignore"))
    h.update(b"|")
    h.update(url.encode("utf-8", errors="ignore"))
    h.update(b"|")
    h.update(title.encode("utf-8", errors="ignore"))
    return h.hexdigest()[:32]


def _matches_any(text: str, keywords: Iterable[str]) -> bool:
    """Lowercase substring match — keyword filter for relevance."""
    if not keywords:
        return True
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in keywords if kw)


def _parse_feed_blocking(url: str) -> List[Dict[str, Any]]:
    """Synchronous fetch + parse — runs in a thread executor.

    feedparser is synchronous and can take a few hundred ms per feed; we
    isolate it in a worker thread so the event loop stays free.
    """
    parsed = feedparser.parse(url)
    source = (
        getattr(parsed.feed, "title", None)
        or urlparse(url).netloc
        or "unknown"
    )
    out: List[Dict[str, Any]] = []
    for entry in parsed.entries[:50]:  # hard cap per feed
        title = getattr(entry, "title", "") or ""
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        link = getattr(entry, "link", "") or ""
        published = (
            getattr(entry, "published", None)
            or getattr(entry, "updated", None)
            or ""
        )
        out.append(
            {
                "title": title.strip(),
                "summary": summary.strip()[:1200],
                "url": link.strip(),
                "source": str(source).strip(),
                "published_raw": published,
            }
        )
    return out


async def _fetch_one(url: str) -> List[Dict[str, Any]]:
    """Async wrapper around the blocking feedparser call."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _parse_feed_blocking, url)
    except Exception as exc:  # noqa: BLE001
        logging.warning("[news_feed] failed to parse feed=%s err=%s", url, exc)
        return []


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
async def refresh_all(
    urls: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Fetch ALL configured feeds in parallel, filter, dedupe, persist.

    Returns a tally of {"fetched", "kept", "added"} so admins can see
    at a glance how a given fetch went.
    """
    feeds = urls or DEFAULT_NEWS_FEEDS
    kw = keywords if keywords is not None else DEFAULT_NEWS_KEYWORDS

    fetched_lists = await asyncio.gather(*(_fetch_one(u) for u in feeds))
    fetched_total = sum(len(lst) for lst in fetched_lists)
    now_iso = datetime.now(timezone.utc).isoformat()

    kept = 0
    added = 0
    for items in fetched_lists:
        for item in items:
            txt = f"{item.get('title', '')} {item.get('summary', '')}"
            if not _matches_any(txt, kw):
                continue
            kept += 1
            doc_id = _hash_id(
                item.get("source", ""),
                item.get("url", ""),
                item.get("title", ""),
            )
            doc = {
                "_id": doc_id,
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "source": item.get("source", ""),
                "published_raw": item.get("published_raw", ""),
                "fetched_at": now_iso,
            }
            res = await db[NEWS_COLLECTION].update_one(
                {"_id": doc_id},
                {"$setOnInsert": doc, "$set": {"last_seen_at": now_iso}},
                upsert=True,
            )
            if res.upserted_id:
                added += 1

    # Prune items older than the TTL (defensive — also cheap)
    cutoff_iso = (
        datetime.now(timezone.utc) - timedelta(hours=NEWS_TTL_HOURS)
    ).isoformat()
    await db[NEWS_COLLECTION].delete_many({"fetched_at": {"$lt": cutoff_iso}})

    logger.info(
        "[news_feed] refresh fetched=%d kept=%d new=%d feeds=%d",
        fetched_total,
        kept,
        added,
        len(feeds),
    )
    return {
        "fetched": fetched_total,
        "kept": kept,
        "added": added,
        "feeds": len(feeds),
        "ts": now_iso,
    }


async def get_recent_items(
    hours: int = 48,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Return the most recent kept news items (for admin preview)."""
    cutoff_iso = (
        datetime.now(timezone.utc) - timedelta(hours=hours)
    ).isoformat()
    cursor = (
        db[NEWS_COLLECTION]
        .find({"fetched_at": {"$gte": cutoff_iso}})
        .sort("fetched_at", -1)
        .limit(limit)
    )
    rows = await cursor.to_list(length=limit)
    return [
        {
            "id": str(r.get("_id")),
            "title": r.get("title", ""),
            "summary": r.get("summary", ""),
            "url": r.get("url", ""),
            "source": r.get("source", ""),
            "published_raw": r.get("published_raw", ""),
            "fetched_at": r.get("fetched_at", ""),
        }
        for r in rows
    ]


async def pick_inspiration_headlines(n: int = 5) -> List[str]:
    """Return up to N short headline strings the Prophet can riff on.

    Format: `"[Source] Title — Summary (truncated)"`. Keeps tokens short
    so multiple headlines fit in the LLM context comfortably.
    """
    items = await get_recent_items(hours=48, limit=max(n * 2, 10))
    out: List[str] = []
    for it in items[:n]:
        title = it.get("title") or ""
        source = it.get("source") or ""
        summary = (it.get("summary") or "").replace("\n", " ").strip()
        if len(summary) > 220:
            summary = summary[:217] + "…"
        if title:
            line = f"[{source}] {title}"
            if summary:
                line += f" — {summary}"
            out.append(line)
    return out


async def build_news_context_block(n: int = 5) -> Optional[str]:
    """Render the headlines as an `extra_context` snippet ready for the LLM.

    Returns None when there's nothing to ground the post on, so the
    caller can decide whether to skip injection.
    """
    headlines = await pick_inspiration_headlines(n=n)
    if not headlines:
        return None
    bulleted = "\n".join(f"- {h}" for h in headlines)
    return (
        "Latest geopolitics / macro headlines (use one or two of them as "
        "the spark of your cynical commentary, do NOT cite them verbatim, "
        "stay in character):\n" + bulleted
    )
