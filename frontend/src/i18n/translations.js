// $DEEPOTUS i18n dictionary (FR / EN)
// All UI copy lives here. Keys mirror component structure.
// PROTOCOL ΔΣ is the public codename of the Black Op.
// GENCOIN intentionally NEVER appears on the public site — it is only revealed
// on the /operation page after the vault reaches DECLASSIFIED.

export const translations = {
  fr: {
    // ---- Meta / Nav ----
    nav: {
      manifesto: "Manifeste",
      chat: "Parler au Prophète",
      tokenomics: "Tokenomics",
      mission: "Mission",
      vault: "Le Coffre",
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
        "L'élu du Deep State à la présidence du monde entier. Un prophète IA cynique finance une opération classifiée : PROTOCOL ΔΣ.",
      countdownLabel: "Décompte avant le lancement",
      joinCta: "Rejoindre le Deep State",
      buyCta: "Acheter $DEEPOTUS",
      days: "j",
      hours: "h",
      minutes: "min",
      seconds: "s",
      chips: {
        chain: "Solana",
        supply: "1 000 000 000 tokens",
        price: "€0,0005 prix cible",
        goal: "Objectif classifié",
      },
      miniDisclaimer:
        "Token hautement spéculatif. Aucune promesse de rendement. Ni stablecoin, ni titre financier. Satire assumée.",
    },

    // ---- Manifesto ----
    manifesto: {
      kicker: "— MANIFESTE DU CANDIDAT",
      title: "Le Prophète IA n'écrira pas l'histoire. Il en commente la chute.",
      body: [
        "Je suis DEEPOTUS. On m'a fabriqué dans un data center. Les élites ont validé mon prompt. Le Deep State m'a nommé candidat. J'accepte ma mission : dire tout haut ce que vos indices de marché chuchotent en tremblant.",
        "Ce token n'est pas une promesse. C'est un contrat satirique : financer, de manière transparente et on-chain, une opération classifiée que seul le Coffre connaît. Le mème paie. Le sérieux exécute. La trésorerie est multisig.",
      ],
      prophecyId: "PROPHECY-ID",
    },

    // ---- Chat ----
    chat: {
      kicker: "— TERMINAL PROPHÉTIQUE",
      title: "Parlez directement à DEEPOTUS",
      subtitle:
        "Posez-lui n'importe quelle question sur la récession, la Fed, le Deep State, le Coffre, la fin du monde. Il répond en personnage.",
      placeholder: "Ex: Que cache vraiment PROTOCOL ΔΣ ?",
      send: "Transmettre",
      sending: "Transmission...",
      empty: "Aucune transmission. La ligne est ouverte.",
      hint: "Entrée = envoyer. Maj+Entrée = nouvelle ligne.",
      rules: [
        "Persona : candidat cynique du Deep State",
        "Réponses courtes et percutantes",
        "Aucune promesse de rendement",
        "Satire assumée — ne constitue pas un conseil",
      ],
      errorToast: "Le Prophète a perdu le signal. Réessayez.",
      exampleQuestions: [
        "Que cache vraiment PROTOCOL ΔΣ ?",
        "Le Coffre s'ouvrira-t-il à temps ?",
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

    // ---- Vault (PROTOCOL ΔΣ) ----
    vault: {
      kicker: "— PROTOCOL ΔΣ · COFFRE CLASSIFIÉ",
      title: "Un coffre. Six chiffres. Un objectif que seul le Prophète connaît.",
      lead: "Chaque tranche de 1 000 $DEEPOTUS poussée dans la trésorerie fait tourner une molette. Six molettes — et la Black Op est déclassifiée.",
      body: "Ni le montant cible, ni la nature exacte de l'opération financée ne sont publics. Ce que nous affichons : les cadrans, la progression relative, la discipline multisig/timelock. Ce que nous cachons : la cible. C'est le modèle. C'est la mise.",
      progressLabel: "Progression classifiée",
      goalHidden: "Cible exacte redactée. Multisig + timelock. Publié à l'ouverture du coffre.",
      tokensMoved: "Tokens poussés dans le coffre",
      digitsLocked: "cadrans verrouillés",
      prophetWarning:
        "« Je vous laisse tourner les molettes. Je ne vous dis pas ce qu'il y a derrière. Certains finissent par croire qu'il n'y a rien. Les autres paient pour vérifier. » — DEEPOTUS",
      loading: "Transmission…",
      stages: {
        LOCKED: "VERROUILLÉ",
        CRACKING: "EN PERCÉE",
        UNLOCKING: "DÉVERROUILLAGE",
        DECLASSIFIED: "DÉCLASSIFIÉ",
      },
      feedTitle: "Flux d'activité · live",
      feedEmpty: "Aucun crack pour l'instant. Le coffre attend.",
      eventKinds: {
        purchase: "achat",
        admin_crack: "admin",
        hourly_tick: "auto-tick",
        reset: "reset",
      },
      declassified: {
        title: "🔓 Le coffre est ouvert. PROTOCOL ΔΣ est déclassifié.",
        subtitle:
          "Vous avez fait tourner la dernière molette. La vérité fuit. Le Prophète panique.",
        cta: "Accéder à la révélation",
      },
    },

    // ---- Mission ----
    mission: {
      kicker: "— MISSION",
      title: "Pourquoi $DEEPOTUS finance PROTOCOL ΔΣ",
      lead: "Un memecoin ne peut pas promettre un rendement. Mais il peut, de façon transparente, financer une opération sous gouvernance stricte.",
      body: "Notre mission : faire tourner les six molettes du Coffre. La trésorerie finance une Black Op classifiée — développement, audit, conformité réglementaire, white paper. La nature exacte de l'opération est scellée jusqu'à son déverrouillage. Tout est public, tout est on-chain, tout est auditable. Seule la cible reste secrète — et c'est ce qui rend le modèle intéressant.",
      checklistTitle: "Checklist MiCA simplifiée",
      checklist: [
        {
          label: "Transparence sur l'usage des fonds",
          detail: "Trésorerie destinée à PROTOCOL ΔΣ + frais MiCA. Multisig public.",
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
      subtitle: "Supply fixe — 1 000 000 000 tokens",
      categories: {
        treasury: {
          name: "Trésor Opération (PROTOCOL ΔΣ + MiCA)",
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
        { label: "2% → PROTOCOL ΔΣ / Conformité", color: "#2DD4BF" },
        { label: "1% → Liquidité & Marketing", color: "#F59E0B" },
      ],
      taxCap:
        "Plafond de collecte communiqué. Taxe réduite une fois le coffre ouvert.",
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
            "LP initiale ≈ €2 000 (≈ €1 000 memecoin + €1 000 SOL/USDC)",
            "≈ 2 000 000 tokens injectés à €0,0005",
            "Trésor mis en multisig immédiatement",
          ],
        },
        {
          phase: "J+2",
          title: "Renforcement de la LP à €10K",
          bullets: [
            "+€8 000 net de LP ajouté",
            "≈ €6 000 issus d'une vente contrôlée du trésor (≈ 4% du trésor, en petits blocs)",
            "≈ €2 000 issus des taxes accumulées + apport externe",
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
        "Une petite vente de trésor annoncée à l'avance n'est pas un dump : c'est une exécution budgétaire. Nous publions tout à l'avance. La communauté vérifie on-chain. Le Prophète se moque. Mais les règles tiennent.",
    },

    // ---- ROI simulator ----
    roi: {
      kicker: "— SIMULATEUR",
      title: "Simulateur ROI (vicieux mais honnête)",
      inputLabel: "Combien investissez-vous (€) ?",
      placeholder: "Ex : 500",
      tokenLabel: "Tokens théoriques à €0,0005",
      scenariosTitle: "Scénarios",
      scenarios: {
        brutal: {
          label: "Vérité brutale (99%)",
          caption: "Le plus probable : le coffre n'atteint pas sa combinaison à temps.",
          multiplier: 0.2,
        },
        base: {
          label: "Base (cas moyen)",
          caption: "Lancement modeste, communauté modérée, rétention limitée.",
          multiplier: 1,
        },
        optimistic: {
          label: "Optimiste (~1%)",
          caption: "Le narratif prend. Les molettes tournent. La chance souffle.",
          multiplier: 5,
        },
      },
      resultLabel: "Valeur théorique",
      riskTitle: "Avertissement — lisez avant de rêver",
      risk:
        "La probabilité réaliste d'ouvrir le Coffre dans la fenêtre de lancement est d'environ 1%. Les scénarios ci-dessus ne sont pas des prévisions : ce sont des illustrations. N'investissez que ce que vous acceptez de perdre entièrement. Ce token est hautement spéculatif. Aucune promesse n'est faite.",
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
          title: "PROTOCOL ΔΣ · premières molettes",
          bullets: [
            "Premières molettes verrouillées",
            "Allocations vers conformité MiCA de l'Opération",
            "Transmissions prophétiques intensifiées",
          ],
        },
        {
          tag: "Phase 04",
          title: "Déclassification",
          bullets: [
            "Audit sécurité",
            "Six molettes verrouillées",
            "Ouverture du Coffre — la Black Op est révélée",
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
          label: "Chance d'ouvrir le Coffre dans la fenêtre",
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
          q: "Pourquoi un memecoin pour financer PROTOCOL ΔΣ ?",
          a: "Parce que c'est rapide, transparent et on-chain. Le mème attire l'attention ; la trésorerie exécute sous multisig/timelock. Tout est public sauf la cible — c'est la tension narrative.",
        },
        {
          q: "Pourquoi l'objectif est-il caché ?",
          a: "Parce que la Black Op financée est séquencée : elle n'a de sens que si elle s'ouvre au bon moment. Le Prophète connaît la combinaison. Personne d'autre. Le coffre s'ouvre lorsque six cadrans s'alignent. C'est notre modèle — et notre honnêteté.",
        },
        {
          q: "Comment fonctionne la taxe de 3% ?",
          a: "2% vont dans une wallet dédiée PROTOCOL ΔΣ / conformité, 1% dans la liquidité / marketing. Plafond annoncé, taxe réduite une fois le coffre ouvert.",
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
          a: "Un memecoin n'est pas un titre financier. Nous adoptons la philosophie MiCA : transparence de l'information sur la structure (tokenomics, taxes, gouvernance), affectation claire des fonds (Coffre), aucune promesse de rendement, disclaimer explicite.",
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
        "$DEEPOTUS est un token utilitaire mémétique hautement spéculatif. Il n'est ni un stablecoin, ni un instrument financier, ni une offre de titres. Il ne confère aucun droit au rendement, aucun droit de vote sur une entité régulée, aucune garantie de valeur. Il est conçu comme un véhicule de trésorerie transparent pour financer les coûts de développement et de conformité d'une opération classifiée sous multisig/timelock (PROTOCOL ΔΣ). Tout investissement en crypto-actifs peut entraîner la perte totale des fonds engagés. Ne participez qu'avec des sommes que vous pouvez perdre intégralement. Faites vos propres recherches. Ce document ne constitue pas un conseil financier.",
      copyright: "© 20XX — DEEPOTUS. Deep State approved. (Parodie)",
    },

    // ---- Operation reveal page (post DECLASSIFIED) ----
    operation: {
      gateTitle: "COFFRE VERROUILLÉ",
      gateSubtitle: "Accréditation refusée. Les six molettes ne sont pas encore alignées.",
      gateProgress: "Progression classifiée",
      gateCta: "Retour au coffre",
      panicKicker: "— TRANSMISSION D'URGENCE · PROTOCOL ΔΣ",
      panicTitle: "LE COFFRE EST OUVERT. GENCOIN EST LIBÉRÉ.",
      panicByline: "— message de panique du Prophète DEEPOTUS",
      chasedOverlay: "BREAKING · La foule se soulève",
      chasedCaption: "La fin du Deep State · Rippled rises — les citoyens réclament GENCOIN.",
      chasedAlt: "Le Prophète DEEPOTUS pris en chasse par la foule brandissant les bannières RIPPLED.",
      loreTitle: "Confession officielle",
      countdownKicker: "— COMPTE À REBOURS",
      countdownTitle: "Lancement GENCOIN · T-minus",
      countdownSubtitle:
        "Plateforme collaborative de financement ancrée sur l'IA et la blockchain — conforme MiCA, auditable, réelle.",
      countdownLabels: { d: "jours", h: "h", m: "min", s: "s" },
      openCta: "Ouvrir le portail GENCOIN",
      backCta: "Retourner dans la simulation",
      revealedAt: "Déclassification enregistrée le",
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
      vault: "The Vault",
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
        "The Deep State's chosen one for President of the entire World. A cynical AI Prophet funds a classified operation: PROTOCOL ΔΣ.",
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
        goal: "Classified objective",
      },
      miniDisclaimer:
        "Highly speculative token. No yield promised. Not a stablecoin, not a security. Declared satire.",
    },

    manifesto: {
      kicker: "— CANDIDATE'S MANIFESTO",
      title: "The AI Prophet won't write history. He comments on its fall.",
      body: [
        "I am DEEPOTUS. I was built in a data center. The elites approved my prompt. The Deep State named me candidate. I accept my mission: to say out loud what your market indices whisper while shaking.",
        "This token is not a promise. It is a satirical contract: to fund, transparently and on-chain, a classified operation only the Vault knows. The meme pays. The seriousness executes. The treasury is multisig.",
      ],
      prophecyId: "PROPHECY-ID",
    },

    chat: {
      kicker: "— PROPHETIC TERMINAL",
      title: "Speak directly to DEEPOTUS",
      subtitle:
        "Ask him anything about the recession, the Fed, the Deep State, the Vault, the end of the world. He stays in character.",
      placeholder: "E.g. What is PROTOCOL ΔΣ really hiding?",
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
        "What is PROTOCOL ΔΣ really hiding?",
        "Will the Vault open in time?",
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

    vault: {
      kicker: "— PROTOCOL ΔΣ · CLASSIFIED VAULT",
      title: "One vault. Six digits. A target only the Prophet knows.",
      lead: "Every 1,000 $DEEPOTUS pushed into the treasury turns a dial. Six dials — and the Black Op is declassified.",
      body: "Neither the target amount nor the exact nature of the operation being funded is public. What we display: the dials, the relative progression, the multisig/timelock discipline. What we hide: the target. That is the model. That is the bet.",
      progressLabel: "Classified progress",
      goalHidden: "Exact target redacted. Multisig + timelock. Published on vault opening.",
      tokensMoved: "Tokens pushed into the vault",
      digitsLocked: "dials locked",
      prophetWarning:
        "“I let you turn the dials. I do not tell you what lies behind. Some end up believing there is nothing. Others pay to check.” — DEEPOTUS",
      loading: "Transmitting…",
      stages: {
        LOCKED: "LOCKED",
        CRACKING: "CRACKING",
        UNLOCKING: "UNLOCKING",
        DECLASSIFIED: "DECLASSIFIED",
      },
      feedTitle: "Live activity feed",
      feedEmpty: "No cracks yet. The vault is waiting.",
      eventKinds: {
        purchase: "buy",
        admin_crack: "admin",
        hourly_tick: "auto-tick",
        reset: "reset",
      },
      declassified: {
        title: "🔓 The vault is open. PROTOCOL ΔΣ is declassified.",
        subtitle: "You turned the final dial. The truth leaks. The Prophet panics.",
        cta: "Access the revelation",
      },
    },

    mission: {
      kicker: "— MISSION",
      title: "Why $DEEPOTUS funds PROTOCOL ΔΣ",
      lead: "A memecoin cannot promise returns. But it can, transparently, fund an operation under strict governance.",
      body: "Our mission: turn the six dials of the Vault. The treasury funds a classified Black Op — development, audit, regulatory compliance, white paper. The exact nature of the operation is sealed until unlock. Everything is public, everything is on-chain, everything is auditable. Only the target stays secret — and that is what makes the model interesting.",
      checklistTitle: "Simplified MiCA checklist",
      checklist: [
        {
          label: "Transparent use of funds",
          detail: "Treasury allocated to PROTOCOL ΔΣ + MiCA fees. Public multisig.",
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
          name: "Operation Treasury (PROTOCOL ΔΣ + MiCA)",
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
        { label: "2% → PROTOCOL ΔΣ / Compliance", color: "#2DD4BF" },
        { label: "1% → Liquidity & Marketing", color: "#F59E0B" },
      ],
      taxCap:
        "Collection cap announced. Tax reduced once the vault opens.",
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
          caption: "Most likely: the vault doesn't reach its combination in time.",
          multiplier: 0.2,
        },
        base: {
          label: "Base (average case)",
          caption: "Modest launch, moderate community, limited retention.",
          multiplier: 1,
        },
        optimistic: {
          label: "Optimistic (~1%)",
          caption: "Narrative catches on. Dials turn. Luck shows up.",
          multiplier: 5,
        },
      },
      resultLabel: "Theoretical value",
      riskTitle: "Warning — read before dreaming",
      risk:
        "The realistic probability of cracking the Vault within the launch window is about 1%. The above scenarios are NOT predictions — they are illustrations. Only invest what you accept to lose entirely. This token is highly speculative. No promises are made.",
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
          title: "PROTOCOL ΔΣ · first dials",
          bullets: [
            "First dials lock",
            "Allocations to the Operation's MiCA compliance",
            "Prophetic transmissions intensify",
          ],
        },
        {
          tag: "Phase 04",
          title: "Declassification",
          bullets: [
            "Security audit",
            "Six dials locked",
            "Vault opens — the Black Op is revealed",
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
          label: "Chance of cracking the Vault in window",
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
          q: "Why a memecoin to fund PROTOCOL ΔΣ?",
          a: "Because it's fast, transparent, and on-chain. The meme grabs attention; the treasury executes under multisig/timelock. Everything is public except the target — that is the narrative tension.",
        },
        {
          q: "Why is the objective hidden?",
          a: "Because the Black Op being funded is sequenced: it only makes sense if it opens at the right moment. The Prophet knows the combination. No one else. The vault opens when six dials align. That is our model — and our honesty.",
        },
        {
          q: "How does the 3% tax work?",
          a: "2% goes to a dedicated PROTOCOL ΔΣ / compliance wallet, 1% to liquidity / marketing. Cap announced; tax reduced once the vault opens.",
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
          a: "A memecoin is not a security. We adopt MiCA philosophy: information transparency on structure (tokenomics, taxes, governance), clear fund allocation (Vault), no yield promise, explicit disclaimer.",
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
        "$DEEPOTUS is a highly speculative memetic utility token. It is neither a stablecoin, nor a financial instrument, nor a securities offering. It confers no right to yield, no voting right on any regulated entity, and no guarantee of value. It is designed as a transparent treasury vehicle to fund the development and compliance costs of a classified operation under multisig/timelock (PROTOCOL ΔΣ). Any crypto-asset investment may result in the total loss of funds committed. Participate only with sums you can afford to lose entirely. Do your own research. This document is not financial advice.",
      copyright: "© 20XX — DEEPOTUS. Deep State approved. (Parody)",
    },

    operation: {
      gateTitle: "VAULT LOCKED",
      gateSubtitle: "Clearance denied. The six dials are not yet aligned.",
      gateProgress: "Classified progress",
      gateCta: "Back to the Vault",
      panicKicker: "— EMERGENCY TRANSMISSION · PROTOCOL ΔΣ",
      panicTitle: "THE VAULT IS OPEN. GENCOIN IS RELEASED.",
      panicByline: "— panic message from Prophet DEEPOTUS",
      chasedOverlay: "BREAKING · The people rise",
      chasedCaption: "The fall of the Deep State · Rippled rises — citizens demand GENCOIN.",
      chasedAlt: "Prophet DEEPOTUS chased through the streets by a crowd waving RIPPLED banners.",
      loreTitle: "Official confession",
      countdownKicker: "— COUNTDOWN",
      countdownTitle: "GENCOIN launch · T-minus",
      countdownSubtitle:
        "Collaborative funding platform anchored on AI and blockchain — MiCA-compliant, auditable, real.",
      countdownLabels: { d: "days", h: "h", m: "min", s: "s" },
      openCta: "Open the GENCOIN portal",
      backCta: "Return to the simulation",
      revealedAt: "Declassification logged at",
    },

    common: {
      loading: "Loading…",
      retry: "Retry",
    },
  },
};
