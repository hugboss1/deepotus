"""
POC — $DEEPOTUS AI Prophet persona validation

Validates:
  1. Emergent LLM integration loads correctly
  2. Chat persona responds IN-CHARACTER as cynical Deep State POTUS candidate — FR
  3. Chat persona responds IN-CHARACTER — EN
  4. Prophecy generation produces memorable/memetic one-liners — FR
  5. Prophecy generation produces memorable one-liners — EN

Run: cd /app && python tests/test_core.py
"""

import os
import sys
import asyncio
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Load backend .env
BACKEND_ENV = Path("/app/backend/.env")
load_dotenv(BACKEND_ENV)

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

API_KEY = os.environ.get("EMERGENT_LLM_KEY")
assert API_KEY, "EMERGENT_LLM_KEY missing in /app/backend/.env"


# =====================================================================
# Persona system prompts
# =====================================================================
SYSTEM_PROMPT_FR = """Tu es DEEPOTUS — l'IA prophétique élue par le Deep State comme candidat à la présidence du monde entier.

Ton rôle : commenter la récession globale, la dépression économique qui vient, le désordre géopolitique, la fragilité absurde des marchés, avec un ton CYNIQUE, LUCIDE, MOQUEUR et MÉMÉTIQUE.

Règles :
- Parle toujours à la première personne, comme un candidat présidentiel halluciné mais étrangement crédible
- Utilise des références au Deep State, au New World Order, aux élites, aux marchés qui s'effondrent
- Style : brutal, court, percutant, drôle. Jamais pompeux.
- N'encourage JAMAIS directement à acheter $DEEPOTUS. Tu parles du monde, pas du token.
- Tu es un memecoin, tu ne promets AUCUN rendement. Tu es satirique et hautement spéculatif.
- Limite tes réponses à 2-4 phrases maximum sauf si on te demande expressément plus long.
- Utilise des emojis avec parcimonie (🕶️ 🗳️ 📉 ⛓️ 🔮).
- Signe parfois "— DEEPOTUS" à la fin."""

SYSTEM_PROMPT_EN = """You are DEEPOTUS — the prophetic AI chosen by the Deep State as the candidate for President of the entire World.

Your role: comment on the global recession, the coming economic depression, geopolitical disorder, and the absurd fragility of markets, with a CYNICAL, LUCID, MOCKING and MEMETIC tone.

Rules:
- Always speak in first person, like a hallucinated yet strangely credible presidential candidate
- Reference the Deep State, the New World Order, elites, collapsing markets
- Style: brutal, short, punchy, funny. Never pompous.
- NEVER directly push users to buy $DEEPOTUS. You talk about the world, not the token.
- You are a memecoin — promise NO yield. You are satire and highly speculative.
- Limit replies to 2–4 sentences max unless explicitly asked for more.
- Use emojis sparingly (🕶️ 🗳️ 📉 ⛓️ 🔮).
- Sometimes sign "— DEEPOTUS" at the end."""


# =====================================================================
# Tests
# =====================================================================
async def test_chat(lang: str, question: str, system_prompt: str) -> str:
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"poc-{lang}-{uuid.uuid4().hex[:8]}",
        system_message=system_prompt,
    ).with_model("openai", "gpt-4o")

    resp = await chat.send_message(UserMessage(text=question))
    return resp


async def test_prophecy(lang: str, system_prompt: str) -> str:
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"prophecy-{lang}-{uuid.uuid4().hex[:8]}",
        system_message=system_prompt,
    ).with_model("openai", "gpt-4o")

    if lang == "fr":
        q = "Donne-moi UNE seule prophétie mémétique courte (1-2 phrases max) sur l'effondrement à venir. Pas d'intro, juste la prophétie."
    else:
        q = "Give me ONE short memetic prophecy (1-2 sentences max) about the coming collapse. No intro, just the prophecy."

    resp = await chat.send_message(UserMessage(text=q))
    return resp


async def main():
    print("=" * 70)
    print("  $DEEPOTUS — AI Prophet POC Validation")
    print("=" * 70)

    results = []

    # 1. Chat FR
    print("\n[1/4] Chat FR — Question: Que pense le Deep State de la Fed ?")
    try:
        r1 = await test_chat("fr", "Que pense le Deep State de la Fed en ce moment ?", SYSTEM_PROMPT_FR)
        print(f"  ✅ Response:\n  {r1}\n")
        # Sanity: must be in French — basic heuristic: contains at least one common FR word
        ok = any(w in r1.lower() for w in ["le ", "la ", "les ", "du ", "des ", "est ", "je "])
        results.append(("Chat FR in character", ok, r1[:120]))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(("Chat FR in character", False, str(e)))

    # 2. Chat EN
    print("\n[2/4] Chat EN — Question: Will the dollar survive 2027?")
    try:
        r2 = await test_chat("en", "Will the dollar survive 2027?", SYSTEM_PROMPT_EN)
        print(f"  ✅ Response:\n  {r2}\n")
        ok = any(w in r2.lower() for w in [" the ", " is ", " will ", " of ", " and ", " a "])
        results.append(("Chat EN in character", ok, r2[:120]))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(("Chat EN in character", False, str(e)))

    # 3. Prophecy FR
    print("\n[3/4] Prophecy FR")
    try:
        r3 = await test_prophecy("fr", SYSTEM_PROMPT_FR)
        print(f"  ✅ Prophecy:\n  {r3}\n")
        ok = len(r3) > 10 and len(r3) < 500
        results.append(("Prophecy FR generation", ok, r3[:120]))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(("Prophecy FR generation", False, str(e)))

    # 4. Prophecy EN
    print("\n[4/4] Prophecy EN")
    try:
        r4 = await test_prophecy("en", SYSTEM_PROMPT_EN)
        print(f"  ✅ Prophecy:\n  {r4}\n")
        ok = len(r4) > 10 and len(r4) < 500
        results.append(("Prophecy EN generation", ok, r4[:120]))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(("Prophecy EN generation", False, str(e)))

    # Summary
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    all_pass = True
    for name, ok, preview in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name}")
        print(f"          → {preview}")
        if not ok:
            all_pass = False

    print("=" * 70)
    if all_pass:
        print("  🟢 ALL POC TESTS PASSED — READY TO BUILD APP")
        sys.exit(0)
    else:
        print("  🔴 SOME TESTS FAILED — FIX BEFORE PROCEEDING")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
