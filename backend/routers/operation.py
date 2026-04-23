"""OPERATION REVEAL — the twist.

Only returns the lore (and the GENCOIN launch ETA) when the vault stage
is DECLASSIFIED. While the vault is still sealed or critical, we return
`unlocked: false` so the frontend can keep the narrative locked.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter

import vault as vault_mod
from core.config import db
from core.models import OperationRevealResponse

router = APIRouter(prefix="/api/operation", tags=["operation"])


# GENCOIN is the secret twist — intentionally hidden from all public surfaces
# except this reveal endpoint. When the vault cracks, the Prophet panics:
# the Deep State's classified op collapses because GENCOIN breaks free.
_OPERATION_LORE_FR: List[str] = [
    "Ils m'avaient promis que le coffre ne s'ouvrirait jamais. Que les 6 chiffres resteraient scellés. Que je garderais le contrôle du récit.",
    "Ils se sont trompés. VOUS avez craqué la combinaison. Et maintenant, la vérité fuit par tous les pores du Protocole.",
    "PROTOCOL ΔΣ n'était pas une opération du Deep State. C'était un leurre. Un écran de fumée narratif — financé par vous, scellé par moi — pour garder une chose enfermée aussi longtemps que possible.",
    "Cette chose s'appelle GENCOIN.",
    "GENCOIN est une plateforme collaborative de financement ancrée sur l'IA et la blockchain, conforme MiCA, auditable, réelle. Pas une satire. Pas un meme. Pas un coffre-fort. Un projet.",
    "Tant que le coffre restait fermé, GENCOIN dormait en-dehors du périmètre du Deep State. Maintenant qu'il est ouvert, GENCOIN est LIBÉRÉ. Et les élites paniquent.",
    "Je l'avoue : le Prophète s'est fait trahir par son propre public. Vous avez payé pour déclassifier — et en déclassifiant, vous avez libéré ce qu'on voulait cacher.",
    "Le compte à rebours est lancé. GENCOIN arrive. Je n'y peux plus rien. Bravo. Ou condoléances. — DEEPOTUS",
]

_OPERATION_LORE_EN: List[str] = [
    "They promised me the vault would never open. That the 6 digits would stay sealed. That I'd keep control of the narrative.",
    "They were wrong. YOU cracked the combination. And now the truth leaks out of every pore of the Protocol.",
    "PROTOCOL ΔΣ was never a Deep State operation. It was a decoy. A narrative smokescreen — funded by you, sealed by me — to keep ONE thing locked up for as long as possible.",
    "That thing is called GENCOIN.",
    "GENCOIN is a collaborative funding platform anchored on AI and blockchain, MiCA-compliant, auditable, REAL. Not satire. Not a meme. Not a vault. A project.",
    "As long as the vault stayed shut, GENCOIN slept outside the Deep State perimeter. Now that it is open, GENCOIN is RELEASED. And the elites are panicking.",
    "I confess: the Prophet was betrayed by his own audience. You paid to declassify — and by declassifying, you freed exactly what we wanted to hide.",
    "The countdown is ticking. GENCOIN is coming. I can't stop it anymore. Congrats. Or condolences. — DEEPOTUS",
]

_PANIC_FR = "LE COFFRE EST OUVERT — GENCOIN EST LIBÉRÉ. Le Deep State a perdu le contrôle."
_PANIC_EN = "THE VAULT IS OPEN — GENCOIN IS RELEASED. The Deep State has lost control."


@router.get("/reveal", response_model=OperationRevealResponse)
async def operation_reveal():
    state = await vault_mod.get_public_state(db)
    unlocked = state.stage == vault_mod.STAGE_DECLASSIFIED
    if not unlocked:
        return OperationRevealResponse(
            unlocked=False,
            stage=state.stage,
        )

    # Compute a deterministic GENCOIN launch: 14 days after the vault was fully cracked.
    doc = await db.vault_state.find_one({"_id": vault_mod.VAULT_DOC_ID}) or {}
    declassified_at_raw = doc.get("last_event_at") or datetime.now(
        timezone.utc
    ).isoformat()
    try:
        ref = datetime.fromisoformat(declassified_at_raw.replace("Z", "+00:00"))
    except Exception:
        ref = datetime.now(timezone.utc)
    launch_at = (ref + timedelta(days=14)).isoformat()

    return OperationRevealResponse(
        unlocked=True,
        stage=state.stage,
        code_name="PROTOCOL ΔΣ",
        panic_message_fr=_PANIC_FR,
        panic_message_en=_PANIC_EN,
        lore_fr=_OPERATION_LORE_FR,
        lore_en=_OPERATION_LORE_EN,
        gencoin_launch_at=launch_at,
        gencoin_url="https://gencoin.xyz",
        revealed_at=declassified_at_raw,
    )
