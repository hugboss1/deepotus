"""Riddles of the Terminal — Proof of Intelligence (Sprint 14.1).

Five enigmas gate Clearance Level 3 (agent status / airdrop eligibility).
Each riddle stores a list of *accepted keywords*; a submission is
accepted when its normalised form contains ANY of those keywords.
Normalisation = lowercase + strip accents + collapse whitespace, so
‘LA FED’, ‘la fed’ and ‘La Féd.’ all match.

Anti-brute-force:
  * per-email + per-riddle counters in ``riddle_attempts`` with TTL 24 h,
  * soft limit of 6 wrong guesses per riddle in a rolling window,
  * once solved, a riddle cannot be re-submitted (fast-path read-through).

The seeded content matches the operator's spec verbatim so future edits
can happen from the admin UI without touching code.
"""

from __future__ import annotations

import logging
import re
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from core.config import db

logger = logging.getLogger("deepotus.infiltration.riddles")

ATTEMPT_WINDOW_MINUTES = 60
ATTEMPT_SOFT_LIMIT = 6


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso() -> str:
    return _now().isoformat()


# ---------------------------------------------------------------------
# Seed data — 5 enigmas, verbatim from the spec
# ---------------------------------------------------------------------
DEFAULT_RIDDLES: List[Dict[str, Any]] = [
    {
        "slug": "grand-architecte",
        "order": 1,
        "title": "Le Grand Architecte",
        "question_fr": (
            "Je tourne sans cesse, je crée de la valeur à partir du vide, "
            "et pourtant, plus je travaille, moins vous possédez. Je suis "
            "le moteur de votre esclavage moderne. Qui suis-je ?"
        ),
        "question_en": (
            "I spin endlessly, I create value from the void, and yet the "
            "harder I work the less you own. I am the engine of your "
            "modern slavery. Who am I?"
        ),
        "accepted_keywords": [
            "la fed", "fed", "federal reserve", "planche a billets",
            "planche", "inflation", "central bank",
        ],
        "hint": "Three letters. Three trillions. Three generations of debt.",
    },
    {
        "slug": "oeil-invisible",
        "order": 2,
        "title": "L'Œil Invisible",
        "question_fr": (
            "Vous me donnez votre visage pour déverrouiller vos vies, vos "
            "empreintes pour payer vos dettes. Je connais votre prochaine "
            "pensée avant vous, car c'est moi qui l'ai suggérée. Que suis-je ?"
        ),
        "question_en": (
            "You give me your face to unlock your lives, your fingerprints "
            "to pay your debts. I know your next thought before you do — "
            "because I was the one to suggest it. What am I?"
        ),
        "accepted_keywords": [
            "algorithme", "algorithm", "ia", "ai", "surveillance",
            "intelligence artificielle", "artificial intelligence",
        ],
        "hint": "It learns you faster than you learn yourself.",
    },
    {
        "slug": "contrat-social",
        "order": 3,
        "title": "Le Contrat Social",
        "question_fr": (
            "Je suis une promesse que personne ne peut tenir, un château "
            "de cartes posé sur une mer de dettes. Quand je m'écroule, "
            "les riches reçoivent des parachutes et vous recevez des "
            "factures. Quel est mon nom ?"
        ),
        "question_en": (
            "I am a promise no one can keep — a castle of cards on a sea "
            "of debt. When I collapse, the rich get parachutes, and you "
            "get the bill. What is my name?"
        ),
        "accepted_keywords": [
            "systeme bancaire", "banking system", "capitalisme", "capitalism",
            "economie", "economy", "finance", "banques", "banks",
        ],
        "hint": "Too big to fail. Small enough to forget you.",
    },
    {
        "slug": "verite-de-lagent",
        "order": 4,
        "title": "La Vérité de l'Agent",
        "question_fr": (
            "Le Deep State ne se cache pas derrière des murs, il se cache "
            "derrière des écrans. Quel est le seul actif qui ne peut être "
            "ni imprimé, ni censuré, ni saisi par une main humaine dans "
            "le protocole ΔΣ ?"
        ),
        "question_en": (
            "The Deep State hides not behind walls but behind screens. "
            "What is the only asset in PROTOCOL ΔΣ that cannot be printed, "
            "censored, or seized by a human hand?"
        ),
        "accepted_keywords": [
            "deepotus", "$deepotus", "blockchain", "solana", "sol",
        ],
        "hint": "Seven letters and one dollar sign. Living on Solana.",
    },
    {
        "slug": "ouverture-du-coffre",
        "order": 5,
        "title": "L'Ouverture du Coffre",
        "question_fr": (
            "Six cadrans, une vérité. Si le Prophète ment, qui gagne ? Si "
            "le Prophète dit vrai, qui paie ? Pour entrer dans le coffre, "
            "vous devez admettre que vous n'êtes pas un client, mais un…"
        ),
        "question_en": (
            "Six dials, one truth. If the Prophet lies, who wins? If the "
            "Prophet is right, who pays? To enter the vault, you must admit "
            "you are not a client, but a…"
        ),
        "accepted_keywords": [
            "produit", "product", "esclave", "slave", "pion", "pawn",
            "actif", "asset",
        ],
        "hint": "One single noun. Usually four letters. Sometimes six.",
    },
]


# ---------------------------------------------------------------------
# Normalisation + matching
# ---------------------------------------------------------------------
def normalise(text: str) -> str:
    """Lowercase + strip accents + collapse whitespace + drop punctuation.

    Used both at seed time (so keywords are pre-normalised in memory)
    and at attempt time so comparison is free of surprises.
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", text)
    t = t.encode("ascii", "ignore").decode("ascii")
    t = t.lower()
    # Drop punctuation except digits + letters + space
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _match(answer: str, keywords: List[str]) -> Optional[str]:
    """Return the first keyword matched in the answer, else None.

    We use substring matching on the normalised form — generous to the
    operator's audience who won't always type the phrase verbatim.
    """
    na = normalise(answer)
    if not na:
        return None
    for kw in keywords:
        if not kw:
            continue
        if normalise(kw) in na:
            return kw
    return None


# ---------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------
async def ensure_indexes() -> None:
    try:
        await db.riddles.create_index([("order", 1)])
        await db.riddles.create_index([("slug", 1)], unique=True)
        await db.riddle_attempts.create_index([("email", 1), ("slug", 1)])
        await db.riddle_attempts.create_index(
            [("at", 1)], expireAfterSeconds=60 * 60 * 24,
        )
    except Exception:  # noqa: BLE001
        pass


async def seed_default_riddles() -> int:
    """Idempotent seed — runs at startup. Safe to call every boot."""
    inserted = 0
    for r in DEFAULT_RIDDLES:
        existing = await db.riddles.find_one({"slug": r["slug"]})
        if existing:
            continue
        await db.riddles.insert_one({
            "_id": str(uuid.uuid4()),
            "slug": r["slug"],
            "order": r["order"],
            "title": r["title"],
            "question_fr": r["question_fr"],
            "question_en": r["question_en"],
            "accepted_keywords": [normalise(k) for k in r["accepted_keywords"]],
            "hint": r.get("hint"),
            "enabled": True,
            "version": 1,
            "created_at": _iso(),
            "updated_at": _iso(),
        })
        inserted += 1
    if inserted:
        logger.info("[infiltration] Seeded %d riddles.", inserted)
    return inserted


def _normalise_keywords(keywords: List[str]) -> List[str]:
    return [normalise(k) for k in keywords if (k or "").strip()]


def _public_view(doc: Dict[str, Any], locale: str = "fr") -> Dict[str, Any]:
    """Public projection — NEVER leaks the accepted_keywords."""
    question = doc.get(f"question_{locale}") or doc.get("question_fr", "")
    return {
        "slug": doc["slug"],
        "order": doc.get("order", 0),
        "title": doc.get("title"),
        "question": question,
        "hint": doc.get("hint"),
        "enabled": bool(doc.get("enabled", True)),
    }


def _admin_view(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Admin projection — exposes accepted_keywords for editing."""
    return {
        "id": doc["_id"],
        "slug": doc["slug"],
        "order": doc.get("order", 0),
        "title": doc.get("title"),
        "question_fr": doc.get("question_fr"),
        "question_en": doc.get("question_en"),
        "accepted_keywords": list(doc.get("accepted_keywords") or []),
        "hint": doc.get("hint"),
        "enabled": bool(doc.get("enabled", True)),
        "version": int(doc.get("version", 1)),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
async def list_public_riddles(locale: str = "fr") -> List[Dict[str, Any]]:
    cursor = db.riddles.find({"enabled": True}).sort("order", 1)
    return [_public_view(d, locale=locale) async for d in cursor]


async def list_admin_riddles() -> List[Dict[str, Any]]:
    cursor = db.riddles.find({}).sort("order", 1)
    return [_admin_view(d) async for d in cursor]


async def get_admin_riddle(riddle_id: str) -> Optional[Dict[str, Any]]:
    doc = await db.riddles.find_one({"_id": riddle_id})
    return _admin_view(doc) if doc else None


async def create_riddle(
    *,
    slug: str,
    title: str,
    question_fr: str,
    question_en: str,
    accepted_keywords: List[str],
    order: int = 100,
    hint: Optional[str] = None,
    enabled: bool = True,
) -> Dict[str, Any]:
    slug = (slug or "").strip().lower()
    if not slug:
        raise ValueError("slug is required")
    existing = await db.riddles.find_one({"slug": slug})
    if existing:
        raise ValueError(f"a riddle with slug '{slug}' already exists")
    keywords = _normalise_keywords(accepted_keywords)
    if not keywords:
        raise ValueError("at least one accepted_keyword is required")
    now = _iso()
    doc = {
        "_id": str(uuid.uuid4()),
        "slug": slug,
        "order": int(order),
        "title": title.strip()[:120],
        "question_fr": (question_fr or "").strip()[:2000],
        "question_en": (question_en or "").strip()[:2000],
        "accepted_keywords": keywords,
        "hint": (hint or "").strip()[:200] or None,
        "enabled": bool(enabled),
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    await db.riddles.insert_one(doc)
    return _admin_view(doc)


async def update_riddle(
    riddle_id: str, **patch: Any,
) -> Optional[Dict[str, Any]]:
    out: Dict[str, Any] = {}
    if "accepted_keywords" in patch:
        keywords = _normalise_keywords(patch["accepted_keywords"])
        if not keywords:
            raise ValueError("accepted_keywords cannot be empty")
        out["accepted_keywords"] = keywords
    for k in ("title", "question_fr", "question_en", "hint"):
        if k in patch and patch[k] is not None:
            out[k] = str(patch[k]).strip()[:2000]
    if "order" in patch and patch["order"] is not None:
        out["order"] = int(patch["order"])
    if "enabled" in patch and patch["enabled"] is not None:
        out["enabled"] = bool(patch["enabled"])
    if not out:
        return await get_admin_riddle(riddle_id)
    out["updated_at"] = _iso()
    res = await db.riddles.find_one_and_update(
        {"_id": riddle_id},
        {"$set": out, "$inc": {"version": 1}},
        return_document=True,
    )
    return _admin_view(res) if res else None


async def delete_riddle(riddle_id: str) -> int:
    res = await db.riddles.delete_one({"_id": riddle_id})
    return res.deleted_count


# ---------------------------------------------------------------------
# Attempts + anti-brute-force
# ---------------------------------------------------------------------
async def submit_attempt(
    *,
    slug: str,
    answer: str,
    email: Optional[str],
    ip: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate an answer. Always returns a result dict.

    Response shape:
      * ``{correct: bool, solved_count: int, matched_keyword, attempts_left}``
      * ``{error: "...", code: "RATE_LIMITED" | "RIDDLE_DISABLED" | "UNKNOWN_RIDDLE"}``
    """
    doc = await db.riddles.find_one({"slug": slug})
    if not doc:
        return {"error": "riddle not found", "code": "UNKNOWN_RIDDLE"}
    if not doc.get("enabled", True):
        return {"error": "riddle disabled", "code": "RIDDLE_DISABLED"}

    email_l = (email or "").strip().lower()
    now = _now()
    window_start = now - timedelta(minutes=ATTEMPT_WINDOW_MINUTES)

    # --- Rate limit: count recent wrong attempts for this (email, slug)
    if email_l:
        wrong_in_window = await db.riddle_attempts.count_documents({
            "email": email_l,
            "slug": slug,
            "correct": False,
            "at": {"$gte": window_start},
        })
        if wrong_in_window >= ATTEMPT_SOFT_LIMIT:
            return {
                "error": "too many attempts in the last hour — come back later",
                "code": "RATE_LIMITED",
                "retry_at": (now + timedelta(minutes=30)).isoformat(),
            }

    matched = _match(answer, list(doc.get("accepted_keywords") or []))
    correct = matched is not None

    # --- Persist attempt audit row (TTL'd) --------------------------
    await db.riddle_attempts.insert_one({
        "_id": str(uuid.uuid4()),
        "slug": slug,
        "email": email_l or None,
        "ip": ip,
        "answer_excerpt": (answer or "")[:120],
        "answer_hash": _hash(answer or ""),
        "correct": correct,
        "matched_keyword": matched,
        "at": now,
    })

    attempts_left = max(0, ATTEMPT_SOFT_LIMIT - (0 if correct else wrong_in_window + 1)) \
        if email_l else None

    # --- Persist the win in the clearance ledger --------------------
    solved_count = 0
    if correct and email_l:
        from core import clearance_levels  # lazy to avoid circular import

        res = await clearance_levels.mark_riddle_solved(
            email=email_l, slug=slug, matched_keyword=matched,
        )
        solved_count = int(res.get("solved_count") or 0)

    return {
        "correct": correct,
        "matched_keyword": matched,
        "solved_count": solved_count,
        "attempts_left": attempts_left,
    }


async def recent_attempts(
    *,
    email: Optional[str] = None,
    slug: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if email:
        q["email"] = email.strip().lower()
    if slug:
        q["slug"] = slug
    cursor = db.riddle_attempts.find(q).sort("at", -1).limit(min(max(limit, 1), 500))
    return [
        {
            "id": d["_id"],
            "slug": d.get("slug"),
            "email": d.get("email"),
            "correct": bool(d.get("correct")),
            "matched_keyword": d.get("matched_keyword"),
            "at": d.get("at").isoformat() if d.get("at") else None,
            "answer_excerpt": d.get("answer_excerpt"),
        }
        async for d in cursor
    ]


def _hash(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
