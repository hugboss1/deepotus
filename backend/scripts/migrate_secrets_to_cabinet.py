"""One-shot migration: copy secrets from env / legacy Fernet vault into
the Cabinet Vault.

USAGE
-----
    cd /app/backend
    python -m scripts.migrate_secrets_to_cabinet \
        --token "<admin JWT>" --mnemonic "word1 word2 ... word24"

Or interactively:
    python -m scripts.migrate_secrets_to_cabinet --interactive

What it does
------------
1. Unlocks the Cabinet Vault using the supplied 24-word mnemonic
   (the master key is held in the script's process memory only).
2. Mirrors every populated env var listed in ``MIGRATION_PLAN`` into
   the matching vault category/key.
3. Reads the legacy Fernet-encrypted custom LLM keys from
   ``bot_config.custom_llm_keys`` and stores them under
   ``llm_custom/{OPENAI|ANTHROPIC|GEMINI}_API_KEY``.
4. Prints a summary table.

Safety
------
- The script never writes to env vars and never deletes the legacy
  Fernet entries — running the migration twice is idempotent and you
  can roll back simply by clearing the vault entries.
- Secrets are NEVER printed in full — only ``mask_for_display()``.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys
from typing import Iterable, List, Optional, Tuple

# Allow running from /app/backend with `python -m scripts.migrate_...`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import cabinet_vault as vault  # noqa: E402
from core.config import db  # noqa: E402
from core.secrets_vault import (  # noqa: E402
    decrypt as fernet_decrypt,
    mask_for_display,
)

# ---------------------------------------------------------------------
# Migration plan
# ---------------------------------------------------------------------
# (vault_category, vault_key, env_var)  — env_var defaults to vault_key
MIGRATION_PLAN: List[Tuple[str, str, Optional[str]]] = [
    ("llm_emergent", "EMERGENT_LLM_KEY", None),
    ("llm_emergent", "EMERGENT_IMAGE_LLM_KEY", None),
    ("email_resend", "RESEND_API_KEY", None),
    ("email_resend", "SENDER_EMAIL", None),
    ("email_resend", "RESEND_WEBHOOK_SECRET", None),
    ("solana_helius", "HELIUS_API_KEY", None),
    ("solana_helius", "HELIUS_WEBHOOK_AUTH", None),
    ("telegram", "TELEGRAM_BOT_TOKEN", None),
    ("telegram", "TELEGRAM_CHAT_ID", None),
    ("x_twitter", "X_BEARER_TOKEN", "TWITTER_BEARER_TOKEN"),
    ("x_twitter", "X_API_KEY", None),
    ("x_twitter", "X_API_SECRET", None),
    ("site", "PUBLIC_BASE_URL", None),
    ("site", "DEEPOTUS_LAUNCH_ISO", None),
]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _row(category: str, key: str, status: str, mask: str = "—") -> str:
    return f"  • {category}/{key:<24} {status:<14} {mask}"


async def _migrate_env_secret(
    *, category: str, key: str, env_var: str, jti: str,
) -> str:
    """Copy ``os.environ[env_var]`` into vault[category, key]. Returns
    a one-line status row."""
    raw = (os.environ.get(env_var) or "").strip()
    if not raw:
        return _row(category, key, "skip:empty_env")
    try:
        await vault.set_secret(category, key, raw, jti=jti)
        return _row(category, key, "imported", mask_for_display(raw))
    except Exception as exc:  # noqa: BLE001
        return _row(category, key, f"FAILED:{type(exc).__name__}")


async def _migrate_legacy_llm_keys(jti: str) -> Iterable[str]:
    """Pull legacy Fernet-encrypted custom LLM keys off the bot_config
    singleton and store the plaintext under ``llm_custom/*``."""
    doc = await db.bot_config.find_one({"_id": "bot_config_singleton"})
    bag_root = ((doc or {}).get("custom_llm_keys") or {})
    out: List[str] = []
    for provider, key_name in (
        ("openai", "OPENAI_API_KEY"),
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("gemini", "GEMINI_API_KEY"),
    ):
        bag = bag_root.get(provider) or {}
        if not bag.get("ciphertext"):
            out.append(_row("llm_custom", key_name, "skip:no_legacy"))
            continue
        try:
            plaintext = fernet_decrypt(bag["ciphertext"])
        except Exception as exc:  # noqa: BLE001
            out.append(_row("llm_custom", key_name,
                            f"FAILED:decrypt:{type(exc).__name__}"))
            continue
        try:
            await vault.set_secret("llm_custom", key_name, plaintext, jti=jti)
            out.append(_row("llm_custom", key_name, "imported",
                            mask_for_display(plaintext)))
        except Exception as exc:  # noqa: BLE001
            out.append(_row("llm_custom", key_name,
                            f"FAILED:write:{type(exc).__name__}"))
    return out


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
async def run(mnemonic: str, jti: str) -> None:
    print("[1/3] Unlocking Cabinet Vault…", flush=True)
    await vault.unlock(mnemonic, jti=jti)
    print("       ✓ unlocked\n")

    print("[2/3] Migrating env-var secrets:")
    for category, key, env_var in MIGRATION_PLAN:
        env_name = env_var or key
        line = await _migrate_env_secret(
            category=category, key=key, env_var=env_name, jti=jti,
        )
        print(line)

    print("\n[3/3] Migrating legacy custom LLM keys (Fernet → AES-GCM):")
    for line in await _migrate_legacy_llm_keys(jti):
        print(line)

    status = await vault.get_status()
    print(
        f"\nDone. secret_count={status['secret_count']} "
        f"locked={status['locked']} "
        f"expires_in={status['expires_in_seconds']}s"
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Migrate env / Fernet secrets into the Cabinet Vault."
    )
    p.add_argument(
        "--mnemonic",
        help="24-word BIP39 mnemonic. If omitted, you'll be prompted.",
    )
    p.add_argument(
        "--jti",
        default="migration-script",
        help="Audit jti tag (default: migration-script)",
    )
    p.add_argument(
        "--interactive",
        action="store_true",
        help="Always prompt for the mnemonic, ignoring --mnemonic.",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    mnemonic = args.mnemonic
    if args.interactive or not mnemonic:
        mnemonic = getpass.getpass("Paste 24-word mnemonic (hidden): ").strip()
    if len(mnemonic.split()) != 24:
        print("ERROR: mnemonic must be exactly 24 words.", file=sys.stderr)
        sys.exit(2)
    asyncio.run(run(mnemonic, args.jti))


if __name__ == "__main__":
    main()
