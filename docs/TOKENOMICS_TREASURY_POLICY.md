# $DEEPOTUS — Tokenomics & Treasury Policy

> **Public document. Source of truth for the MiCA-compliant transparency posture
> of PROTOCOL ΔΣ.**
> 
> Last revision: 2026-04-27 · Document version: 1.0

This document is the binding public statement of how the $DEEPOTUS supply is
distributed, vested, and managed post-launch. It is published BEFORE the
on-chain mint so every wallet, every schedule, and every disclosure protocol
is committed to in advance — not retrofitted.

It is intentionally short and verifiable. Every claim below resolves to either
(a) a Solana wallet address you can read on-chain or (b) a smart-contract
schedule you can pull from Streamflow / Squads dashboards.

---

## 1. Supply distribution (1,000,000,000 $DEEPOTUS)

| Slice                    | %    | Tokens         | On-chain owner               | Lock / Schedule                                |
|--------------------------|------|----------------|------------------------------|------------------------------------------------|
| **Treasury (project)**   | 30 % | 300,000,000    | `Wallet_TREASURY` (Squads multisig, 2-of-3) | Subject to the Treasury Take-Profit Policy in §3 |
| **Team vesting**         | 15 % | 150,000,000    | `Wallet_TEAM_VESTING` (Streamflow contract) | **3-month cliff + 12-month linear vest**       |
| **Public liquidity**     | 25 % | 250,000,000    | Pump.fun bonding curve, then PumpSwap LP burned at migration | **Burned LP** at PumpSwap migration (no team rug possible) |
| **Airdrop & Clearance**  | 10 % | 100,000,000    | `Wallet_AIRDROPS`           | Reserved for Proof-of-Intelligence holders (§4) |
| **Marketing & KOLs**     | 10 % | 100,000,000    | `Wallet_MARKETING`           | Spent on disclosed line items (§5)             |
| **Founder allocation**   | 10 % | 100,000,000    | `Wallet_FOUNDER`             | **3-month cliff + 12-month linear vest** (Streamflow), parity with team |

> Wallet addresses are published on `/transparency` of the website 24 hours
> before mint. Any difference between the on-chain reality and this table
> after T-0 invalidates the entire MiCA compliance claim of the project.

### What we do NOT do
- ❌ No "stealth founder bag" — the founder allocation is on-chain and vested
  identically to the team.
- ❌ No private "snipe" of the public bonding curve by team-controlled wallets
  at T-0. Any post-launch buying by the founder is performed with personal
  funds, from a wallet disclosed under §6, **after** mint is public.
- ❌ No coordinated wallet rotation to mask team activity. Each wallet above
  has a single, immutable purpose for the lifetime of the project.

---

## 2. Team vesting — `Wallet_TEAM_VESTING`

- **Mechanism**: [Streamflow](https://streamflow.finance) on-chain vesting contract.
- **Schedule**: 3-month cliff (no token releasable for 90 days post-mint),
  followed by 12 months linear release (1/365 per day for 365 days).
- **Beneficiaries**: each team member has their own Streamflow stream so the
  release is per-person, not pooled.
- **Read-only verification**: anyone can pull the schedule from Streamflow's
  public dashboard via the contract address published on `/transparency`.

The same schedule applies to `Wallet_FOUNDER` for parity.

---

## 3. Treasury Take-Profit Policy — `Wallet_TREASURY`

The Treasury exists to fund the post-memecoin phase of the project — building
the MiCA-licensed product the Cabinet keeps mentioning. To fund that build
without dumping the chart, we commit to the following **public schedule** :

### Release tiers

| Trigger                                             | Action                                             | Cap        |
|-----------------------------------------------------|----------------------------------------------------|-----------|
| **Phase 1** — `MC ≥ 5× initial MC` (break-even)     | Sell up to **10 %** of Treasury position           | EUR 5 k   |
| **Phase 2** — `MC ≥ 15× initial MC` (growth)        | Sell up to **20 %** of Treasury position           | EUR 25 k  |
| **Phase 3** — Post-PumpSwap migration                | Sell up to **5 % per "green candle"** (≥+15% / 1h) | EUR 250 k |

### Operational rules
1. **Multisig signature**: every Treasury sell requires 2-of-3 Squads multisig
   approval. No single signer can move funds.
2. **24-hour pre-announcement**: every sell is announced on X+Telegram
   **24 hours before** the order is signed. The community can verify the
   announced size against the on-chain transaction.
3. **Per-day cap**: never more than **5% of 24h volume** on a single sell, so
   the chart absorbs without a wick.
4. **Panic suspension**: if the Cabinet engages the Propaganda Engine's
   `panic` switch (e.g. exploit, regulatory event), all Treasury sells are
   frozen until panic is cleared.
5. **Audit log**: every Treasury action is logged to `propaganda_events`
   collection AND mirrored on-chain via the Squads transaction history. The
   two MUST match — divergence is a red flag the community is invited to
   surface.

### What the Treasury funds

- Year 1 — MiCA legal counsel, audit, license filing
- Year 1 — Engineering team to build the post-memecoin product
- Year 2 — Marketing for the licensed product launch
- Reserve — Bear-market runway

A quarterly transparency report is published on `/transparency` listing the
spend per category vs the cumulative draw from Treasury.

---

## 4. Airdrop & Clearance reserve — `Wallet_AIRDROPS`

100 M tokens (10 % of supply) are reserved exclusively for users who have
earned **Clearance Level ≥ 3** through the on-site Terminal's Proof-of-
Intelligence flow (`/api/infiltration/riddles/*`).

- **Eligibility** is captured in the `clearance_levels` collection at
  `level_3_achieved_at` time.
- A snapshot CSV (email + linked wallet + clearance level + riddles solved)
  is published on `/transparency` 7 days before each airdrop wave.
- The community has 7 days to dispute any line item before the wave is
  signed.
- No wave > 25 % of the reserve in a single transaction.

The Sleeper Cell mode (`/api/admin/infiltration/sleeper-cell`), when ENGAGED,
suspends new Level-3 grants pre-launch — by design, so the airdrop list
can't be manipulated retroactively after mint.

---

## 5. Marketing & KOLs — `Wallet_MARKETING`

100 M tokens (10 %) are budgeted for paid promotion. To prevent shadow-paid
shills posing as organic supporters:

- Every payment from `Wallet_MARKETING` is published on `/transparency` with
  the recipient's handle (X / Telegram), the SOL/USD value at sign time, and
  the deliverable expected.
- KOLs paid in $DEEPOTUS receive their tokens with a **30-day vesting**
  (Streamflow) so they have skin in the game during the campaign.
- No retroactive payments. The campaign brief precedes the transaction.

Trading-bot referral commissions (Trojan, BONKBot, etc.) are also routed to
`Wallet_MARKETING` and tracked in the same ledger.

---

## 6. Founder buy disclosure protocol

The founder explicitly will buy $DEEPOTUS at launch with **personal funds**
(separate from any project wallet) — same conditions as any retail buyer, no
private pre-allocation beyond the 10 % Founder allocation already vested.

To keep this transparent and auditable:

1. The founder publishes the **personal wallet pubkey** ahead of mint on
   `/transparency` and on the project's pinned X post.
2. Within **30 minutes** of any personal buy, the Cabinet's Propaganda
   Engine pushes a disclosure to X+Telegram of the form:

   > *"Cabinet noted: founder bought X SOL at MC $Y. Wallet: ABCD…WXYZ.
   > Tx: <signature>."*

   This goes through the standard **2FA-protected approval queue** so it's
   not silent and not faked.
3. Founder sells from the personal wallet are subject to the same
   24-hour pre-announcement rule as Treasury sells.
4. The personal wallet **never** sniped the bonding curve at T-0. Any buy
   that happened in the first block of the bonding curve is a red flag the
   community is invited to surface.

---

## 7. Anti-manipulation commitments

The following are **not** part of the project, will **not** be implemented,
and the founder commits to publicly disowning any such deployment:

- ❌ **No wash trading** to maintain Pump.fun "Live Feed" position.
- ❌ **No coordinated buy walls** by team-controlled wallets to defend a
  price floor.
- ❌ **No T-0 sniper bots** funded by team or founder.
- ❌ **No private OTC "team allocation" buys** at favorable prices outside
  the public tokenomics above.
- ❌ **No spoofing** (placing then cancelling orders) on PumpSwap / Jupiter.

Any community member who spots evidence of the above is invited to file a
report on `/transparency#whistleblow`. Verified reports trigger an immediate
Propaganda Engine `panic` and a public statement within 24 hours.

---

## 8. Cabinet "Brain Connect" — read-only on-chain Lore

The site's Whale Watcher (Sprint 15.2) reads on-chain swap activity via
Helius webhooks and feeds the Propaganda Engine with prophecy triggers
when a public wallet (NOT a project wallet) buys ≥ 5 SOL.

**This is OBSERVATION, not TRADING.** The Cabinet narrates what the public
chain shows. It never writes a transaction. It never holds a private key.

The classification tiers are public:

| Tier | SOL range  | Public message tone                                      |
|------|------------|----------------------------------------------------------|
| T1   | 5–15 SOL   | "Cabinet noted a Class-3 acquisition on the chain."      |
| T2   | 15–50 SOL  | "Clearance Level 2 detected. The Vault tracks the wallet." |
| T3   | > 50 SOL   | "Cabinet has been notified. The wallet has been logged." |

The Cabinet does not name the buyer. Only the truncated wallet
(`ABCD…WXYZ`) and the SOL amount are surfaced on the public Lore feed.

---

## 9. How to verify everything in this document

- **Wallets**: published with full pubkeys at `/transparency`. Paste in
  Solscan / Solana Explorer.
- **Vesting**: Streamflow contract IDs published at `/transparency`.
  Read-only via Streamflow's public viewer.
- **Multisig**: Squads vault address published at `/transparency`.
  Members and threshold visible on Squads.so.
- **Treasury history**: every move pre-announced on the project X account
  AND visible on the multisig's transaction history.
- **Disclosure log**: every founder buy/sell, every marketing payment,
  every airdrop wave is mirrored in the `propaganda_events` audit feed
  (admin) AND on the public `/transparency` page.

---

## 10. Versioning of this document

Material changes (any change to %, schedule, wallet, or commitment above)
require:

1. A 7-day public comment window (announced on X+Telegram).
2. A version bump (this section, top of document).
3. The diff posted on `/transparency#policy-history`.

Cosmetic changes (typo, link fix) are committed directly with the diff
visible in the GitHub repo.

---

> *"Propre et auditable pour le public, exécuté avec discipline pour le
> futur du projet."* — PROTOCOL ΔΣ
