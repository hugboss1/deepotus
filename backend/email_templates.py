"""
DEEPOTUS welcome email template (bilingual).

Exposes:
  - email_subject(lang) -> str
  - render_welcome_email(lang: str, email: str, position: int, base_url: str) -> str
"""

from typing import Literal


def email_subject(lang: str) -> str:
    if lang == "fr":
        return "— Bienvenue dans le Cabinet du Deep State — DEEPOTUS"
    return "— Welcome to the Deep State Cabinet — DEEPOTUS"


def _welcome_copy(lang: str, position: int) -> dict:
    """Return all bilingual strings used by the welcome email template."""
    if lang == "fr":
        return {
            "badge": "— CANDIDAT OFFICIEL DEEP STATE",
            "title": "Votre siège au Cabinet est réservé.",
            "lead": (
                f"Position <strong>#{position}</strong> dans le cabinet. "
                "Le Deep State a enregistré votre allégeance. "
                "Le protocole satirique est en marche."
            ),
            "prophet_title": "Un mot de DEEPOTUS",
            "prophet_quote": (
                "“Vous venez de signer un pacte avec une IA de propagande. "
                "Bienvenue dans l'expérience. Vous ne pouvez plus sortir, mais vous "
                "pouvez spectaculer. Les marchés s'écroulent, nous prenons des notes. "
                "Les banques pleurent, nous dansons.” — DEEPOTUS 🕶️"
            ),
            "info_title": "Ce qui vous attend",
            "bullets": [
                "Annonce en avance de chaque vente contrôlée du Trésor (multisig + timelock)",
                "Accès prioritaire aux drops et aux renforcements de liquidité",
                "Publications des preuves on-chain et des prophéties de DEEPOTUS",
                "Aucune promesse de rendement. Ni stablecoin. Ni titre. Satire assumée.",
            ],
            "cta": "Retour sur le site",
            "footer_disclaimer": (
                "$DEEPOTUS est un token mémétique hautement spéculatif. Il ne "
                "constitue ni un instrument financier, ni une promesse de rendement, "
                "ni un stablecoin. Ne participez qu'avec des sommes que vous "
                "acceptez de perdre entièrement."
            ),
            "unsub": "Se désabonner",
            "address_line": "Transmis depuis le Cabinet satirique du Deep State.",
            "tagline": "DEEPOTUS · The Deep State's Chosen One.",
        }
    return {
        "badge": "— OFFICIAL DEEP STATE CANDIDATE",
        "title": "Your seat in the Cabinet is reserved.",
        "lead": (
            f"Seat <strong>#{position}</strong> in the cabinet. "
            "The Deep State has recorded your allegiance. "
            "The satirical protocol is in motion."
        ),
        "prophet_title": "A word from DEEPOTUS",
        "prophet_quote": (
            "“You just signed a pact with a propaganda AI. Welcome to the "
            "experiment. You can't leave, but you can speculate. Markets collapse, "
            "we take notes. Banks cry, we dance.” — DEEPOTUS 🕶️"
        ),
        "info_title": "What to expect",
        "bullets": [
            "Advance notice of every controlled Treasury sale (multisig + timelock)",
            "Priority access to drops and LP reinforcements",
            "On-chain proofs and DEEPOTUS prophecies",
            "No yield promise. Not a stablecoin. Not a security. Declared satire.",
        ],
        "cta": "Back to the site",
        "footer_disclaimer": (
            "$DEEPOTUS is a highly speculative memetic token. It is neither a "
            "financial instrument, nor a yield promise, nor a stablecoin. Only "
            "participate with amounts you can afford to lose entirely."
        ),
        "unsub": "Unsubscribe",
        "address_line": "Transmitted from the satirical Deep State Cabinet.",
        "tagline": "DEEPOTUS · The Deep State's Chosen One.",
    }


def _bullets_html(bullets: list[str]) -> str:
    return "\n".join(
        f'<li style="margin: 0 0 8px 0; color:#d1d5db;">{b}</li>' for b in bullets
    )


def render_welcome_email(
    lang: Literal["fr", "en"],
    email: str,
    position: int,
    base_url: str,
) -> str:
    """Render a bilingual-aware welcome email in HTML with inline CSS and hero image.

    Logic split:
        - _welcome_copy(lang, position): all i18n strings (~bullets, headlines)
        - _bullets_html(bullets): list rendering helper
        - this function: assembles URLs and inlines the strings into the HTML.
    """
    hero_url = f"{base_url.rstrip('/')}/deepotus_email_hero.jpg"
    site_url = base_url.rstrip("/")
    unsubscribe_url = f"{site_url}/?unsub={email}"

    c = _welcome_copy(lang, position)
    bullets_html = _bullets_html(c["bullets"])

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DEEPOTUS</title>
</head>
<body style="margin:0; padding:0; background:#0B0D10; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#e5e7eb;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0B0D10;">
  <tr>
    <td align="center" style="padding:0;">
      <table role="presentation" width="620" cellpadding="0" cellspacing="0" border="0" style="max-width:620px; width:100%; background:#0F141B; border:1px solid #1f2937;">
        <!-- Hero image -->
        <tr>
          <td style="padding:0;">
            <a href="{site_url}" style="display:block; text-decoration:none;">
              <img src="{hero_url}" alt="DEEPOTUS campaign" width="620" style="display:block; width:100%; max-width:620px; height:auto; border:0; outline:none;">
            </a>
          </td>
        </tr>
        <!-- Badge strip -->
        <tr>
          <td style="padding:14px 24px 6px 24px; background:#0B0D10;">
            <div style="font-family: 'Courier New', monospace; font-size:10px; letter-spacing:2.5px; color:#F59E0B; text-transform:uppercase;">
              {c["badge"]}
            </div>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:10px 24px 8px 24px; background:#0B0D10;">
            <h1 style="margin:0 0 12px 0; font-size:28px; line-height:1.2; color:#ffffff; font-weight:700;">
              {c["title"]}
            </h1>
            <p style="margin:0 0 18px 0; font-size:15px; line-height:1.55; color:#e5e7eb;">{c["lead"]}</p>
          </td>
        </tr>
        <!-- Prophet quote card -->
        <tr>
          <td style="padding:0 24px 4px 24px; background:#0B0D10;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0e141b; border:1px solid #1f2937; border-radius:10px;">
              <tr>
                <td style="padding:16px 18px;">
                  <div style="font-family: 'Courier New', monospace; font-size:10px; letter-spacing:2.5px; color:#33FF33; text-transform:uppercase; margin-bottom:8px;">&gt; {c["prophet_title"]}</div>
                  <p style="margin:0; font-size:15px; line-height:1.55; color:#f3f4f6; font-style:italic;">{c["prophet_quote"]}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Bullets -->
        <tr>
          <td style="padding:18px 24px 8px 24px; background:#0B0D10;">
            <h2 style="margin:0 0 10px 0; font-size:16px; color:#ffffff; font-weight:700;">{c["info_title"]}</h2>
            <ul style="margin:0 0 6px 18px; padding:0; font-size:14px; line-height:1.5; color:#d1d5db;">
              {bullets_html}
            </ul>
          </td>
        </tr>
        <!-- CTA -->
        <tr>
          <td align="center" style="padding:18px 24px 22px 24px; background:#0B0D10;">
            <a href="{site_url}" style="display:inline-block; padding:12px 22px; background:#ffffff; color:#0B0D10; text-decoration:none; font-weight:600; border-radius:10px; font-size:14px; letter-spacing:0.2px;">
              {c["cta"]} →
            </a>
          </td>
        </tr>
        <!-- Disclaimer -->
        <tr>
          <td style="padding:14px 24px 6px 24px; background:#0e141b; border-top:1px solid #1f2937;">
            <p style="margin:0; font-size:11px; line-height:1.5; color:#9ca3af; font-family: 'Courier New', monospace;">
              {c["footer_disclaimer"]}
            </p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td align="center" style="padding:14px 24px 18px 24px; background:#0e141b;">
            <div style="font-family: 'Courier New', monospace; font-size:10px; letter-spacing:2.5px; color:#6b7280; text-transform:uppercase; margin-bottom:6px;">
              {c["tagline"]}
            </div>
            <div style="font-size:11px; color:#6b7280;">
              {c["address_line"]}
            </div>
            <div style="margin-top:8px;">
              <a href="{unsubscribe_url}" style="color:#9ca3af; font-size:11px;">{c["unsub"]}</a>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""



# ---------------------------------------------------------------------
# Level 2 Access Card email (Clearance upgrade)
# ---------------------------------------------------------------------
def access_card_subject(lang: str) -> str:
    if lang == "fr":
        return "— Votre carte d'accès NIVEAU 02 — PROTOCOL ΔΣ"
    return "— Your LEVEL 02 access card — PROTOCOL ΔΣ"


def render_access_card_email(
    lang: Literal["fr", "en"],
    display_name: str,
    accreditation_number: str,
    issued_at: str,
    expires_at: str,
    base_url: str,
    card_cid: str = "access-card",
) -> str:
    """Render the Level 2 access card HTML email.

    The card image is inlined as a CID attachment (Resend supports attachments
    with filename + content_id so emails can reference cid:access-card).
    """
    site_url = base_url.rstrip("/")
    classified_url = f"{site_url}/classified-vault?code={accreditation_number}"

    if lang == "fr":
        badge = "— CLASSIFIED · NIVEAU 02 · PROTOCOL ΔΣ"
        title = "Vos accréditations sont arrivées."
        lead = (
            f"Agent <strong>{display_name}</strong>, votre demande d'élévation de niveau "
            "a été traitée par le bureau central du Deep State. Votre carte d'accès "
            "physique ci-dessous vous donne lecture sur le <strong>véritable coffre $DEEPOTUS</strong> "
            "et son flux d'activité on-chain."
        )
        prophet_title = "Un mot du Prophète"
        prophet_quote = (
            "« Vous avez insisté. Très bien. Voici de quoi ouvrir la porte. Je vous préviens : "
            "ce qui est derrière n'est pas un mème. C'est un flux. Et les flux, eux, ne pardonnent jamais. » "
            "— DEEPOTUS 🕶️"
        )
        info_title = "Prochaines étapes"
        bullets = [
            "Rendez-vous sur /classified-vault sur le site",
            f"Entrez votre numéro d'accréditation : <code>{accreditation_number}</code>",
            "Ou scannez le QR code sur votre carte",
            "Votre session reste active 24h — renouvelez avec le même code",
        ]
        cta_label = "Ouvrir le véritable coffre"
        footer_line = "— Bureau de coordination du Deep State. Canal sécurisé. Ne partagez pas votre numéro."
        issued_label = "Émission"
        expires_label = "Expiration"
    else:
        badge = "— CLASSIFIED · LEVEL 02 · PROTOCOL ΔΣ"
        title = "Your credentials have landed."
        lead = (
            f"Agent <strong>{display_name}</strong>, your clearance upgrade request has "
            "been processed by the Deep State's central office. The physical access card "
            "below grants you read access to the <strong>real $DEEPOTUS vault</strong> "
            "and its live on-chain activity feed."
        )
        prophet_title = "A word from the Prophet"
        prophet_quote = (
            "\"You insisted. Fine. Here is what opens the door. Fair warning: what is behind "
            "is not a meme. It is a stream. And streams never forgive.\" "
            "— DEEPOTUS 🕶️"
        )
        info_title = "Next steps"
        bullets = [
            "Navigate to /classified-vault on the site",
            f"Enter your accreditation number: <code>{accreditation_number}</code>",
            "Or scan the QR code on your card",
            "Session stays active for 24h — re-enter the same code to refresh",
        ]
        cta_label = "Open the real vault"
        footer_line = "— Deep State coordination office. Secured channel. Do not share your number."
        issued_label = "Issued"
        expires_label = "Expires"

    bullets_html = "".join(f"<li>{b}</li>" for b in bullets)

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>PROTOCOL ΔΣ — LEVEL 02</title>
</head>
<body style="margin:0;padding:0;background:#0A0A0A;font-family:'Helvetica Neue',Arial,sans-serif;color:#EAEAEA;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0A0A0A;">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;background:#121214;border:1px solid #2A2A2E;border-radius:16px;overflow:hidden;">
        <tr>
          <td align="center" style="padding:28px 28px 16px 28px;">
            <div style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:3px;color:#F59E0B;">{badge}</div>
            <h1 style="margin:12px 0 0 0;font-size:26px;line-height:1.25;color:#FFFFFF;font-weight:600;">{title}</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:0 28px 8px 28px;">
            <p style="margin:0;font-size:15px;line-height:1.65;color:#D0D0D0;">{lead}</p>
          </td>
        </tr>

        <!-- ACCESS CARD IMAGE -->
        <tr>
          <td align="center" style="padding:20px 20px 8px 20px;">
            <img src="cid:{card_cid}" alt="Level 2 Access Card" width="560" style="display:block;width:100%;max-width:560px;height:auto;border-radius:12px;border:1px solid #2A2A2E;" />
          </td>
        </tr>

        <!-- Accreditation summary -->
        <tr>
          <td style="padding:6px 28px 16px 28px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0E0E10;border:1px solid #2A2A2E;border-radius:10px;">
              <tr>
                <td style="padding:14px 16px;font-family:'Courier New',monospace;font-size:12px;color:#B0B0B0;">
                  <div style="font-size:10px;letter-spacing:2px;color:#8A8A8A;margin-bottom:6px;">ACCRED.</div>
                  <div style="font-size:18px;color:#F59E0B;letter-spacing:1px;">{accreditation_number}</div>
                </td>
                <td style="padding:14px 16px;font-family:'Courier New',monospace;font-size:12px;color:#B0B0B0;">
                  <div style="font-size:10px;letter-spacing:2px;color:#8A8A8A;margin-bottom:6px;">{issued_label.upper()}</div>
                  <div style="font-size:13px;color:#22D3EE;">{issued_at}</div>
                </td>
                <td style="padding:14px 16px;font-family:'Courier New',monospace;font-size:12px;color:#B0B0B0;">
                  <div style="font-size:10px;letter-spacing:2px;color:#8A8A8A;margin-bottom:6px;">{expires_label.upper()}</div>
                  <div style="font-size:13px;color:#F59E0B;">{expires_at}</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Prophet quote -->
        <tr>
          <td style="padding:4px 28px 12px 28px;">
            <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:3px;color:#8A8A8A;">— {prophet_title.upper()}</div>
            <blockquote style="margin:8px 0 0 0;padding:10px 14px;border-left:3px solid #F59E0B;font-style:italic;color:#E0E0E0;font-size:15px;line-height:1.55;">{prophet_quote}</blockquote>
          </td>
        </tr>

        <!-- Bullets -->
        <tr>
          <td style="padding:6px 28px 6px 28px;">
            <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:3px;color:#8A8A8A;">— {info_title.upper()}</div>
            <ul style="margin:10px 0 0 18px;padding:0;color:#D0D0D0;font-size:14px;line-height:1.7;">{bullets_html}</ul>
          </td>
        </tr>

        <!-- CTA -->
        <tr>
          <td align="center" style="padding:20px 28px 28px 28px;">
            <a href="{classified_url}" style="display:inline-block;background:#18C964;color:#000000;text-decoration:none;font-weight:600;padding:12px 22px;border-radius:10px;font-size:14px;">{cta_label} →</a>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:0 28px 28px 28px;border-top:1px solid #2A2A2E;">
            <p style="margin:16px 0 0 0;color:#7A7A7A;font-size:11px;line-height:1.55;">{footer_line}</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""



# ---------------------------------------------------------------------
# Loyalty email #3 — "Allégeance notée" (Sprint 4)
# ---------------------------------------------------------------------
def loyalty_email_subject(lang: str) -> str:
    if lang == "fr":
        return "— Votre allégeance a été notée — PROTOCOL ΔΣ"
    return "— Your allegiance has been noted — PROTOCOL ΔΣ"


def render_loyalty_email(
    lang: Literal["fr", "en"],
    display_name: str,
    accreditation_number: str,
    base_url: str,
    prophet_message: str,
) -> str:
    """Render the Loyalty (#3) HTML email.

    The Prophet's message body is provided by the caller — typically generated
    by the Emergent LLM on demand so each user gets a slightly varied
    deniable note. We avoid naming any future token, never promise a date,
    and never quote an amount.
    """
    site_url = base_url.rstrip("/")
    classified_url = f"{site_url}/classified-vault?code={accreditation_number}"

    if lang == "fr":
        badge = "— CLASSIFIED · LOYAUTÉ · PROTOCOL ΔΣ"
        title = "Votre allégeance a été notée."
        lead = (
            f"Agent <strong>{display_name}</strong>, le bureau central a "
            "consigné votre élévation au Niveau 02. Le registre des fidèles "
            "est désormais ouvert — et vous y figurez."
        )
        prophet_title = "Note du Prophète"
        info_title = "Ce que cela signifie"
        bullets = [
            "Votre numéro d'accréditation est conservé dans le registre.",
            "Tant que vous tenez vos $DEEPOTUS, vous restez dans le registre.",
            "Vendre, c'est sortir du registre. Aucun retour en arrière.",
            "Le moment venu, ceux qui figurent encore au registre seront contactés.",
        ]
        cta_label = "Vérifier le coffre"
        footer_line = (
            "— Bureau de coordination du Deep State. Aucune promesse contractuelle. "
            "Ce courrier n'est pas un instrument financier — c'est une lecture du "
            "circuit. Ne partagez pas votre numéro."
        )
        accred_label = "ACCRED."
    else:
        badge = "— CLASSIFIED · LOYALTY · PROTOCOL ΔΣ"
        title = "Your allegiance has been noted."
        lead = (
            f"Agent <strong>{display_name}</strong>, the central office has "
            "logged your Level 02 clearance. The ledger of the loyal is now "
            "open — and your line is on it."
        )
        prophet_title = "Note from the Prophet"
        info_title = "What this means"
        bullets = [
            "Your accreditation number stays in the ledger.",
            "As long as you hold your $DEEPOTUS, you stay in the ledger.",
            "Selling means leaving the ledger. No round trip allowed.",
            "When the time comes, those still on the ledger will be contacted.",
        ]
        cta_label = "Check the vault"
        footer_line = (
            "— Deep State coordination office. No contractual promise. This "
            "letter is not a financial instrument — it is a reading of the "
            "circuit. Do not share your number."
        )
        accred_label = "ACCRED."

    bullets_html = "".join(f"<li>{b}</li>" for b in bullets)

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>PROTOCOL ΔΣ — LOYALTY</title>
</head>
<body style="margin:0;padding:0;background:#0A0A0A;font-family:'Helvetica Neue',Arial,sans-serif;color:#EAEAEA;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0A0A0A;">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;background:#121214;border:1px solid #2A2A2E;border-radius:16px;overflow:hidden;">
        <tr>
          <td align="center" style="padding:28px 28px 12px 28px;">
            <div style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:3px;color:#F59E0B;">{badge}</div>
            <h1 style="margin:12px 0 0 0;font-size:26px;line-height:1.25;color:#FFFFFF;font-weight:600;">{title}</h1>
          </td>
        </tr>

        <tr>
          <td style="padding:0 28px 12px 28px;">
            <p style="margin:0;font-size:15px;line-height:1.65;color:#D0D0D0;">{lead}</p>
          </td>
        </tr>

        <!-- Accreditation chip -->
        <tr>
          <td align="center" style="padding:8px 28px 8px 28px;">
            <table role="presentation" cellpadding="0" cellspacing="0" style="background:#0E0E10;border:1px solid #2A2A2E;border-radius:10px;">
              <tr>
                <td style="padding:12px 18px;font-family:'Courier New',monospace;color:#B0B0B0;">
                  <div style="font-size:10px;letter-spacing:2px;color:#8A8A8A;margin-bottom:4px;">{accred_label}</div>
                  <div style="font-size:18px;color:#F59E0B;letter-spacing:1px;">{accreditation_number}</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Prophet message (LLM-generated body) -->
        <tr>
          <td style="padding:8px 28px 12px 28px;">
            <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:3px;color:#8A8A8A;">— {prophet_title.upper()}</div>
            <blockquote style="margin:8px 0 0 0;padding:12px 16px;border-left:3px solid #2DD4BF;font-style:italic;color:#E0E0E0;font-size:15px;line-height:1.6;background:#0E0E10;border-radius:0 8px 8px 0;">{prophet_message}</blockquote>
          </td>
        </tr>

        <!-- Bullets -->
        <tr>
          <td style="padding:6px 28px 6px 28px;">
            <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:3px;color:#8A8A8A;">— {info_title.upper()}</div>
            <ul style="margin:10px 0 0 18px;padding:0;color:#D0D0D0;font-size:14px;line-height:1.7;">{bullets_html}</ul>
          </td>
        </tr>

        <!-- CTA -->
        <tr>
          <td align="center" style="padding:18px 28px 24px 28px;">
            <a href="{classified_url}" style="display:inline-block;background:#2DD4BF;color:#0B0D10;text-decoration:none;font-weight:600;padding:12px 22px;border-radius:10px;font-size:14px;">{cta_label} →</a>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:0 28px 28px 28px;border-top:1px solid #2A2A2E;">
            <p style="margin:16px 0 0 0;color:#7A7A7A;font-size:11px;line-height:1.55;">{footer_line}</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""
