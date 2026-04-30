# 📚 Docs index — $DEEPOTUS

> Lisez en priorité les docs **🟢 current**. Les docs **🟡 partial** sont utiles mais partiellement dépassées par le fichier pointé dans leur header.

---

## 🚀 Déploiement

| Doc | Statut | Usage |
|---|---|---|
| [`VERCEL_DASHBOARD_SETUP.md`](./VERCEL_DASHBOARD_SETUP.md) | 🟢 current | **Frontend Vercel — setup complet dashboard.** Lire en 1er si premier déploiement ou si site affiche `undefined`. |
| [`VERCEL_REDEPLOY_QUICK.md`](./VERCEL_REDEPLOY_QUICK.md) | 🟢 current | Routine 30s pour redeploy (push git, bouton dashboard, ou CLI). |
| [`VERCEL_DEPLOYMENT.md`](./VERCEL_DEPLOYMENT.md) | 🟢 current | RCA technique AJV + plan B overrides npm + migration Vite. Pour troubleshooting approfondi. |
| [`RENDER_DEPLOYMENT.md`](./RENDER_DEPLOYMENT.md) | 🟢 current | **Backend Render — setup complet.** Incl. llm_compat Mode A/B + Sprint 13.3 env vars + rotation credentials. |
| [`SPRINT_13_3_DISPATCHERS.md`](./SPRINT_13_3_DISPATCHERS.md) | 🟢 current | Propaganda Dispatchers (Telegram/X). Architecture, routes admin, checklist passage en LIVE. |
| [`../DEPLOY.md`](../DEPLOY.md) | 🟢 current | Checklist ultra-condensée de déploiement end-to-end. |
| [`../DEPLOYMENT_AND_PHASES_GUIDE.md`](../DEPLOYMENT_AND_PHASES_GUIDE.md) | 🟡 partial | Master guide pré-mint du 25/04. Sections 1-7 + 13-18 valables; sections 8-12 remplacées par les docs ci-dessus. |

## 🔐 Sécurité & opérations

| Doc | Statut | Usage |
|---|---|---|
| [`2FA_SETUP_GUIDE.md`](./2FA_SETUP_GUIDE.md) | 🟢 current | Activation 2FA admin (TOTP + backup codes). |
| [`TOKENOMICS_TREASURY_POLICY.md`](./TOKENOMICS_TREASURY_POLICY.md) | 🟢 current | Politique treasury + team lock + transparency. |
| [`../SETUP_DOMAIN_WEBHOOK.md`](../SETUP_DOMAIN_WEBHOOK.md) | 🟢 current | DNS + webhook Helius/Resend. |

## 📋 Produit & planning

| Doc | Statut | Usage |
|---|---|---|
| [`../README.md`](../README.md) | 🟢 current | Overview projet, tech stack, commandes dev. |
| [`../plan.md`](../plan.md) | 🟢 current | Plan séquentiel des phases (17.A→17.G, Sprint 13.3, etc.) — auto-mis à jour par les agents. |
| [`../design_guidelines.md`](../design_guidelines.md) | 🟢 current | UI/UX guidelines Matrix/Deep State. |
| [`../TODO_POST_LAUNCH.md`](../TODO_POST_LAUNCH.md) | 🟢 current | Todos à faire post-mint (KOL listener polling, retry counter dispatchers, etc.). |
| [`../TODO_TYPESCRIPT.md`](../TODO_TYPESCRIPT.md) | 🟡 partial | Plan migration TS (coverage actuelle 15.4%). En attente post-launch. |

---

## 🎯 Quick links par besoin

**"Mon site Vercel affiche `undefined` dans les URLs API"**
→ [`VERCEL_DASHBOARD_SETUP.md#étape-1️⃣`](./VERCEL_DASHBOARD_SETUP.md) — section Environment Variables, puis redeploy sans cache.

**"Mon site Vercel build échoue avec AJV error"**
→ [`VERCEL_DASHBOARD_SETUP.md#étape-2️⃣-et-3️⃣`](./VERCEL_DASHBOARD_SETUP.md) — Install Command + Node 20.

**"Mon backend Render échoue sur `No matching distribution found for emergentintegrations`"**
→ [`RENDER_DEPLOYMENT.md#stratégie-llm-sur-render`](./RENDER_DEPLOYMENT.md) — choisir Mode B (clés natives) ou Mode A (PIP_EXTRA_INDEX_URL).

**"Je veux activer les posts automatiques Telegram/X"**
→ [`SPRINT_13_3_DISPATCHERS.md#checklist-pour-passer-en-live`](./SPRINT_13_3_DISPATCHERS.md) — vault credentials + toggle dry_run=false.

**"Je veux redéployer le frontend après un fix"**
→ [`VERCEL_REDEPLOY_QUICK.md`](./VERCEL_REDEPLOY_QUICK.md) — git push = auto redeploy, ou dashboard pour forcer sans cache.
