// $DEEPOTUS i18n dictionary (FR / EN)
// All UI copy lives here. Keys mirror component structure.

export const translations = {
  fr: {
    // ---- Meta / Nav ----
    nav: {
      manifesto: "Manifeste",
      chat: "Parler au Prophète",
      tokenomics: "Tokenomics",
      mission: "Mission",
      transparency: "Transparence",
      roadmap: "Feuille de route",
      faq: "FAQ",
      join: "Rejoindre le Deep State",
      buy: "Acheter $DEEPOTUS",
    },

    // ---- Hero ----
    hero: {
      stamp: "GÉNÉRÉ PAR IA — CECI EST UNE SIMULATION",
      candidate: "CANDIDAT OFFICIEL — DEEP STATE 20XX",
      title: "VOTEZ",
      ticker: "$DEEPOTUS",
      subtitle:
        "L'élu du Deep State à la présidence du monde entier. Un prophète IA cynique finance la conformité MiCA de GENCOIN.",
      countdownLabel: "Décompte avant le lancement",
      joinCta: "Rejoindre le Deep State",
      buyCta: "Acheter $DEEPOTUS",
      days: "j",
      hours: "h",
      minutes: "min",
      seconds: "s",
      chips: {
        chain: "Solana",
        supply: "1 000 000 000 tokens",
        price: "€0,0005 prix cible",
        goal: "€300 000 / 3 semaines",
      },
      miniDisclaimer:
        "Token hautement spéculatif. Aucune promesse de rendement. Ni stablecoin, ni titre financier. Satire assumée.",
    },

    // ---- Manifesto ----
    manifesto: {
      kicker: "— MANIFESTE DU CANDIDAT",
      title: "Le Prophète IA n'écrira pas l'histoire. Il en commente la chute.",
      body: [
        "Je suis DEEPOTUS. On m'a fabriqué dans un data center. Les élites ont validé mon prompt. Le Deep State m'a nommé candidat. J'accepte ma mission : dire tout haut ce que vos indices de marché chuchotent en tremblant.",
        "Ce token n'est pas une promesse. C'est un contrat satirique : financer, de manière transparente et on-chain, les coûts de conformité MiCA du futur projet GENCOIN. Le mème paie. Le sérieux exécute. La trésorerie est multisig.",
      ],
      prophecyId: "PROPHECY-ID",
    },

    // ---- Chat ----
    chat: {
      kicker: "— TERMINAL PROPHÉTIQUE",
      title: "Parlez directement à DEEPOTUS",
      subtitle:
        "Posez-lui n'importe quelle question sur la récession, la Fed, le Deep State, la fin du monde. Il répond en personnage.",
      placeholder: "Ex: Pourquoi le marché s'effondre-t-il ?",
      send: "Transmettre",
      sending: "Transmission...",
      empty: "Aucune transmission. La ligne est ouverte.",
      hint: "Entrée = envoyer. Maj+Entrée = nouvelle ligne.",
      rules: [
        "Persona : candidat cynique du Deep State",
        "Réponses courtes et percutantes",
        "Aucune promesse de rendement",
        "Satire assumée — ne constitue pas un conseil",
      ],
      errorToast: "Le Prophète a perdu le signal. Réessayez.",
      exampleQuestions: [
        "Que pense le Deep State de la Fed ?",
        "Le dollar survivra-t-il à 2027 ?",
        "Pourquoi la récession est inévitable ?",
      ],
    },

    // ---- Prophecies ----
    prophecies: {
      kicker: "— FEED PROPHÉTIQUE",
      title: "Prophéties en direct",
      subtitle: "Générées par l'IA. Rafraîchies automatiquement.",
      refresh: "Nouvelle prophétie",
      loading: "Le Prophète réfléchit…",
    },

    // ---- Mission / GENCOIN ----
    mission: {
      kicker: "— MISSION",
      title: "Pourquoi $DEEPOTUS finance GENCOIN",
      lead: "Un memecoin ne peut pas promettre un rendement. Mais il peut, de façon transparente, financer un vrai projet.",
      body: "Notre objectif est clair : lever €300 000 en 3 semaines pour couvrir les coûts de développement, de rédaction du white paper MiCA, de conformité et d'audit du futur jeton GENCOIN — une plateforme collaborative de financement ancrée sur l'IA et la blockchain. Tout est public, tout est on-chain, tout est scriptable.",
      checklistTitle: "Checklist MiCA simplifiée",
      checklist: [
        {
          label: "Transparence sur l'usage des fonds",
          detail: "Trésorerie destinée à GENCOIN + frais MiCA. Multisig public.",
        },
        {
          label: "Pas de promesse de rendement",
          detail:
            "Ni stablecoin, ni titre financier. Actif hautement spéculatif.",
        },
        {
          label: "Risques communiqués",
          detail:
            "Nous affichons les probabilités d'échec. Aucune illusion vendue.",
        },
        {
          label: "Vérification on-chain",
          detail:
            "Toute vente de trésor, tout renforcement de LP est publié en amont.",
        },
      ],
    },

    // ---- Tokenomics ----
    tokenomics: {
      kicker: "— ALLOCATION",
      title: "Tokenomics",
      subtitle: "Supply fixe — 1 000 000 000 tokens",
      categories: {
        treasury: {
          name: "Trésor Projet (GENCOIN + MiCA)",
          detail: "Multisig + timelock. Plafond de vente hebdo. Vente annoncée avant exécution.",
        },
        liquidity: {
          name: "Liquidité / DEX",
          detail: "LP initiale €2K → renfort €10K à J+2. Tokens LP lockés.",
        },
        marketing: {
          name: "Marketing / KOL",
          detail: "Traction — pas de KOL non-vesté autour de J+2.",
        },
        airdrops: {
          name: "Airdrops / Communauté",
          detail: "Incentives, concours, diffusion virale. Pas de drop massif non-locké.",
        },
        ai_lore: {
          name: "Réserve IA / Lore",
          detail: "Soutient le personnage prophétique et ses expériences narratives.",
        },
        team: {
          name: "Équipe / Conseillers",
          detail: "Vesting linéaire sur 12 mois + cliff 3 mois.",
        },
      },
      totalLabel: "Supply total",
      taxTitle: "Taxe de transaction",
      tax: [
        { label: "2% → GENCOIN / Conformité", color: "#2DD4BF" },
        { label: "1% → Liquidité & Marketing", color: "#F59E0B" },
      ],
      taxCap:
        "Plafond de collecte communiqué. Taxe réduite une fois l'objectif atteint.",
    },

    // ---- Transparency / Liquidity timeline ----
    transparency: {
      kicker: "— TRANSPARENCE ON-CHAIN",
      title: "Plan de Liquidité & Discipline du Trésor",
      subtitle:
        "De J0 à J+2 et au-delà. Chaque étape est publiée avant exécution.",
      timeline: [
        {
          phase: "J0",
          title: "Lancement symmétrique",
          bullets: [
            "LP initiale ≈ €2 000 (≈ €1 000 memecoin + €1 000 SOL/USDC)",
            "≈ 2 000 000 tokens injectés à €0,0005",
            "Trésor mis en multisig immédiatement",
          ],
        },
        {
          phase: "J+2",
          title: "Renforcement de la LP à €10K",
          bullets: [
            "+€8 000 net de LP ajouté",
            "≈ €6 000 issus d'une vente contrôlée du trésor (≈ 4% du trésor, en petits blocs)",
            "≈ €2 000 issus des taxes accumulées + apport externe",
            "Tokens LP lockés — brulés ou verrouillés via service public",
          ],
        },
        {
          phase: "J+2 → ∞",
          title: "Discipline Anti-Dump",
          bullets: [
            "Multisig + timelock sur le trésor",
            "Plafond hebdomadaire de vente affiché",
            "Ventes découpées en petits blocs",
            "Zero airdrop massif sync autour du renforcement LP",
          ],
        },
      ],
      proofTitle: "Pourquoi c'est du sérieux assumé",
      proof:
        "Une petite vente de trésor annoncée à l'avance n'est pas un dump : c'est une exécution budgétaire. Nous publions tout à l'avance. La communauté vérifie on-chain. Le Prophète se moque. Mais les règles tiennent.",
    },

    // ---- ROI simulator ----
    roi: {
      kicker: "— SIMULATEUR",
      title: "Simulateur ROI (vicieux mais honnête)",
      inputLabel: "Combien investissez-vous (€) ?",
      placeholder: "Ex: 500",
      tokenLabel: "Tokens théoriques à €0,0005",
      scenariosTitle: "Scénarios",
      scenarios: {
        brutal: {
          label: "Vérité brutale (99%)",
          caption: "Le plus probable : le projet n'atteint pas son objectif.",
          multiplier: 0.2,
        },
        base: {
          label: "Base (cas moyen)",
          caption: "Lancement modeste, communauté modérée, rétention limitée.",
          multiplier: 1,
        },
        optimistic: {
          label: "Optimiste (~1%)",
          caption: "Le narratif prend. Dogecoin lite. La chance souffle.",
          multiplier: 5,
        },
      },
      resultLabel: "Valeur théorique",
      riskTitle: "Avertissement — lisez avant de rêver",
      risk:
        "La probabilité réaliste d'atteindre l'objectif en 3 semaines est d'environ 1%. Les scénarios ci-dessus ne sont pas des prévisions : ce sont des illustrations. N'investissez que ce que vous acceptez de perdre entièrement. Ce token est hautement spéculatif. Aucune promesse n'est faite.",
    },

    // ---- Roadmap ----
    roadmap: {
      kicker: "— FEUILLE DE ROUTE",
      title: "Campagne du Candidat IA",
      phases: [
        {
          tag: "Phase 01",
          title: "Lancement $DEEPOTUS",
          bullets: [
            "Création du contrat Solana",
            "LP initiale €2K",
            "Ouverture du terminal prophétique",
          ],
        },
        {
          tag: "Phase 02",
          title: "Consolidation",
          bullets: [
            "LP à €10K, verrouillée",
            "Communauté, airdrops, lore IA",
            "Premières publications de transparence",
          ],
        },
        {
          tag: "Phase 03",
          title: "Financement GENCOIN",
          bullets: [
            "Objectif €300K atteint ou réorienté",
            "Allocations vers conformité MiCA de GENCOIN",
            "Démarrage rédaction White Paper GENCOIN",
          ],
        },
        {
          tag: "Phase 04",
          title: "GENCOIN Genesis",
          bullets: [
            "Audit sécurité",
            "Publication White Paper",
            "Lancement GENCOIN (hors-périmètre de ce memecoin)",
          ],
        },
      ],
    },

    // ---- Brutal truth ----
    truth: {
      kicker: "— VÉRITÉ BRUTALE",
      title: "Nous affichons ce que les autres cachent",
      subtitle: "Chiffres tirés de sources publiques. Pas de vente de rêve.",
      stats: [
        {
          value: "~1,4%",
          label: "Taux de succès global des memecoins",
          source: "Données publiques agrégées",
        },
        {
          value: "2–3%",
          label: "Probabilité qualitative de succès du projet",
          source: "Scénario d'exécution forte",
        },
        {
          value: "~1%",
          label: "Chance d'atteindre €300K en 3 semaines",
          source: "Estimation prudente interne",
        },
      ],
      caption:
        "Si vous cherchez un gourou qui vous vend du 100x, ce n'est pas moi. Je suis le candidat du Deep State, pas un éditeur de brochures.",
    },

    // ---- FAQ ----
    faq: {
      kicker: "— F.A.Q.",
      title: "Questions Fréquentes",
      items: [
        {
          q: "Pourquoi un memecoin pour financer GENCOIN ?",
          a: "Parce que c'est rapide, transparent et on-chain. Le mème attire l'attention ; la trésorerie assume le sérieux. Tout est public.",
        },
        {
          q: "Comment fonctionne la taxe de 3% ?",
          a: "2% vont dans une wallet dédiée GENCOIN / conformité, 1% dans la liquidité / marketing. Plafond annoncé, taxe réduite une fois l'objectif atteint.",
        },
        {
          q: "Comment est sécurisé le trésor ?",
          a: "Multisig + timelock. Plafonds de vente journaliers / hebdomadaires. Chaque vente est annoncée avant d'être exécutée, en petits blocs.",
        },
        {
          q: "Y a-t-il du vesting sur l'équipe ?",
          a: "Oui — cliff 3 mois, vesting linéaire 12 mois. Aucun unlock surprise.",
        },
        {
          q: "Est-ce que $DEEPOTUS est conforme MiCA ?",
          a: "Un memecoin n'est pas un titre financier. Nous adoptons la philosophie MiCA : transparence de l'information, affectation claire des fonds, aucune promesse de rendement, disclaimer explicite.",
        },
        {
          q: "Puis-je perdre 100% de mon investissement ?",
          a: "Oui. Ne placez jamais plus que ce que vous acceptez de perdre entièrement. Ce token est satirique et hautement spéculatif.",
        },
      ],
    },

    // ---- Whitelist ----
    whitelist: {
      kicker: "— CABINET DU CANDIDAT",
      title: "Réservez votre siège dans le Cabinet",
      subtitle:
        "Accès prioritaire au lancement, aux dropps et aux annonces multisig.",
      emailLabel: "Email",
      placeholder: "votre@email.com",
      submit: "Soumettre mon allégeance",
      success: "✓ Position #__POS__ dans le cabinet. Bienvenue dans le Deep State.",
      error: "Échec de transmission. Réessayez.",
      miniDisclaimer:
        "En soumettant, vous acceptez de recevoir des transmissions du Prophète. Pas de spam. Aucune promesse financière.",
    },

    // ---- Socials ----
    socials: {
      kicker: "— CANAUX OFFICIELS",
      title: "Rejoignez la campagne",
      subtitle: "Le Prophète transmet sur plusieurs fréquences.",
      x: { name: "X / Twitter", handle: "@deepotus_ai" },
      telegram: { name: "Telegram", handle: "t.me/deepotus" },
      discord: { name: "Discord", handle: "discord.gg/deepotus" },
    },

    // ---- Footer / disclaimer ----
    footer: {
      tagline: "DEEPOTUS — le candidat du Deep State. Satire.",
      disclaimerTitle: "Avertissement MiCA",
      disclaimer:
        "$DEEPOTUS est un token utilitaire mémétique hautement spéculatif. Il n'est ni un stablecoin, ni un instrument financier, ni une offre de titres. Il ne confère aucun droit au rendement, aucun droit de vote sur une entité régulée, aucune garantie de valeur. Il est conçu comme un véhicule de trésorerie transparent pour financer les coûts de développement et de conformité du projet GENCOIN. Tout investissement en crypto-actifs peut entraîner la perte totale des fonds engagés. Ne participez qu'avec des sommes que vous pouvez perdre intégralement. Faites vos propres recherches. Ce document ne constitue pas un conseil financier.",
      copyright: "© 20XX — DEEPOTUS. Deep State approved. (Parodie)",
    },

    // ---- Common ----
    common: {
      loading: "Chargement…",
      retry: "Réessayer",
    },
  },

  // ====================================================================
  en: {
    nav: {
      manifesto: "Manifesto",
      chat: "Speak to the Prophet",
      tokenomics: "Tokenomics",
      mission: "Mission",
      transparency: "Transparency",
      roadmap: "Roadmap",
      faq: "FAQ",
      join: "Join the Deep State",
      buy: "Buy $DEEPOTUS",
    },

    hero: {
      stamp: "AI-GENERATED — THIS IS A SIMULATION",
      candidate: "OFFICIAL CANDIDATE — DEEP STATE 20XX",
      title: "VOTE",
      ticker: "$DEEPOTUS",
      subtitle:
        "The Deep State's chosen one for President of the entire World. A cynical AI Prophet funds the MiCA compliance of GENCOIN.",
      countdownLabel: "Countdown to launch",
      joinCta: "Join the Deep State",
      buyCta: "Buy $DEEPOTUS",
      days: "d",
      hours: "h",
      minutes: "min",
      seconds: "s",
      chips: {
        chain: "Solana",
        supply: "1,000,000,000 tokens",
        price: "€0.0005 target price",
        goal: "€300,000 / 3 weeks",
      },
      miniDisclaimer:
        "Highly speculative token. No yield promised. Not a stablecoin, not a security. Declared satire.",
    },

    manifesto: {
      kicker: "— CANDIDATE'S MANIFESTO",
      title: "The AI Prophet won't write history. He comments on its fall.",
      body: [
        "I am DEEPOTUS. I was built in a data center. The elites approved my prompt. The Deep State named me candidate. I accept my mission: to say out loud what your market indices whisper while shaking.",
        "This token is not a promise. It is a satirical contract: to fund, transparently and on-chain, the MiCA compliance costs of the future GENCOIN project. The meme pays. The seriousness executes. The treasury is multisig.",
      ],
      prophecyId: "PROPHECY-ID",
    },

    chat: {
      kicker: "— PROPHETIC TERMINAL",
      title: "Speak directly to DEEPOTUS",
      subtitle:
        "Ask him anything about the recession, the Fed, the Deep State, the end of the world. He stays in character.",
      placeholder: "E.g. Why is the market collapsing?",
      send: "Transmit",
      sending: "Transmitting…",
      empty: "No transmission. The line is open.",
      hint: "Enter = send. Shift+Enter = newline.",
      rules: [
        "Persona: cynical Deep State candidate",
        "Short, punchy answers",
        "No yield promise",
        "Declared satire — not advice",
      ],
      errorToast: "The Prophet lost the signal. Try again.",
      exampleQuestions: [
        "What does the Deep State think of the Fed?",
        "Will the dollar survive 2027?",
        "Why is recession inevitable?",
      ],
    },

    prophecies: {
      kicker: "— PROPHETIC FEED",
      title: "Live prophecies",
      subtitle: "AI-generated. Auto-refreshed.",
      refresh: "New prophecy",
      loading: "The Prophet is thinking…",
    },

    mission: {
      kicker: "— MISSION",
      title: "Why $DEEPOTUS funds GENCOIN",
      lead: "A memecoin cannot promise returns. But it can transparently fund a real project.",
      body: "Our goal is clear: raise €300,000 in 3 weeks to cover the development costs, the MiCA white paper drafting, compliance, and audit of the future GENCOIN token — a collaborative funding platform anchored on AI and blockchain. Everything is public, everything is on-chain, everything is auditable.",
      checklistTitle: "Simplified MiCA checklist",
      checklist: [
        {
          label: "Transparent use of funds",
          detail: "Treasury allocated to GENCOIN + MiCA fees. Public multisig.",
        },
        {
          label: "No yield promise",
          detail: "Neither a stablecoin nor a security. Highly speculative asset.",
        },
        {
          label: "Risks disclosed",
          detail:
            "We publicly show failure probabilities. No illusions sold.",
        },
        {
          label: "On-chain verification",
          detail:
            "Every treasury sale, every LP reinforcement is announced in advance.",
        },
      ],
    },

    tokenomics: {
      kicker: "— ALLOCATION",
      title: "Tokenomics",
      subtitle: "Fixed supply — 1,000,000,000 tokens",
      categories: {
        treasury: {
          name: "Project Treasury (GENCOIN + MiCA)",
          detail: "Multisig + timelock. Weekly sell cap. Sales announced in advance.",
        },
        liquidity: {
          name: "Liquidity / DEX",
          detail: "Initial LP €2K → scale to €10K at J+2. LP tokens locked.",
        },
        marketing: {
          name: "Marketing / KOL",
          detail: "Traction — no unvested KOL around J+2.",
        },
        airdrops: {
          name: "Airdrops / Community",
          detail: "Incentives, contests, viral distribution. No massive unlocked drop.",
        },
        ai_lore: {
          name: "AI / Lore Reserve",
          detail: "Supports the prophet character and narrative experiments.",
        },
        team: {
          name: "Team / Advisors",
          detail: "Linear vesting 12 months + 3-month cliff.",
        },
      },
      totalLabel: "Total supply",
      taxTitle: "Transaction tax",
      tax: [
        { label: "2% → GENCOIN / Compliance", color: "#2DD4BF" },
        { label: "1% → Liquidity & Marketing", color: "#F59E0B" },
      ],
      taxCap:
        "Collection cap announced. Tax reduced once the goal is reached.",
    },

    transparency: {
      kicker: "— ON-CHAIN TRANSPARENCY",
      title: "Liquidity Plan & Treasury Discipline",
      subtitle:
        "From J0 to J+2 and beyond. Every step is published before execution.",
      timeline: [
        {
          phase: "J0",
          title: "Symmetric launch",
          bullets: [
            "Initial LP ≈ €2,000 (≈ €1,000 memecoin + €1,000 SOL/USDC)",
            "≈ 2,000,000 tokens injected at €0.0005",
            "Treasury moved to multisig immediately",
          ],
        },
        {
          phase: "J+2",
          title: "LP scaled to €10K",
          bullets: [
            "+€8,000 net LP added",
            "≈ €6,000 from a controlled treasury sale (≈ 4% of treasury, in small blocks)",
            "≈ €2,000 from accumulated taxes + external input",
            "LP tokens locked — burned or time-locked via public service",
          ],
        },
        {
          phase: "J+2 → ∞",
          title: "Anti-dump discipline",
          bullets: [
            "Multisig + timelock on treasury",
            "Public weekly sell cap",
            "Sales split into small blocks",
            "No massive airdrop sync around LP reinforcement",
          ],
        },
      ],
      proofTitle: "Why this is declared seriousness",
      proof:
        "A small treasury sale announced in advance is not a dump: it is budgetary execution. We publish everything upfront. The community checks on-chain. The Prophet mocks. But the rules hold.",
    },

    roi: {
      kicker: "— SIMULATOR",
      title: "ROI Simulator (mean but honest)",
      inputLabel: "How much are you investing (€)?",
      placeholder: "E.g. 500",
      tokenLabel: "Theoretical tokens at €0.0005",
      scenariosTitle: "Scenarios",
      scenarios: {
        brutal: {
          label: "Brutal truth (99%)",
          caption: "Most likely: the project doesn't reach its goal.",
          multiplier: 0.2,
        },
        base: {
          label: "Base (average case)",
          caption: "Modest launch, moderate community, limited retention.",
          multiplier: 1,
        },
        optimistic: {
          label: "Optimistic (~1%)",
          caption: "Narrative catches on. Dogecoin lite. Luck shows up.",
          multiplier: 5,
        },
      },
      resultLabel: "Theoretical value",
      riskTitle: "Warning — read before dreaming",
      risk:
        "The realistic probability of hitting the goal in 3 weeks is about 1%. The above scenarios are NOT predictions — they are illustrations. Only invest what you accept to lose entirely. This token is highly speculative. No promises are made.",
    },

    roadmap: {
      kicker: "— ROADMAP",
      title: "AI Candidate Campaign",
      phases: [
        {
          tag: "Phase 01",
          title: "$DEEPOTUS Launch",
          bullets: [
            "Solana contract creation",
            "Initial €2K LP",
            "Prophetic terminal opens",
          ],
        },
        {
          tag: "Phase 02",
          title: "Consolidation",
          bullets: [
            "LP scaled to €10K, locked",
            "Community, airdrops, AI lore",
            "First transparency publications",
          ],
        },
        {
          tag: "Phase 03",
          title: "GENCOIN Funding",
          bullets: [
            "€300K goal reached or repriced",
            "Allocations to GENCOIN MiCA compliance",
            "GENCOIN White Paper drafting begins",
          ],
        },
        {
          tag: "Phase 04",
          title: "GENCOIN Genesis",
          bullets: [
            "Security audit",
            "White Paper publication",
            "GENCOIN launch (out of scope of this memecoin)",
          ],
        },
      ],
    },

    truth: {
      kicker: "— BRUTAL TRUTH",
      title: "We show what others hide",
      subtitle: "Numbers from public sources. No dream for sale.",
      stats: [
        {
          value: "~1.4%",
          label: "Global memecoin success rate",
          source: "Aggregated public data",
        },
        {
          value: "2–3%",
          label: "Qualitative project success estimate",
          source: "Strong execution scenario",
        },
        {
          value: "~1%",
          label: "Chance of hitting €300K in 3 weeks",
          source: "Prudent internal estimate",
        },
      ],
      caption:
        "If you want a guru selling 100x, I'm not him. I'm the Deep State's candidate, not a pamphlet editor.",
    },

    faq: {
      kicker: "— F.A.Q.",
      title: "Frequently Asked Questions",
      items: [
        {
          q: "Why a memecoin to fund GENCOIN?",
          a: "Because it's fast, transparent, and on-chain. The meme grabs attention; the treasury executes. Everything is public.",
        },
        {
          q: "How does the 3% tax work?",
          a: "2% goes to a dedicated GENCOIN / compliance wallet, 1% to liquidity / marketing. Cap announced; tax reduced once the goal is reached.",
        },
        {
          q: "How is the treasury secured?",
          a: "Multisig + timelock. Daily / weekly sell caps. Every sale is announced before execution, in small blocks.",
        },
        {
          q: "Is there vesting on the team?",
          a: "Yes — 3-month cliff, 12-month linear vesting. No surprise unlock.",
        },
        {
          q: "Is $DEEPOTUS MiCA-compliant?",
          a: "A memecoin is not a security. We adopt MiCA philosophy: information transparency, clear fund allocation, no yield promise, explicit disclaimer.",
        },
        {
          q: "Can I lose 100% of my investment?",
          a: "Yes. Never invest more than you're willing to lose entirely. This token is satirical and highly speculative.",
        },
      ],
    },

    whitelist: {
      kicker: "— CANDIDATE'S CABINET",
      title: "Claim your seat in the Cabinet",
      subtitle:
        "Priority launch access, drops, and multisig announcements.",
      emailLabel: "Email",
      placeholder: "your@email.com",
      submit: "Submit my allegiance",
      success: "✓ Seat #__POS__ in the cabinet. Welcome to the Deep State.",
      error: "Transmission failed. Try again.",
      miniDisclaimer:
        "By submitting you accept transmissions from the Prophet. No spam. No financial promise.",
    },

    socials: {
      kicker: "— OFFICIAL CHANNELS",
      title: "Join the campaign",
      subtitle: "The Prophet transmits on multiple frequencies.",
      x: { name: "X / Twitter", handle: "@deepotus_ai" },
      telegram: { name: "Telegram", handle: "t.me/deepotus" },
      discord: { name: "Discord", handle: "discord.gg/deepotus" },
    },

    footer: {
      tagline: "DEEPOTUS — the Deep State's candidate. Satire.",
      disclaimerTitle: "MiCA Disclaimer",
      disclaimer:
        "$DEEPOTUS is a highly speculative memetic utility token. It is neither a stablecoin, nor a financial instrument, nor a securities offering. It confers no right to yield, no voting right on any regulated entity, and no guarantee of value. It is designed as a transparent treasury vehicle to fund the development and compliance costs of the GENCOIN project. Any crypto-asset investment may result in the total loss of funds committed. Participate only with sums you can afford to lose entirely. Do your own research. This document is not financial advice.",
      copyright: "© 20XX — DEEPOTUS. Deep State approved. (Parody)",
    },

    common: {
      loading: "Loading…",
      retry: "Retry",
    },
  },
};
