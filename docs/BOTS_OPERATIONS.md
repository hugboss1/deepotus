# Bots d'Infiltration & de Propagande — Guide d'Exploitation

Ce document explique comment les deux systèmes de bots de PROTOCOL ΔΣ
fonctionnent, quand ils se déclenchent, et comment les piloter au quotidien
depuis l'admin dashboard.

> TL;DR — il y a **deux bots indépendants** avec des objectifs opposés :
> - **Propagande** (sortant) pousse des messages vers **X + Telegram** quand
>   un événement marché intéressant arrive.
> - **Infiltration** (entrant) observe la communauté — riddles résolues,
>   mentions KOL, niveaux de clearance — pour qualifier les vrais adeptes.

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Bot de Propagande](#bot-de-propagande)
   - [Anatomie d'un trigger](#anatomie-dun-trigger)
   - [Cycle de vie d'un message](#cycle-de-vie-dun-message)
   - [Les 11 triggers seedés](#les-11-triggers-seedés)
   - [Kill switches & sauvegardes](#kill-switches--sauvegardes)
   - [Checklist avant de passer LIVE](#checklist-avant-de-passer-live)
3. [Bot d'Infiltration](#bot-dinfiltration)
   - [Les 3 niveaux de clearance](#les-3-niveaux-de-clearance)
   - [Les 5 énigmes du Terminal](#les-5-énigmes-du-terminal)
   - [KOL Mention Listener](#kol-mention-listener)
   - [Whitelist & airdrop gating](#whitelist--airdrop-gating)
4. [Comment les deux bots communiquent](#comment-les-deux-bots-communiquent)
5. [Endpoints utiles (cheat sheet)](#endpoints-utiles-cheat-sheet)

---

## Vue d'ensemble

```
              PROTOCOL ΔΣ — les deux bots en 1 schéma

┌─────────────────────────────────────────────────────────────────┐
│                       BOT DE PROPAGANDE                         │
│                    (sortant : vous → foule)                     │
│                                                                 │
│  [Market event]  ──►  [Trigger detect]  ──►  [Template pick]    │
│  whale_buy                                    (FR / EN)          │
│  mc_milestone                                                   │
│  kol_mention                ▼                                   │
│  jeet_dip          [LLM tone rewrite*]                          │
│                      (Sprint 13.2)                              │
│                            ▼                                    │
│                    [Dispatch Queue]                             │
│                    policy: auto | approval                      │
│                            ▼                                    │
│                  [Dispatch Worker tick 30s]                     │
│                  gates: panic / enabled / dry_run / rate        │
│                            ▼                                    │
│                ┌───────────┴────────────┐                       │
│                ▼                        ▼                       │
│          Telegram API               X API v2                    │
│          sendMessage                POST /2/tweets              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      BOT D'INFILTRATION                         │
│                     (entrant : foule → vous)                    │
│                                                                 │
│   [User visite /]           [User clique Terminal]              │
│       │                           │                             │
│       ▼                           ▼                             │
│  [Email capture]       [Riddle 1 — Grand Architecte]            │
│  Clearance L1          [Riddle 2 — Œil Invisible]               │
│                        [Riddle 3 — Contrat Social]              │
│  [User share X]        [Riddle 4 — Vérité de l'Agent]           │
│  Clearance L2          [Riddle 5 — Ouverture du Coffre]         │
│                            ↓                                    │
│                        Clearance L3 = AGENT                     │
│                                                                 │
│   [KOL mentions $DEEPOTUS]                                      │
│         │                                                       │
│         ▼                                                       │
│   [kol_listener polls X API]    ──►  re-déclenche Propagande    │
│   (trigger kol_mention)              via /fire                  │
│                                                                 │
│   Sortie : registre d'agents niveau 3 + wallet Solana linké     │
│            → export CSV pour airdrop                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Bot de Propagande

### Anatomie d'un trigger

Un trigger = une règle **(détecteur + métadonnées)** qui transforme un événement
marché (ou une action admin) en message publié.

Chaque trigger est défini en Python (`backend/core/triggers.py`) et a une
config persistée en MongoDB (`propaganda_triggers` collection) que l'admin peut
modifier à chaud.

**Schéma d'un trigger** :

| Champ | Rôle |
|---|---|
| `key` | ID unique (ex: `whale_buy`, `mc_milestone`) |
| `enabled` | Activé/désactivé depuis l'UI |
| `policy` | `auto` = auto-dispatch / `approval` = approbation humaine avant publication |
| `cooldown_minutes` | Anti-spam : temps minimum entre deux fires du même trigger |
| `metadata` | Paramètres custom (ex: `threshold_usd` pour whale_buy) |
| `last_fired_at` | Dernière fois que le trigger a été validé |
| `fire_count` | Compteur total de fires |

### Cycle de vie d'un message

```
1. TRIGGER FIRE
   ┌─────────────────┐
   │ event detected  │  ex: whale_buy avec 5k$ sur le pool
   └────────┬────────┘
            ▼
2. GATES (early exits)
   ┌─────────────────┐
   │ panic? disabled?│  si panic_on → audit "fire_skip_panic", stop
   │ cooldown active?│  si cooldown → audit "fire_skip_cooldown", stop
   │ sleeper cell on?│  en pre-launch, bloque les triggers marché
   └────────┬────────┘
            ▼
3. TEMPLATE PICK
   ┌─────────────────┐
   │ pick template   │  FR ou EN selon settings.default_locale
   │ vault_link_every│  tous les N messages, impose la mention du Cabinet Vault
   └────────┬────────┘
            ▼
4. RENDER + OPTIONAL LLM REWRITE
   ┌─────────────────┐
   │ {placeholders}  │  {buy_link}, {whale_amount}, {mc}, ...
   │ tone_engine?    │  si LLM activé, claude/gpt réécrit dans le ton cynique
   └────────┬────────┘
            ▼
5. ENQUEUE (propaganda_queue)
   ┌─────────────────┐
   │ policy == auto? │  → status=approved, scheduled_for = now + delay (10-30s)
   │ policy==approval│  → status=pending_review, attend admin PATCH /approve
   └────────┬────────┘
            ▼
6. DISPATCH WORKER TICK (30s cadence)
   ┌─────────────────┐
   │ gates suite     │  panic? dispatch_enabled? rate limits? dry_run?
   │ claim item      │  find_one_and_update (status: approved → dispatching)
   │ call dispatchers│  telegram.send() + x.send()
   └────────┬────────┘
            ▼
7. RESULT
   ┌─────────────────┐
   │ all_ok    → sent│   store platform_message_id (tweet ID, TG msg ID)
   │ transient → retry│  Sprint 13.3.x : 60s → 120s → 240s × 3, puis failed
   │ permanent → failed│ admin re-approuve manuellement
   └─────────────────┘
```

### Les 11 triggers seedés

| `key` | Quand se déclenche | Policy par défaut | Cooldown |
|---|---|---|---|
| `whale_buy` | BUY on-chain ≥ seuil USD (metadata `threshold_usd`) | `auto` | 10 min |
| `jeet_dip` | Prix drop > 20% sur 2 min | `approval` | 15 min |
| `mc_milestone` | MC franchit 10k/100k/1M/10M | `auto` | 60 min |
| `bonk_reached` | Milestone Bonk spécifique (post-ATL rebound) | `approval` | 60 min |
| `stealth_launch` | Flag manuel post-mint | `approval` | N/A (one-shot) |
| `raid_call` | Manuel admin — raid Telegram sur un target | `approval` | 30 min |
| `kol_mention` | KOL tweet mentionne $DEEPOTUS (via kol_listener) | `approval` | 5 min |
| `sentiment_shift` | Analyse X sentiment swing > 30% | `approval` | 60 min |
| `fed_meeting` | Scheduled: FOMC press release | `approval` | N/A (scheduled) |
| `manifest_line` | Manuel — diffuse une ligne manifeste | `approval` | 120 min |
| `burn_event` | Supply burn détecté on-chain | `auto` | 120 min |

**Chaque trigger a ses propres placeholders** dans les templates (ex:
`{whale_amount}`, `{mc}`, `{kol_handle}`) — voir `backend/core/templates_repo.py`
pour la liste complète.

### Kill switches & sauvegardes

Trois interrupteurs en cascade, dans cet ordre :

1. **PANIC** (propaganda_settings.panic)
   - Bouton rouge dans l'admin UI Propaganda.
   - Quand ON : tue toute la queue en attente (status → killed), bloque
     toute nouvelle fire, bloque le dispatch worker.
   - Usage : "J'ai vu un message qui ne devrait pas partir, je coupe tout".

2. **Dispatch Enabled** (propaganda_settings.dispatch_enabled)
   - Par défaut `false` — le worker lit la queue mais ne touche à rien.
   - Usage : staging / debug du scheduling sans envoyer réellement.

3. **Dispatch Dry-run** (propaganda_settings.dispatch_dry_run)
   - Par défaut `true` — les dispatchers court-circuitent l'appel HTTP
     et loggent `would_send ...`.
   - Usage : premier passage LIVE une fois les creds vaulted — on veut voir
     le pipeline tourner sans poster pour de vrai.

En plus :

- **Rate limits** (`rate_limits.per_hour`, `per_day`, `per_trigger_minutes`)
  — le worker refuse de dispatch au-delà.
- **Sleeper cell** (`core/sleeper_cell.py`) — en pre-launch, bloque les
  triggers qui leakeraient un lien d'achat avant le mint.
- **Audit log** (`propaganda_events`) — chaque fire, skip, approve, reject,
  kill, panic est loggé avec jti + IP + timestamp.

### Checklist avant de passer LIVE

```
[ ] 2FA activée sur /admin/security
[ ] Cabinet Vault unlocked
[ ] Telegram bot token + chat_id stockés (vérifier via /dispatch/preflight)
[ ] X API: 4 secrets OAuth 1.0a stockés (X_API_KEY / X_API_SECRET /
    X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET)
[ ] Tier X confirmé : Basic ($100/mo) minimum pour POST /2/tweets
[ ] X app permissions "Read and write" (pas juste Read)
[ ] Test Manual Fire d'un trigger approval-mode → approuver → observer la queue
[ ] dispatch_enabled=true, dispatch_dry_run=true → POST /dispatch/tick-now →
    observer que la bannière UI passe à DRY-RUN et que le log dit "would_send"
[ ] Vérifier audit log : pas d'erreur permanente dans les 10 derniers events
[ ] Flip dispatch_dry_run=false → re-tick-now → observer bannière LIVE
[ ] Surveiller le premier message réellement posté sur X + TG
[ ] Si KO, remettre panic=true immédiatement, debug audit log
```

---

## Bot d'Infiltration

Le bot d'infiltration ne **dispatche rien**. Son boulot : qualifier silencieusement
les utilisateurs qui visitent le site et leur attribuer un **niveau de clearance**
qui servira à la whitelist airdrop.

### Les 3 niveaux de clearance

| Niveau | Nom | Critère | Vérifié par |
|---|---|---|---|
| **L1 OBSERVER** | Observateur | Follow `@Deepotus_AI` + join Telegram | Manuel (14.1) → auto (14.2) |
| **L2 INFILTRATOR** | Infiltré | Partage une prophétie avec `#DEEPOTUS` | Manuel (14.1) → auto (14.2) |
| **L3 AGENT** | Agent | A résolu **≥ 1 énigme** sur le Terminal | **Auto** (ce qui marche aujourd'hui) |

Le niveau est **dérivé** de la présence/absence des champs `level_N_achieved_at`
sur le document `clearance_levels` (1 par email). L3 est **déverrouillé** dès
qu'au moins 1 énigme est solved.

**Transition attendue Sprint 14.2** :
- L1 auto-validé par polling X API (follow check) + Telegram bot API
  (getChatMember) — attend le tier X Elevated.
- L2 auto-validé par search X API (requête filtrée `#DEEPOTUS from:user`).
- Pour l'instant, l'admin coche L1/L2 manuellement depuis `/admin/clearance`
  (`POST /admin/clearance/set-level`).

### Les 5 énigmes du Terminal

Les énigmes sont dans `backend/core/riddles.py` (seed verbatim) :

| Slug | Titre | Mots-clés acceptés (normalisés) |
|---|---|---|
| `grand-architecte` | Le Grand Architecte | `la fed`, `fed`, `inflation`, `planche`, `central bank` |
| `oeil-invisible` | L'Œil Invisible | `algorithme`, `ia`, `ai`, `surveillance`, `intelligence artificielle` |
| `contrat-social` | Le Contrat Social | `systeme bancaire`, `capitalisme`, `economie`, `finance` |
| `verite-de-lagent` | La Vérité de l'Agent | `deepotus`, `$deepotus`, `blockchain`, `solana` |
| `ouverture-du-coffre` | L'Ouverture du Coffre | `produit`, `esclave`, `pion`, `actif` |

**Mécanisme anti-brute force** :
- Normalisation agressive (lowercase + strip accents + drop punctuation).
- Matching par **substring** → `"La Féd."` match `la fed` ✅.
- Limite douce : 6 tentatives fausses / heure / email / énigme.
- TTL 24h sur `riddle_attempts` (collection Mongo auto-purgée).
- Une énigme résolue → permanente (`$addToSet` sur `riddles_solved`).

**Admin UI** : `/admin/infiltration` permet d'éditer questions / mots-clés /
activer-désactiver une énigme sans redéployer.

### KOL Mention Listener

Fichier : `backend/core/kol_listener.py`

**Ce qui marche aujourd'hui** :
- Liste de 10 KOL handles seedés (`aeyakovenko`, `Ansem`, `SolBigBrain`, …).
- Endpoint admin `POST /admin/kol-listener/simulate` pour tester le pipeline
  en injectant une fausse mention.
- Queue FSM : `detected → analyzing → propaganda_proposed → notified | skipped`.
- Worker tick toutes les 5 min qui drain la queue → appelle
  `propaganda_engine.fire("kol_mention", ...)` → un template kol_reply est
  rendu + envoyé en approval.

**Ce qui attend le Sprint 17** :
- Polling X API réel (nécessite tier Basic ≥ $100/mo).
- Pseudo-code prêt en `_fetch_kol_recent_tweets` — il ne reste qu'à le wire.

### Whitelist & airdrop gating

```
Email captured (L0)
    ▼
L1 (follow + TG join)
    ▼
L2 (share prophecy)
    ▼
L3 (solve ≥ 1 riddle)  ← auto-award déjà opérationnel
    ▼
link_wallet() → wallet Solana validé (base58, 32-44 char)
    ▼
Eligible airdrop → export CSV depuis /admin/clearance/export-csv
```

**Export airdrop** (`snapshot_level3()`) :
- Liste les L3 avec wallet → priorité 1 (eligible).
- Liste les L3 sans wallet → flag `_snapshot_status: "no_wallet"` → à relancer
  par email pour qu'ils ajoutent leur wallet.

L'admin peut **force-promote** un utilisateur via
`POST /admin/clearance/set-level` (avec `notes` pour audit).

---

## Comment les deux bots communiquent

Un seul lien direct : **`kol_listener` appelle `propaganda_engine.fire()`**
quand une mention est drainée.

```python
# backend/core/kol_listener.py
res = await propaganda_engine.fire(
    trigger_key="kol_mention",
    manual=True,                 # by-passe le détecteur (c'est bien un fire)
    payload_override={
        "kol_handle": "aeyakovenko",
        "kol_tweet_excerpt": "...",
        "kol_tweet_url": "...",
    },
)
```

Le trigger `kol_mention` est en `policy=approval` par défaut — l'admin valide
avant publication. Ça évite qu'un compte usurpé ou un tweet ironique déclenche
un post public immédiat.

**Sinon, les deux bots partagent** :
- Le Cabinet Vault (mêmes secrets `x_twitter` pour le polling KOL ET pour le
  dispatch X).
- L'audit log `propaganda_events` (tout fire/skip, y compris de source KOL).
- La base MongoDB (collections séparées : `propaganda_*` vs `clearance_levels`
  / `riddles` / `kol_mentions`).

---

## Endpoints utiles (cheat sheet)

### Propagande (admin)

| Méthode | Endpoint | Rôle |
|---|---|---|
| `GET` | `/api/admin/propaganda/settings` | État global (panic, dispatch_enabled, rate_limits, …) |
| `PATCH` | `/api/admin/propaganda/settings` | Modifier settings |
| `GET` | `/api/admin/propaganda/triggers` | Liste des 11 triggers + config |
| `PATCH` | `/api/admin/propaganda/triggers/:key` | Modifier un trigger |
| `POST` | `/api/admin/propaganda/fire` | Manual Fire (admin déclenche un trigger) |
| `GET` | `/api/admin/propaganda/queue?status=pending_review` | Liste items en attente |
| `POST` | `/api/admin/propaganda/queue/:id/approve` | Approuver un item |
| `POST` | `/api/admin/propaganda/queue/:id/reject` | Rejeter un item |
| `GET` | `/api/admin/propaganda/dispatch/status` | Stats du worker |
| `GET` | `/api/admin/propaganda/dispatch/preflight` | Vérifier creds X/TG |
| `POST` | `/api/admin/propaganda/dispatch/tick-now` | Force une tick |
| `POST` | `/api/admin/propaganda/dispatch/toggle` | Bascule enabled / dry_run |
| `GET` | `/api/admin/propaganda/activity?limit=100` | Audit log |

### Infiltration (admin)

| Méthode | Endpoint | Rôle |
|---|---|---|
| `GET` | `/api/admin/infiltration/riddles` | Liste éditoriale (avec keywords) |
| `PATCH` | `/api/admin/infiltration/riddles/:id` | Modifier une énigme |
| `POST` | `/api/admin/infiltration/riddles/:id/toggle` | On/off |
| `GET` | `/api/admin/clearance?level=3` | Liste des agents par niveau |
| `GET` | `/api/admin/clearance/stats` | Compteurs dashboard |
| `POST` | `/api/admin/clearance/set-level` | Force-promote un email |
| `POST` | `/api/admin/clearance/set-wallet` | Lier un wallet Solana à un email |
| `GET` | `/api/admin/clearance/export-csv` | Export airdrop (L3 avec wallet) |
| `GET` | `/api/admin/kol-listener/config` | Handles + match_terms |
| `PATCH` | `/api/admin/kol-listener/config` | Update config (handles, enabled, …) |
| `POST` | `/api/admin/kol-listener/simulate` | Injecter une fausse mention |
| `GET` | `/api/admin/kol-listener/mentions?status=detected` | Queue |

### Public / user

| Méthode | Endpoint | Rôle |
|---|---|---|
| `GET` | `/api/infiltration/riddles?lang=fr` | Liste publique (sans keywords) |
| `POST` | `/api/infiltration/riddles/:slug/attempt` | Soumettre une réponse |
| `GET` | `/api/infiltration/clearance/:email` | État d'un utilisateur |
| `POST` | `/api/infiltration/clearance/:email/link-wallet` | Lier son wallet |

---

## Questions fréquentes

> **Q : Un trigger en `policy=auto` peut-il spammer ?**
>
> Non — il passe par la queue comme les autres, et la queue respecte les
> rate_limits (per_hour / per_day / per_trigger_minutes). L'intérêt de `auto`
> est juste d'éviter le clic admin : si tout est dans les clous, l'item est
> dispatch tout seul.

> **Q : Si je factory-reset le vault, que se passe-t-il pour les bots ?**
>
> Les secrets X/TG/Helius sont perdus → les dispatchers tomberont en
> `FAILED permanent: no_credentials` à la prochaine tick. Il faut **re-saisir
> les secrets avant** de re-unlock le vault.

> **Q : Puis-je désactiver un bot sans désactiver l'autre ?**
>
> Oui. Propagande = `panic=true` OU `dispatch_enabled=false`. Infiltration =
> chaque énigme peut être `enabled=false` individuellement, ou `kol_listener.config.enabled=false`
> pour couper le polling KOL sans toucher aux riddles.

> **Q : Comment retirer un agent de la whitelist ?**
>
> `POST /admin/clearance/set-level` avec `level=0` — le niveau repart à 0,
> la ligne reste pour audit. Mettez le `notes` pour dire pourquoi (ex:
> "wallet drainé, suspicion sybil").
