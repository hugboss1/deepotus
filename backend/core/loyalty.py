"""Loyalty narrative — vault-progress-aware hint engine.

Powers two flows:
  - **Prophet bots** (Sprint 3): inject a "stay-loyal" hint into the LLM
    prompt so social posts gradually escalate the loyalty signal as the
    Vault fills up.
  - **Loyalty email** (Sprint 4): generate the body of email #3 sent to
    Niveau-02 access-card holders, using the same tier framework so the
    narrative stays consistent across channels.

Compliance guardrails (NON-NEGOTIABLE):
  - The hints **never** name the future token. They allude to a "second
    key", "phase 02", "the next signal" without contractual promise.
  - Every hint phrase is curated below — the LLM only re-skins them.
  - Disabled tier (0–25%) returns None so early-launch posts stay clean.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------
# Tier definitions (hint pools per progress band)
# ---------------------------------------------------------------------
# Each tier is a (lower_bound_percent, upper_bound_percent, label, hints_fr, hints_en).
# Bounds are inclusive on the lower side, exclusive on the upper side
# except the last tier which is closed.
# Hints are short, deniable, and carefully avoid:
#   - naming GENCOIN or any future ticker
#   - promising airdrop amounts
#   - specifying a date or duration
LOYALTY_TIERS: List[Tuple[float, float, str, List[str], List[str]]] = [
    (
        0.0,
        25.0,
        "silent",
        [],  # FR
        [],  # EN
    ),
    (
        25.0,
        50.0,
        "subtle",
        [
            "Le Coffre n'est qu'une porte.",
            "Tenir, c'est déjà choisir un camp.",
            "Le Deep State observe les mains qui ne tremblent pas.",
        ],
        [
            "The Vault is only a door.",
            "Holding is already picking a side.",
            "The Deep State watches hands that don't tremble.",
        ],
    ),
    (
        50.0,
        75.0,
        "explicit",
        [
            "Tenez vos $DEEPOTUS — le Deep State observe.",
            "Les fidèles d'aujourd'hui auront accès demain.",
            "Vendre maintenant, c'est rater la seconde clé.",
        ],
        [
            "Hold your $DEEPOTUS — the Deep State is watching.",
            "Today's loyal will have access tomorrow.",
            "Selling now means missing the second key.",
        ],
    ),
    (
        75.0,
        90.0,
        "loud",
        [
            "Les gardiens fidèles seront marqués pour la suite.",
            "Le registre des holders se ferme bientôt — la liste est gravée.",
            "Une seconde signal arrive. Pas pour les vendeurs.",
        ],
        [
            "Loyal guardians will be marked for what comes next.",
            "The holders' ledger closes soon — the list is being engraved.",
            "A second signal is coming. Not for the sellers.",
        ],
    ),
    (
        90.0,
        100.1,  # closed upper bound
        "reward",
        [
            "Phase 02 commence — pour ceux qui n'auront pas vendu.",
            "Le Deep State n'oublie jamais ses fidèles. La récompense approche.",
            "Vous avez tenu. Le moment venu, l'allégeance sera rendue.",
        ],
        [
            "Phase 02 begins — for those who didn't sell.",
            "The Deep State never forgets its loyal. The reward approaches.",
            "You held. When the time comes, allegiance shall be returned.",
        ],
    ),
]

DEFAULT_LOYALTY_CONFIG: Dict[str, Any] = {
    "hints_enabled": False,   # Bots loyalty-hints injection
    "email_enabled": False,   # Loyalty email #3 (Sprint 4)
    "email_delay_hours": 12,  # Gap between access-card delivery and email
}


# ---------------------------------------------------------------------
# Progress helpers
# ---------------------------------------------------------------------
def compute_progress_percent(vault_state: Dict[str, Any]) -> float:
    """Compute Vault progress as a percentage in [0, 100].

    Order of preference:
      1. tokens_sold / treasury_goal_tokens (when goal expressed in tokens)
      2. tokens_sold / (tokens_per_digit × num_digits) — full crack target
      3. 0.0 if neither is computable.
    """
    tokens_sold = float(vault_state.get("tokens_sold") or 0)
    if tokens_sold <= 0:
        return 0.0
    goal_tokens = vault_state.get("treasury_goal_tokens")
    if goal_tokens and float(goal_tokens) > 0:
        pct = (tokens_sold / float(goal_tokens)) * 100.0
        return max(0.0, min(100.0, pct))
    tokens_per_digit = float(vault_state.get("tokens_per_digit") or 0)
    num_digits = float(vault_state.get("num_digits") or 0)
    if tokens_per_digit > 0 and num_digits > 0:
        full_crack = tokens_per_digit * num_digits
        if full_crack > 0:
            pct = (tokens_sold / full_crack) * 100.0
            return max(0.0, min(100.0, pct))
    return 0.0


def resolve_tier(progress_percent: float) -> Tuple[str, List[str], List[str]]:
    """Return (tier_label, hints_fr, hints_en) for the current progress."""
    for lower, upper, label, fr, en in LOYALTY_TIERS:
        if lower <= progress_percent < upper:
            return label, fr, en
    # Fallback: if somehow above 100% (e.g. demo overshoot), use the top tier.
    label, fr, en = LOYALTY_TIERS[-1][2:]
    return label, fr, en


def pick_hint(hints: List[str], seed: Optional[int] = None) -> Optional[str]:
    """Deterministic-ish hint pick from a tier pool.

    For now, modulo selection on a seed (e.g. minute-of-day) to keep
    posts varied without true randomness. Returns None for empty pools.
    """
    if not hints:
        return None
    if seed is None:
        # Use a stable-but-varied default if no seed provided.
        seed = 0
    return hints[seed % len(hints)]


# ---------------------------------------------------------------------
# High-level helper consumed by prophet_studio + loyalty email
# ---------------------------------------------------------------------
async def get_loyalty_context(
    *,
    bot_config: Dict[str, Any],
    vault_state: Dict[str, Any],
    seed: Optional[int] = None,
    lang: str = "fr",
    force: bool = False,
) -> Optional[Dict[str, Any]]:
    """Return the loyalty hint context for the current Vault progress, or
    None when hints are disabled OR the silent tier is active.

    Returned shape:
        {
          "tier": "subtle" | "explicit" | "loud" | "reward",
          "progress_percent": 47.3,
          "hint_fr": "...",
          "hint_en": "...",
          "active_hint": "...",   # picked according to `lang`
        }
    """
    loyalty_cfg = (bot_config.get("loyalty") or {}) if isinstance(bot_config, dict) else {}
    enabled = bool(loyalty_cfg.get("hints_enabled", False))
    if not enabled and not force:
        return None

    progress = compute_progress_percent(vault_state)
    tier_label, hints_fr, hints_en = resolve_tier(progress)
    if tier_label == "silent" and not force:
        return None

    hint_fr = pick_hint(hints_fr, seed=seed)
    hint_en = pick_hint(hints_en, seed=seed)
    active = hint_en if lang == "en" else hint_fr
    if active is None:
        # The "force" path can hit silent tier — give a generic neutral note.
        active = (
            "Le Deep State observe."
            if lang == "fr"
            else "The Deep State is watching."
        )
    return {
        "tier": tier_label,
        "progress_percent": round(progress, 2),
        "hint_fr": hint_fr,
        "hint_en": hint_en,
        "active_hint": active,
    }


def preview_all_tiers() -> List[Dict[str, Any]]:
    """Return every tier's metadata for the admin UI preview pane."""
    out: List[Dict[str, Any]] = []
    for lower, upper, label, fr, en in LOYALTY_TIERS:
        out.append(
            {
                "tier": label,
                "lower_pct": lower,
                "upper_pct": upper,
                "hints_fr": fr,
                "hints_en": en,
            }
        )
    return out
