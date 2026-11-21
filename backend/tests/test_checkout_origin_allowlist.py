"""Regression test — VideoGen leaves the shop, checkout redirects pinned.

Two guards on ``POST /api/payments/checkout/session``:

  * ``product_id`` only accepts ``boardgame``. VideoGen is sold on its
    own site; its catalogue entry stays so older orders still resolve.
  * ``origin_url`` (used to build Stripe's success / cancel URLs) must be
    an allow-listed bare origin. Otherwise anyone could create a real
    checkout session that sends the buyer to a third-party site after
    paying (open redirect).

Pure checks: no Mongo, no Stripe call.
"""

from __future__ import annotations

import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "deepotus_test")

from core import stripe_checkout  # noqa: E402
from routers.payments import CreateSessionPayload  # noqa: E402

ALLOWED = ["https://www.deepotus.xyz", "https://deepotus.xyz"]


# ---------------------------------------------------------------------
# product_id
# ---------------------------------------------------------------------
def test_boardgame_still_accepted() -> None:
    p = CreateSessionPayload(product_id="boardgame", origin_url="https://deepotus.xyz")
    assert p.product_id == "boardgame"


@pytest.mark.parametrize("product_id", ["videogen", "VIDEOGEN", "boardgame|videogen", ""])
def test_videogen_and_others_rejected(product_id: str) -> None:
    with pytest.raises(ValidationError):
        CreateSessionPayload(product_id=product_id, origin_url="https://deepotus.xyz")


def test_videogen_catalogue_entry_kept_for_old_orders() -> None:
    assert "videogen" in stripe_checkout.PRODUCT_CATALOG


# ---------------------------------------------------------------------
# origin_url allow-list
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "origin_url, expected",
    [
        ("https://www.deepotus.xyz", "https://www.deepotus.xyz"),
        ("https://deepotus.xyz", "https://deepotus.xyz"),
        ("https://deepotus.xyz/", "https://deepotus.xyz"),
        ("HTTPS://WWW.DEEPOTUS.XYZ", "https://www.deepotus.xyz"),
    ],
)
def test_allowed_origins(origin_url: str, expected: str) -> None:
    assert stripe_checkout.checked_origin(origin_url, ALLOWED) == expected


@pytest.mark.parametrize(
    "origin_url",
    [
        "https://evil.example",
        "https://deepotus.xyz.evil.example",
        "https://evil.example/https://deepotus.xyz",
        "https://deepotus.xyz@evil.example",
        "https://deepotus.xyz/paiement",
        "https://deepotus.xyz?next=https://evil.example",
        "https://deepotus.xyz#x",
        "http://deepotus.xyz",
        "javascript:alert(1)",
        "//deepotus.xyz",
        "",
    ],
)
def test_rejected_origins(origin_url: str) -> None:
    with pytest.raises(ValueError):
        stripe_checkout.checked_origin(origin_url, ALLOWED)


def test_default_allow_list_has_production_hosts() -> None:
    assert stripe_checkout.checked_origin("https://www.deepotus.xyz") == "https://www.deepotus.xyz"
    assert stripe_checkout.checked_origin("https://deepotus.xyz") == "https://deepotus.xyz"
    with pytest.raises(ValueError):
        stripe_checkout.checked_origin("https://evil.example")
