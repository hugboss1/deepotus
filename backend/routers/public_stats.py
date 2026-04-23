"""Enriched public analytics for the landing page.

All counters, timeseries and distributions are aggregated server-side
from the `whitelist` and `chat_logs` collections. No PII is exposed.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from fastapi import APIRouter

from core.config import db
from core.models import (
    EvolutionPoint,
    LangDistribution,
    PublicStatsResponse,
    TopSessionItem,
)
from routers.public import get_launch_timestamp

router = APIRouter(prefix="/api/public", tags=["public-stats"])


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
async def compute_evolution(days: int) -> List[EvolutionPoint]:
    days = max(1, min(days, 365))
    today_utc = datetime.now(timezone.utc).date()
    start_utc = today_utc - timedelta(days=days - 1)

    wl_rows = await db.whitelist.find({}, {"created_at": 1, "_id": 0}).to_list(
        length=100000
    )
    ch_rows = await db.chat_logs.find({}, {"created_at": 1, "_id": 0}).to_list(
        length=500000
    )

    def parse_day(iso_str):
        try:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).date()
        except Exception:
            return None

    wl_daily: Dict[str, int] = {}
    for r in wl_rows:
        d = parse_day(r.get("created_at", ""))
        if d:
            k = d.isoformat()
            wl_daily[k] = wl_daily.get(k, 0) + 1

    ch_daily: Dict[str, int] = {}
    for r in ch_rows:
        d = parse_day(r.get("created_at", ""))
        if d:
            k = d.isoformat()
            ch_daily[k] = ch_daily.get(k, 0) + 1

    before_wl = sum(c for k, c in wl_daily.items() if k < start_utc.isoformat())
    before_ch = sum(c for k, c in ch_daily.items() if k < start_utc.isoformat())

    series: List[EvolutionPoint] = []
    wl_cum = before_wl
    ch_cum = before_ch

    for i in range(days):
        d = start_utc + timedelta(days=i)
        key = d.isoformat()
        w_d = wl_daily.get(key, 0)
        c_d = ch_daily.get(key, 0)
        wl_cum += w_d
        ch_cum += c_d
        series.append(
            EvolutionPoint(
                date=key,
                whitelist=wl_cum,
                chat=ch_cum,
                whitelist_daily=w_d,
                chat_daily=c_d,
            )
        )

    return series


def _anon_session(session_id: str) -> str:
    """Deterministic short hash of session_id — never reveals the original."""
    if not session_id:
        return "anon-XXXX"
    h = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    return f"anon-{h[:6].upper()}"


async def _top_sessions(n: int = 5) -> List[TopSessionItem]:
    pipeline = [
        {
            "$group": {
                "_id": "$session_id",
                "count": {"$sum": 1},
                "lang": {"$last": "$lang"},
                "first": {"$min": "$created_at"},
                "last": {"$max": "$created_at"},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": n},
    ]
    rows = await db.chat_logs.aggregate(pipeline).to_list(length=n)
    return [
        TopSessionItem(
            anon_id=_anon_session(r["_id"] or ""),
            lang=r.get("lang", "fr"),
            message_count=int(r.get("count", 0)),
            first_seen_at=r.get("first"),
            last_seen_at=r.get("last"),
        )
        for r in rows
    ]


async def _lang_distribution() -> Dict[str, LangDistribution]:
    wl = await db.whitelist.aggregate(
        [{"$group": {"_id": "$lang", "count": {"$sum": 1}}}]
    ).to_list(length=10)
    ch = await db.chat_logs.aggregate(
        [{"$group": {"_id": "$lang", "count": {"$sum": 1}}}]
    ).to_list(length=10)

    def _to(obj):
        out = LangDistribution()
        for it in obj:
            key = (it.get("_id") or "fr").lower()
            if key == "fr":
                out.fr = int(it.get("count", 0))
            elif key == "en":
                out.en = int(it.get("count", 0))
        return out

    return {"whitelist": _to(wl), "chat": _to(ch)}


async def _activity_heatmap(days: int = 30) -> List[List[int]]:
    """7 rows (Mon=0 .. Sun=6) x 24 cols (hour UTC). Count of chat messages."""
    today_utc = datetime.now(timezone.utc).date()
    start_utc = today_utc - timedelta(days=days - 1)
    start_iso = datetime.combine(
        start_utc, datetime.min.time(), tzinfo=timezone.utc
    ).isoformat()

    grid = [[0 for _ in range(24)] for _ in range(7)]
    rows = await db.chat_logs.find(
        {"created_at": {"$gte": start_iso}}, {"created_at": 1, "_id": 0}
    ).to_list(length=200000)

    for r in rows:
        try:
            dt = datetime.fromisoformat(
                r.get("created_at", "").replace("Z", "+00:00")
            )
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)
            dow = dt_utc.weekday()  # Mon=0..Sun=6
            hour = dt_utc.hour
            grid[dow][hour] += 1
        except Exception:
            continue
    return grid


# ---------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------
@router.get("/stats", response_model=PublicStatsResponse)
async def public_stats(days: int = 30):
    days = max(1, min(days, 90))
    wl = await db.whitelist.count_documents({})
    chat_ct = await db.chat_logs.count_documents({})
    prophecies = 0
    c = await db.counters.find_one({"_id": "prophecies"})
    if c:
        prophecies = int(c.get("count", 0))
    series = await compute_evolution(days)
    lang_dist = await _lang_distribution()
    tops = await _top_sessions(5)
    heatmap = await _activity_heatmap(30)

    return PublicStatsResponse(
        whitelist_count=wl,
        chat_messages=chat_ct,
        prophecies_served=prophecies,
        launch_timestamp=await get_launch_timestamp(),
        generated_at=datetime.now(timezone.utc).isoformat(),
        series_days=days,
        series=series,
        lang_distribution=lang_dist,
        top_sessions=tops,
        activity_heatmap=heatmap,
    )
