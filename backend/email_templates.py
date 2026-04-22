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


def render_welcome_email(
    lang: Literal["fr", "en"],
    email: str,
    position: int,
    base_url: str,
) -> str:
    """Render a bilingual-aware welcome email in HTML with inline CSS and hero image."""

    hero_url = f"{base_url.rstrip('/')}/deepotus_email_hero.jpg"
    site_url = base_url.rstrip("/")
    unsubscribe_url = f"{site_url}/?unsub={email}"

    if lang == "fr":
        badge = "— CANDIDAT OFFICIEL DEEP STATE"
        title = "Votre siège au Cabinet est réservé."
        lead = (
            f"Position <strong>#{position}</strong> dans le cabinet. "
            "Le Deep State a enregistré votre allégeance. Le protocole satirique est en marche."
        )
        prophet_title = "Un mot de DEEPOTUS"
        prophet_quote = (
            "“Vous venez de signer un pacte avec une IA de propagande. "
            "Bienvenue dans l'expérience. Vous ne pouvez plus sortir, mais vous pouvez spectaculer. "
            "Les marchés s'écroulent, nous prenons des notes. Les banques pleurent, nous dansons.” "
            "— DEEPOTUS 🕶️"
        )
        info_title = "Ce qui vous attend"
        bullets = [
            "Annonce en avance de chaque vente contrôlée du Trésor (multisig + timelock)",
            "Accès prioritaire aux drops et aux renforcements de liquidité",
            "Publications des preuves on-chain et des prophéties de DEEPOTUS",
            "Aucune promesse de rendement. Ni stablecoin. Ni titre. Satire assumée.",
        ]
        cta = "Retour sur le site"
        footer_disclaimer = (
            "$DEEPOTUS est un token mémétique hautement spéculatif. Il ne constitue ni "
            "un instrument financier, ni une promesse de rendement, ni un stablecoin. "
            "Ne participez qu'avec des sommes que vous acceptez de perdre entièrement."
        )
        unsub = "Se désabonner"
        address_line = "Transmis depuis le Cabinet satirique du Deep State."
        tagline = "DEEPOTUS · The Deep State's Chosen One."
    else:
        badge = "— OFFICIAL DEEP STATE CANDIDATE"
        title = "Your seat in the Cabinet is reserved."
        lead = (
            f"Seat <strong>#{position}</strong> in the cabinet. "
            "The Deep State has recorded your allegiance. The satirical protocol is in motion."
        )
        prophet_title = "A word from DEEPOTUS"
        prophet_quote = (
            "“You just signed a pact with a propaganda AI. Welcome to the experiment. "
            "You can't leave, but you can speculate. Markets collapse, we take notes. "
            "Banks cry, we dance.” — DEEPOTUS 🕶️"
        )
        info_title = "What to expect"
        bullets = [
            "Advance notice of every controlled Treasury sale (multisig + timelock)",
            "Priority access to drops and LP reinforcements",
            "On-chain proofs and DEEPOTUS prophecies",
            "No yield promise. Not a stablecoin. Not a security. Declared satire.",
        ]
        cta = "Back to the site"
        footer_disclaimer = (
            "$DEEPOTUS is a highly speculative memetic token. It is neither a financial "
            "instrument, nor a yield promise, nor a stablecoin. Only participate with "
            "amounts you can afford to lose entirely."
        )
        unsub = "Unsubscribe"
        address_line = "Transmitted from the satirical Deep State Cabinet."
        tagline = "DEEPOTUS · The Deep State's Chosen One."

    bullets_html = "\n".join(
        f'<li style="margin: 0 0 8px 0; color:#1f2937;">{b}</li>' for b in bullets
    )

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
              {badge}
            </div>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:10px 24px 8px 24px; background:#0B0D10;">
            <h1 style="margin:0 0 12px 0; font-size:28px; line-height:1.2; color:#ffffff; font-weight:700;">
              {title}
            </h1>
            <p style="margin:0 0 18px 0; font-size:15px; line-height:1.55; color:#e5e7eb;">{lead}</p>
          </td>
        </tr>
        <!-- Prophet quote card -->
        <tr>
          <td style="padding:0 24px 4px 24px; background:#0B0D10;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0e141b; border:1px solid #1f2937; border-radius:10px;">
              <tr>
                <td style="padding:16px 18px;">
                  <div style="font-family: 'Courier New', monospace; font-size:10px; letter-spacing:2.5px; color:#33FF33; text-transform:uppercase; margin-bottom:8px;">&gt; {prophet_title}</div>
                  <p style="margin:0; font-size:15px; line-height:1.55; color:#f3f4f6; font-style:italic;">{prophet_quote}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Bullets -->
        <tr>
          <td style="padding:18px 24px 8px 24px; background:#0B0D10;">
            <h2 style="margin:0 0 10px 0; font-size:16px; color:#ffffff; font-weight:700;">{info_title}</h2>
            <ul style="margin:0 0 6px 18px; padding:0; font-size:14px; line-height:1.5; color:#d1d5db;">
              {bullets_html.replace('color:#1f2937', 'color:#d1d5db')}
            </ul>
          </td>
        </tr>
        <!-- CTA -->
        <tr>
          <td align="center" style="padding:18px 24px 22px 24px; background:#0B0D10;">
            <a href="{site_url}" style="display:inline-block; padding:12px 22px; background:#ffffff; color:#0B0D10; text-decoration:none; font-weight:600; border-radius:10px; font-size:14px; letter-spacing:0.2px;">
              {cta} →
            </a>
          </td>
        </tr>
        <!-- Disclaimer -->
        <tr>
          <td style="padding:14px 24px 6px 24px; background:#0e141b; border-top:1px solid #1f2937;">
            <p style="margin:0; font-size:11px; line-height:1.5; color:#9ca3af; font-family: 'Courier New', monospace;">
              {footer_disclaimer}
            </p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td align="center" style="padding:14px 24px 18px 24px; background:#0e141b;">
            <div style="font-family: 'Courier New', monospace; font-size:10px; letter-spacing:2.5px; color:#6b7280; text-transform:uppercase; margin-bottom:6px;">
              {tagline}
            </div>
            <div style="font-size:11px; color:#6b7280;">
              {address_line}
            </div>
            <div style="margin-top:8px;">
              <a href="{unsubscribe_url}" style="color:#9ca3af; font-size:11px;">{unsub}</a>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""
