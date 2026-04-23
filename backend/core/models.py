"""Pydantic models used across routers.

Keeping them in a single module makes the schema inspectable, avoids
circular imports between routers, and lets OpenAPI stay consistent.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------
# Chat / prophecy
# ---------------------------------------------------------------------
class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=1000)
    lang: Literal["fr", "en"] = "fr"


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    lang: str


class ProphecyResponse(BaseModel):
    prophecy: str
    lang: str
    generated_at: str


# ---------------------------------------------------------------------
# Whitelist / stats
# ---------------------------------------------------------------------
class WhitelistRequest(BaseModel):
    email: EmailStr
    lang: Optional[str] = "fr"


class WhitelistResponse(BaseModel):
    id: str
    email: str
    position: int
    created_at: str
    email_sent: bool = False


class StatsResponse(BaseModel):
    whitelist_count: int
    prophecies_served: int
    chat_messages: int
    launch_timestamp: str


# ---------------------------------------------------------------------
# Admin auth
# ---------------------------------------------------------------------
class AdminLoginRequest(BaseModel):
    password: str
    totp_code: Optional[str] = None
    backup_code: Optional[str] = None


class AdminLoginResponse(BaseModel):
    token: str
    expires_at: str
    jti: str


# ---------------------------------------------------------------------
# 2FA
# ---------------------------------------------------------------------
class TwoFASetupResponse(BaseModel):
    secret: str
    otpauth_uri: str
    qr_png_base64: str
    backup_codes: List[str]


class TwoFAStatusResponse(BaseModel):
    enabled: bool
    setup_pending: bool
    backup_codes_remaining: int
    enabled_at: Optional[str] = None


class TwoFAVerifyRequest(BaseModel):
    code: str


class TwoFADisableRequest(BaseModel):
    password: str
    code: str


# ---------------------------------------------------------------------
# Whitelist admin views
# ---------------------------------------------------------------------
class WhitelistItem(BaseModel):
    id: str
    email: str
    lang: str
    position: int
    created_at: str
    email_sent: bool = False
    email_sent_at: Optional[str] = None
    email_status: Optional[str] = None  # sent / delivered / bounced / complained / opened


class PaginatedWhitelist(BaseModel):
    items: List[WhitelistItem]
    total: int
    limit: int
    skip: int


# ---------------------------------------------------------------------
# Chat logs
# ---------------------------------------------------------------------
class ChatLogItem(BaseModel):
    id: str
    session_id: str
    lang: str
    user_message: str
    reply: str
    created_at: str


class PaginatedChatLogs(BaseModel):
    items: List[ChatLogItem]
    total: int
    limit: int
    skip: int


# ---------------------------------------------------------------------
# Generic responses
# ---------------------------------------------------------------------
class SimpleOk(BaseModel):
    ok: bool
    message: str = ""


# ---------------------------------------------------------------------
# Evolution timeseries
# ---------------------------------------------------------------------
class EvolutionPoint(BaseModel):
    date: str
    whitelist: int
    chat: int
    whitelist_daily: int
    chat_daily: int


class EvolutionResponse(BaseModel):
    days: int
    series: List[EvolutionPoint]


# ---------------------------------------------------------------------
# Blacklist
# ---------------------------------------------------------------------
class BlacklistItem(BaseModel):
    id: str
    email: str
    blacklisted_at: str
    source_entry_id: Optional[str] = None
    reason: Optional[str] = None
    cooldown_until: Optional[str] = None


class BlacklistList(BaseModel):
    items: List[BlacklistItem]
    total: int


class BlacklistAddRequest(BaseModel):
    email: EmailStr
    reason: Optional[str] = None
    cooldown_days: Optional[int] = None  # if set, auto-unblock after N days


class BlacklistImportRequest(BaseModel):
    csv_text: Optional[str] = None
    emails: Optional[List[str]] = None
    reason: Optional[str] = "bulk import"
    cooldown_days: Optional[int] = None


class BlacklistImportResponse(BaseModel):
    imported: int
    skipped_invalid: int
    skipped_existing: int
    total_rows: int
    errors: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------
# Public enriched stats
# ---------------------------------------------------------------------
class LangDistribution(BaseModel):
    fr: int = 0
    en: int = 0


class TopSessionItem(BaseModel):
    anon_id: str  # hashed, short
    lang: str
    message_count: int
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None


class PublicStatsResponse(BaseModel):
    whitelist_count: int
    chat_messages: int
    prophecies_served: int
    launch_timestamp: str
    generated_at: str
    series_days: int
    series: List[EvolutionPoint]
    lang_distribution: Dict[str, LangDistribution]  # {whitelist:{fr,en}, chat:{fr,en}}
    top_sessions: List[TopSessionItem]
    activity_heatmap: List[List[int]]  # 7 rows (Mon..Sun) x 24 cols (hours UTC)


# ---------------------------------------------------------------------
# Email events
# ---------------------------------------------------------------------
class EmailEventItem(BaseModel):
    id: str
    type: str
    email_id: Optional[str] = None
    recipient: Optional[str] = None
    received_at: str
    summary: Optional[str] = None


class PaginatedEmailEvents(BaseModel):
    items: List[EmailEventItem]
    total: int
    limit: int
    skip: int
    type_counts: Dict[str, int]


# ---------------------------------------------------------------------
# Admin sessions & JWT rotation
# ---------------------------------------------------------------------
class AdminSessionItem(BaseModel):
    jti: str
    created_at: str
    last_seen_at: Optional[str] = None
    expires_at: Optional[str] = None
    revoked: bool = False
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    secret_version: Optional[str] = None
    is_current: bool = False


class AdminSessionList(BaseModel):
    items: List[AdminSessionItem]
    total: int


class RotateSecretResponse(BaseModel):
    ok: bool
    rotated_at: str
    revoked_sessions: int
    message: str


# ---------------------------------------------------------------------
# Admin test email
# ---------------------------------------------------------------------
class AdminTestEmailRequest(BaseModel):
    email: EmailStr
    lang: Optional[str] = "fr"


class AdminTestEmailResponse(BaseModel):
    ok: bool
    email_id: Optional[str] = None
    recipient: str
    message: str


# ---------------------------------------------------------------------
# Vault — public report-purchase
# ---------------------------------------------------------------------
class VaultCrackPublicRequest(BaseModel):
    # Client-reported purchase. Later this will be replaced by an on-chain worker.
    # We accept it for now but clamp server-side to avoid abuse.
    tokens: int = Field(..., gt=0, le=50_000)
    agent_code: Optional[str] = Field(None, max_length=24)


# ---------------------------------------------------------------------
# Operation reveal
# ---------------------------------------------------------------------
class OperationRevealResponse(BaseModel):
    unlocked: bool
    stage: str
    # Payload (present only if unlocked)
    code_name: Optional[str] = None
    panic_message_fr: Optional[str] = None
    panic_message_en: Optional[str] = None
    lore_fr: Optional[List[str]] = None
    lore_en: Optional[List[str]] = None
    gencoin_launch_at: Optional[str] = None
    gencoin_url: Optional[str] = None
    revealed_at: Optional[str] = None
