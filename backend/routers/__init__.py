"""FastAPI routers package.

All business endpoints live here, organized by domain:
    - public      : unauthenticated user-facing (chat, prophecy, whitelist, stats)
    - public_stats: enriched read-only analytics for the landing page
    - webhooks    : Resend webhook receiver (svix-signed)
    - admin       : admin dashboard (JWT + 2FA protected)
    - vault       : PROTOCOL ΔΣ state + admin crack endpoints
    - access_card : Level 2 clearance / classified-vault gate
    - operation   : /operation/reveal (twist endpoint)
"""
