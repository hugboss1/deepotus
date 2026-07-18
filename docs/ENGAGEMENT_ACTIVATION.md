# Engagement organique X — runbook d'activation

Deux modules, livrés désactivés (`enabled=false`) :

| Module | Ce qu'il fait | Ce qu'il ne fait JAMAIS |
|---|---|---|
| **Mention Responder** | Répond automatiquement aux comptes qui mentionnent @Deepotus_AI (surface conforme aux règles X : ils nous ont engagés d'abord). ~4 polls/jour, max 5 réponses/tick, cooldown 24 h par compte. | Chercher des inconnus par mots-clés. |
| **Keyword Digest** | 2×/jour, cherche les tweets « i need a ticker », « no pump & dump », « chill »… et envoie un digest Telegram PRIVÉ avec, pour chaque tweet : lien, réponse prête à coller, et lien « Répondre en 1 clic » (composeur X pré-rempli). | Poster sur X. L'envoi reste un geste humain. |

## Prérequis (une fois)

1. **Credentials X** déjà en place (`x_twitter/X_API_KEY|X_API_SECRET|X_ACCESS_TOKEN|X_ACCESS_TOKEN_SECRET|X_BEARER_TOKEN` dans le Cabinet Vault, ou en env sur Render).
2. **`telegram/TELEGRAM_ADMIN_CHAT_ID`** : le chat privé du fondateur avec le bot Prophète.
   - Envoyer n'importe quel message au bot depuis ton compte Telegram perso.
   - Ouvrir `https://api.telegram.org/bot<TOKEN>/getUpdates` → relever `message.chat.id`.
   - Le stocker dans le Vault (`telegram/TELEGRAM_ADMIN_CHAT_ID`) ou en env Render.
   - Volontairement **sans fallback** vers `TELEGRAM_CHAT_ID` (canal public) : si absent, le digest se met en `no_admin_chat_id` et n'envoie rien.

## Recette (dry-run, aucun tweet posté)

```bash
# 1. Mention Responder — 1er appel = pose la baseline (aucune réponse)
POST /api/admin/engagement/mentions/poll-now?dry_run=true
# 2. Mentionner @Deepotus_AI depuis un compte de test, attendre ~1 min
# 3. Re-poller : la réponse apparaît en outcome=dry_run dans l'audit
POST /api/admin/engagement/mentions/poll-now?dry_run=true
GET  /api/admin/engagement/mentions/replies
# 4. Digest — envoie le digest réel sur TON Telegram (rien sur X)
POST /api/admin/engagement/digest/run-now
```

## Mise en service

```bash
PATCH /api/admin/engagement/mentions/config   {"enabled": true}
PATCH /api/admin/engagement/digest/config     {"enabled": true}
```

Le scheduler (jobs `mention_responder` + `keyword_digest`, tick 30 min,
auto-gatés) prend le relais. Le mode réel des réponses aux mentions
suit le flag global `propaganda_settings.dispatch_dry_run`.

## Réglages utiles

- `PATCH /mentions/config` : `poll_interval_hours` (déf. 6), `max_replies_per_tick` (déf. 5, plafond dur 10), `per_handle_cooldown_hours` (déf. 24), `reply_templates` (rotation anti-duplicate, `{handle}` injecté).
- `PATCH /digest/config` : `hours_utc` (déf. `[7,16]` ≈ 9h/18h Paris), `rules` (`label` + `query` syntaxe X + `template`), `min_author_followers` (déf. 25), `max_hits_per_rule` (déf. 5).

## Budget crédits X (Pay-Per-Use, par jour, défauts)

- Mentions : 4 lectures + ≤ 20 écritures (en pratique bien moins).
- Digest : ~6 lectures de recherche, 0 écriture.
