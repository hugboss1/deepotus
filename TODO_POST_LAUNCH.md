# 🛠 $DEEPOTUS — Post-Launch Refactor Backlog

> Items tirés du code review du 24/04/2026, **délibérément différés** au post-launch parce que :
> - Ils ne créent **aucun bug user-visible** aujourd'hui
> - Ils représentent **40-80h de refacto** (split, audit auth, type hints)
> - On est **à 7 jours du go-live** et chaque touche au code = risque de régression sur le fil sécurité-coffre
>
> Une fois live et validé en prod, on peut prendre 1-2 sprints calmes pour exécuter ce backlog.

---

## 🔴 Priority 1 — Sécurité (post-launch sprint 1)

### 1.1 Migration `localStorage` → `httpOnly cookies` pour l'auth admin

**Surface concernée** : 7 fichiers
- `src/pages/Admin.jsx` (lines 178, 229)
- `src/pages/AdminVault.jsx`
- `src/pages/AdminEmails.jsx`
- `src/pages/AdminBots.jsx`
- `src/pages/ClassifiedVault.jsx` (lines 44, 133) — session vault visiteur
- `src/components/landing/vault/TerminalPopup.jsx` (line 149) — session vault visiteur

**Pourquoi le faire post-launch** :
- Surface XSS quasi-nulle aujourd'hui (zero contenu user-generated)
- Protection 2FA déjà en place sur l'admin
- Le refactor demande :
  - Backend : émettre `Set-Cookie: token=...; HttpOnly; Secure; SameSite=None; Domain=.deepotus.xyz`
  - CSRF middleware avec double-submit pattern
  - Frontend : tous les `axios`/`fetch` à passer en `withCredentials: true`
  - Re-test E2E complet du flux 2FA + révocation sessions
- Risque casser l'auth en prod = très mauvais juste avant launch

**Plan post-launch** :
1. Créer une branche feature `auth/httponly-cookies`
2. Implémenter côté FastAPI (`Response.set_cookie` + `request.cookies.get`)
3. Ajouter middleware CSRF (`itsdangerous.URLSafeTimedSerializer`)
4. Refactor frontend axios baseConfig avec `withCredentials`
5. Tester sur preview Emergent puis Render staging
6. Cutover prod
**Estimation** : 2-3 jours dev + 1 jour test

---

### 1.2 Splits de composants > 500 lignes

| Fichier | Lignes | Découpe proposée |
|---|---|---|
| `Admin.jsx` | 1075 | `<AdminLogin />` · `<WhitelistTable />` · `<BlacklistTable />` · `<EmailEventsList />` · `<AdminSidebar />` · custom hooks `useAdminAuth`, `useWhitelist` |
| `AdminBots.jsx` | 1063 | `<BotConfigPanel />` · `<BotPreviewPanel />` · `<BotJobsTab />` · `<BotLogsTab />` · `<KillSwitchHero />` |
| `AdminVault.jsx` | 850 | `<VaultStateCard />` · `<HeliusIndexerCard />` · `<DialOverridePanel />` · `<VaultPresetsPicker />` |
| `ClassifiedVault.jsx` | 599 | `<VaultDigicode />` · `<VaultUnlocked />` · custom hook `useVaultSession` |
| `TerminalPopup.jsx` | 537 | `<TerminalDeniedPhase />` · `<TerminalRequestForm />` · `<TerminalVerifyForm />` · `<TerminalSuccess />` |
| `PublicStats.jsx` | 428 | `<StatsKpis />` · `<StatsCharts />` · `<StatsHeatmap />` |
| `Hero.jsx` | 382 | `<HeroVariants />` · `<HeroMintBlock />` · `<HeroCountdownIndicator />` |
| `Tokenomics.jsx` | 317 | `<TokenomicsPie />` · `<TokenomicsLockBadges />` · `<TokenomicsBuyCTA />` |

**Pourquoi le faire post-launch** : zéro impact runtime, mais ~1 journée de refacto par fichier, total ~1 semaine.

**Plan** : faire ça tranquillement entre J+7 et J+30.

---

## 🟡 Priority 2 — Lisibilité backend (post-launch sprint 2)

### 2.1 Refacto de fonctions complexes

| Fichier | Fonction | Lignes | Découpe |
|---|---|---|---|
| `access_card.py` | `render_card()` | 161 | extraire `_draw_header_block`, `_draw_agent_block`, `_draw_qr_block`, `_draw_dates_block` |
| `core/prophet_studio.py` | `generate_post()` | 137 | séparer `_build_user_prompt`, `_call_llm`, `_parse_json_output` |
| `core/email_service.py` | `send_welcome_email()` | 61 | extraire `_render_welcome_template` |
| `email_templates.py` | `render_welcome_email()` | 170 | découper en `_render_header`, `_render_lore`, `_render_cta_block` |
| `dexscreener.py` | `dex_poll_once()` | 67 | séparer `_fetch_dex_data` et `_process_swaps` |
| `core/security.py` | `verify_admin_jwt`, `require_admin` | 11 nesting | flatten avec early returns |

**Pourquoi le faire post-launch** : zéro impact comportemental, juste readability. Le code marche et est testé.

---

### 2.2 Type hints (couverture actuelle ~60%)

Files à 0% :
- `generate_logos_round4.py` (script one-shot, peu critique)
- `generate_prophet_guide.py` (script one-shot)
- `routers/operation.py`
- `server.py` (entrypoint, surtout du wiring)

**Plan** : ajouter au fil des modifications futures (rule "tout fichier touché = type-hinted on the way out").

---

## 🟢 Décisions tranchées (NE PAS RE-CHECKER)

Ces points ont été audités et **rejetés** car le reviewer s'est trompé :

### ❌ Python `is` vs `==` — FALSE POSITIVE

Le reviewer a flagué 27 lignes dans `vault.py`, `routers/vault.py`, `routers/bots.py`, `routers/public_stats.py`, `core/bot_scheduler.py`. **Toutes ces lignes utilisent correctement `is None` / `is not None`** — c'est l'idiome Python recommandé par PEP 8. Vérification faite avec `ruff F632` : **0 erreur sur tout le backend**.

Ne pas appliquer.

### ❌ Hook deps manquants — FALSE POSITIVE

Le reviewer a flagué les `useEffect` de `Operation.jsx`, `ClassifiedVault.jsx`, `PublicStats.jsx`, `AdminBots.jsx`, `Admin.jsx`, `use-toast.js`. **Toutes ces lignes ont des `// eslint-disable-next-line react-hooks/exhaustive-deps` délibérés** parce que :
- Les fonctions citées (`bootstrap`, `loadAll`, `fetchData`) sont définies dans le composant et changent à chaque render → les ajouter en dep = **boucle infinie**
- Les setters (`setNow`, `setState`) sont garantis stables par React
- `API`, `SESSION_KEY` sont des constantes module-level

L'amélioration "correcte" serait de wrapper toutes ces fonctions en `useCallback`, mais ça représente ~50-100 lignes de boilerplate pour un gain proche de zéro. Reporter à post-launch.

### ❌ Index as key — FALSE POSITIVE pour les listes structurelles

Le reviewer a flagué `Operation.jsx:112`, `HowToBuy.jsx:307`, `AdminVault.jsx:388`, `VaultSection.jsx:177`, `FAQ.jsx`, `BrutalTruth.jsx`, `Manifesto.jsx`, `Mission.jsx`, `ActivityHeatmap.jsx`. **Tous ces cas sont des listes ordonnées structurelles** :
- 6 cadrans Δ1-Δ6 du Vault → position = identité
- Heatmap 7×24 → jour×heure = grille fixe
- FAQ / Manifesto / BrutalTruth → contenu statique de translations.js, jamais réordonné
- HowToBuy steps → ordre = séquence d'instructions

L'index EST l'identité stable dans ces cas. Aucun risque de mauvais update.

---

## ✅ Fixes appliqués pendant la review (24/04/2026)

| Fix | Fichier | Pourquoi |
|---|---|---|
| `useMemo` sur context value + `useCallback` sur toggle | `theme/ThemeProvider.jsx` | Évite re-render de TOUS les consumers de useTheme à chaque render parent |
| Extraction des chart configs en constants module-level | `pages/PublicStats.jsx` | `CHART_MARGIN`, `AXIS_TICK_STYLE`, `AXIS_LINE_STYLE` — perf recharts |

---

## 📊 Synthèse — Effort vs Risque

| Catégorie | Risque actuel | Effort fix | Quand |
|---|---|---|---|
| Splits composants | 0 (juste maintenabilité) | 5 jours | Post-launch sprint 2 |
| localStorage→cookies | Faible (pas de XSS surface) | 3-4 jours | Post-launch sprint 1 |
| Refacto fonctions complexes | 0 (code tested) | 2-3 jours | Post-launch sprint 2 |
| Type hints scripts one-shot | 0 | 1 journée | Au fil de l'eau |
| `is` vs `==` | **N/A — false positive** | 0 | — |
| Hook deps | **N/A — délibéré** | 0 | — |
| Index as key | **N/A — listes structurelles** | 0 | — |

**Total backlog réel** : ~10 jours dev répartis sur 2 sprints post-launch.

---

> Document maintenu par Neo · à mettre à jour à chaque review Code Quality
