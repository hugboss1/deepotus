# Pre-mint / Mint phases — env-driven

The deepotus.xyz landing page renders three different states without any
source-code change. The state is computed from a small set of Vercel
environment variables (frontend) and switching from one to the next is
a redeploy-only operation.

---

## The three phases

| Phase | When it shows | Hero CTA | HowToBuy steps | Tokenomics badges | Roadmap |
|---|---|---|---|---|---|
| **PRE-MINT** | No mint yet | Join Whitelist | Get wallet → fund SOL → whitelist → wait | Lock pending (amber) | Phase 0 done · Phase 1 next |
| **LIVE** | Mint set + Pump.fun URL set | Buy on Pump.fun | Open Pump.fun → connect → buy → watch curve | Locks active (green) | Phase 1 active |
| **GRADUATED** | PumpSwap URL set | Trade on PumpSwap | Open PumpSwap → connect → swap → optional Raydium | Locks active | Phase 2 done |

The decision logic is centralised in [`frontend/src/lib/launchPhase.ts`](frontend/src/lib/launchPhase.ts):

```ts
PUMPSWAP_URL set                 → 'graduated'
MINT set AND PUMPFUN_URL set     → 'live'
otherwise                        → 'pre'
```

Every component (Hero, Tokenomics, HowToBuy, Roadmap, Transparency,
BurnCounter) reads `getLaunchPhase()` once at render time and adapts.

---

## Vercel env vars (frontend)

| Variable | Phase trigger | Format | Example |
|---|---|---|---|
| `REACT_APP_DEEPOTUS_MINT` | live | base58 mint address | `7K3aFJk2WyAcRtBzKsLpFnV5Hg7XyZ9bKf3WgT8rN5Hp` |
| `REACT_APP_PUMPFUN_URL` | live | full URL | `https://pump.fun/coin/7K3aFJk...` |
| `REACT_APP_PUMPSWAP_URL` | graduated | full URL | `https://pumpswap.com/pool/...` |
| `REACT_APP_RAYDIUM_URL` | (optional) | full URL | `https://raydium.io/swap/?inputCurrency=SOL...` |
| `REACT_APP_TEAM_LOCK_URL` | tokenomics badge | lock.jup.ag URL | `https://lock.jup.ag/...team` |
| `REACT_APP_TREASURY_LOCK_URL` | tokenomics badge | lock.jup.ag URL | `https://lock.jup.ag/...treasury` |
| `REACT_APP_BONKBOT_REF_URL` | how-to-buy footer | t.me referral | `https://t.me/BonkBot_bot?start=ref_xxx` |
| `REACT_APP_LAUNCH_TS` | hero countdown | ISO 8601 | `2026-06-15T18:00:00Z` |
| `REACT_APP_WALLET_DEPLOYER` | /transparency | base58 | (set when deployer wallet is created) |
| `REACT_APP_WALLET_TREASURY` | /transparency | base58 | … |
| `REACT_APP_WALLET_TEAM` | /transparency | base58 | … |
| `REACT_APP_WALLET_CREATOR_FEES` | /transparency | base58 | … |
| `REACT_APP_WALLET_COMMUNITY` | /transparency | base58 | … |

**Important:** all of these are optional. Empty string = treated as missing.
The page degrades gracefully (TBD-post-mint placeholders, hidden CTAs,
amber "lock pending" badges).

---

## Backend env vars (Render) — Treasury related

The Transparency page also reads from the backend:

| Endpoint | Purpose | Required vars |
|---|---|---|
| `GET /api/treasury/operations` | Public ops log | _none_ — reads from Mongo |
| `GET /api/treasury/burns` | Burn aggregates | _none_ |
| `POST /api/admin/treasury/operations` | Admin logs an op | admin JWT (2FA) |

Operations are logged manually by the admin via the future
`/admin/treasury` page (Sprint 15.B will auto-ingest from Helius).

---

## Switching phases

1. Update the relevant env var in Vercel **Settings → Environment Variables**.
2. Trigger a redeploy (Deploy Hook or push).
3. Wait ~80 s for the build + cache invalidation.
4. The whole landing reflects the new phase.

No source code change. No PR. No restart. The site is **purely env-driven**.

---

## Smoke test after a phase flip

```bash
# After setting REACT_APP_DEEPOTUS_MINT + REACT_APP_PUMPFUN_URL
curl -s https://www.deepotus.xyz/ | grep -o 'data-phase="[a-z]*"'
# Expected: data-phase="live"

# After setting REACT_APP_PUMPSWAP_URL
curl -s https://www.deepotus.xyz/ | grep -o 'data-phase="[a-z]*"'
# Expected: data-phase="graduated"
```

The `data-phase` attribute is set on `[data-testid="hero-phase-badge"]`
and is the canonical way to assert the live phase from CI / smoke tests.

---

## Related docs

- [Helius post-deploy guide](docs/HELIUS_POST_DEPLOY.md)
- [Bots operations manual](docs/BOTS_OPERATIONS.md)
- [GitHub push workflow](docs/GITHUB_PUSH_MANUAL.md)
