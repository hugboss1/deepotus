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
      requestClearance: "Demander un niveau d'accréditation",
      alreadyHaveCode: "J'ai déjà un numéro d'accréditation",
    },

    // ---- Terminal popup (Level 2 gatekeeper) ----
    terminal: {
      deniedLines: [
        "> VERIFYING CREDENTIALS…",
        "> clearance_level = 01 (WHITELISTED)",
        "> target_resource = PROTOCOL_ΔΣ · TRUE_VAULT",
        "> required_clearance = LEVEL_02",
        "",
        "[REFUS D'ACCÈS]",
        "",
        "Bien essayé, citoyen. Le coffre-fort que vous pensez avoir ouvert n'était qu'un leurre narratif — le niveau 01 ne vous donne que la version déclassifiée publique.",
        "",
        "Le VRAI coffre — celui qui contient le flux d'activité réel de $DEEPOTUS — requiert une accréditation de NIVEAU 02.",
        "",
        "Rassurez-vous : le Deep State est bureaucrate. Demandez votre carte. On vous l'enverra.",
      ],
      ctaRequest: "Demander l'accréditation niveau 02",
      ctaRetreat: "Retirer ma demande (retour)",
      formIntro:
        "Identifiez-vous. Le Deep State archivera votre dossier et vous délivrera une carte d'accès personnelle avec un numéro d'accréditation unique.",
      emailLabel: "Email de contact",
      emailPlaceholder: "votre@email.com",
      nameLabel: "Nom d'agent (facultatif)",
      namePlaceholder: "AGENT OMEGA-042",
      emailInvalid: "Email invalide. Réessayez.",
      submit: "Transmettre la demande",
      back: "Retour",
      successTitle: "TRANSMISSION REÇUE. DOSSIER ARCHIVÉ.",
      successInbox:
        "Votre carte d'accès est en route vers __EMAIL__ — délai typique : quelques secondes.",
      successNext: "Prochaine étape — ouvrir le véritable coffre",
      openVault: "Ouvrir le véritable coffre",
      close: "Fermer le terminal",
      retry: "Réessayer",
    },

    // ---- Classified vault (full-page real vault) ----
    classifiedVault: {
      gateKicker: "Accès restreint · NIVEAU 02",
      gateTitle: "Le véritable coffre-fort.",
      gateSubtitle:
        "Entrez votre numéro d'accréditation niveau 02. Il vous a été transmis par email sur votre carte d'accès Deep State.",
      gateLabel: "Numéro d'accréditation",
      gateError: "Accréditation invalide ou expirée.",
      gateHint:
        "Pas encore de numéro ? Rendez-vous sur la page d'accueil, ouvrez le terminal depuis la section du coffre et demandez votre accréditation niveau 02.",
      gateHintShort: "Saisir directement sur l'écran de la porte ↑",
      gateChannel: "CANAL SÉCURISÉ",
      gateLevel: "LEVEL 02 · PROTOCOL ΔΣ",
      gateIdle: "IDLE",
      gateBack: "Retour au site",
      verify: "Vérifier l'accès",
      verifying: "Vérification…",
      authedKicker: "CLEARANCE ACCORDÉE · NIVEAU 02",
      authedTitle: "Bienvenue dans le véritable coffre $DEEPOTUS.",
      authedSubtitle:
        "Ce que vous voyez ici est le flux réel de l'activité on-chain du jeton. Aucune mise en scène. Aucun filtre. La combinaison progresse littéralement au rythme des achats.",
      liveCombination: "Combinaison en direct",
      dials: "cadrans",
      progress: "progression",
      tokens: "tokens poussés",
      microTicks: "micro-rotations",
      treasury: "Trésor (€)",
      mode: "source",
      disclaimer:
        "Avertissement : le coffre évolue en fonction de l'activité on-chain réelle du jeton (DexScreener). Aucune promesse de rendement. Ce token est satirique et hautement spéculatif.",
      feedTitle: "Flux d'activité en direct",
      externalTitle: "Vérifier on-chain",
      sessionUntil: "Session jusqu'au",
      logout: "Déconnexion",
      declassified: {
        kicker: "PROTOCOL ΔΣ · DÉCLASSIFIÉ",
        title: "Le coffre est ouvert. La confession est disponible.",
        subtitle:
          "Le Prophète panique, la foule se soulève. Accédez à la révélation complète et au lancement GENCOIN.",
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
      kicker: "— ALLOCATION & DISCIPLINE",
      title: "Tokenomics · Protocole 0% Tax",
      subtitle: "Supply fixe — 1 000 000 000 tokens · Lancement sur Pump.fun",
      categories: {
        treasury: {
          name: "Trésor Opérationnel (PROTOCOL ΔΣ)",
          detail: "Réserve de guerre pour le futur projet MiCA-compliant. Multisig public. Financé par sa propre valorisation — jamais par vos échanges.",
        },
        liquidity: {
          name: "Liquidité & Ascension Raydium",
          detail: "Départ sur Pump.fun. Migration chirurgicale vers Raydium dès la complétion de la Bonding Curve. Renfort de LP pour stabiliser le prix cible ≈ 0,0005€.",
        },
        marketing: {
          name: "Traction & Opérations X/TG",
          detail: "Propagande et acquisition. Parce qu'un prophète silencieux ne sert à rien dans ce marché.",
        },
        airdrops: {
          name: "Communauté & Airdrops",
          detail: "Pour les agents actifs. Distributions ciblées et verrouillées pour récompenser la loyauté, pas le dump.",
        },
        ai_lore: {
          name: "Réserve IA & Lore",
          detail: "Maintient les serveurs de la simulation et alimente les prophéties quotidiennes.",
        },
        team: {
          name: "Équipe & Prophète",
          detail: "Vesting linéaire 12 mois + cliff 3 mois. Verrouillage public via Streamflow.",
        },
      },
      totalLabel: "Supply total",
      taxTitle: "0% TAX PROTOCOL",
      taxBadge: "Vélocité maximale",
      taxIntro: "Le Deep State a décidé d'éliminer les frictions inutiles. $DEEPOTUS adopte une structure 0% Tax à l'achat comme à la vente. Pas de frais cachés, pas de bureaucratie on-chain.",
      taxCap: "Le financement du PROTOCOL ΔΣ est assuré par la valorisation du Trésor (30%) — scellé en multisig, ventes planifiées et annoncées à l'avance.",
      cynicalTitle: "Transparence Cynique",
      cynicalBody: "L'absence de taxe signifie que nous comptons uniquement sur la croissance du jeton pour financer PROTOCOL ΔΣ. Si le prix monte, le coffre se remplit. Si le coffre se remplit, la vérité éclate. C'est le seul indicateur qui compte.",
    },

    // ---- Transparency / Liquidity timeline ----
    transparency: {
      kicker: "— TRANSPARENCE ON-CHAIN",
      title: "Lancement Pump.fun & Discipline du Trésor",
      subtitle:
        "De J0 à l'Ascension Raydium. Chaque étape est publiée avant exécution.",
      timeline: [
        {
          phase: "J0",
          title: "Lancement Pump.fun · 0% Tax",
          bullets: [
            "Mint 1 000 000 000 $DEEPOTUS · standard SPL Pump.fun",
            "Dev-buy modéré du fondateur pour crédibilité (annoncé on-chain)",
            "Tokens équipe lockés immédiatement via Streamflow (vesting 12m + cliff 3m)",
            "Trésor (30%) scellé en multisig public",
          ],
        },
        {
          phase: "Bonding Curve",
          title: "Montée sur la courbe de Pump.fun",
          bullets: [
            "Prix déterminé par la bonding curve — pas de taxe sur les swaps",
            "Objectif : atteindre 100% de la courbe (≈ 60k$ de MC)",
            "Le coffre commence à se verrouiller au fil des achats",
            "Aucune vente du trésor tant que la migration n'est pas faite",
          ],
        },
        {
          phase: "Ascension Raydium",
          title: "Migration automatique vers Raydium",
          bullets: [
            "Pump.fun brûle la LP initiale et la migre vers Raydium (≈ 12k$)",
            "Renfort chirurgical de la LP pour stabiliser le prix cible ≈ 0,0005€",
            "Apport externe (2–4k€) + ventes contrôlées du trésor annoncées à l'avance",
            "Audit sécurité publié + vérification on-chain ouverte à tous",
          ],
        },
        {
          phase: "Raydium → ∞",
          title: "Discipline Anti-Dump",
          bullets: [
            "Multisig + timelock sur le trésor",
            "Plafond hebdomadaire de vente du trésor affiché publiquement",
            "Ventes découpées en petits blocs, annoncées 48h à l'avance",
            "Zéro airdrop massif sync autour des renforts de LP",
          ],
        },
      ],
      proofTitle: "Pourquoi c'est du sérieux assumé",
      proof:
        "0% Tax signifie un coffre qui se remplit uniquement par la croissance. Chaque action du trésor est annoncée avant exécution, la communauté vérifie on-chain, et le Prophète se moque pendant ce temps. Les règles tiennent — même quand le narratif est cynique.",
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
          title: "The Bonding Curve Trial — Lancement Pump.fun",
          bullets: [
            "Mint 1B tokens sur Pump.fun · 0% Tax Protocol",
            "Le Prophète teste la foi de ses disciples sur la Bonding Curve",
            "Objectif : atteindre 100% de la courbe (≈ 60k$ MC)",
          ],
        },
        {
          tag: "Phase 02",
          title: "Raydium Ascension — Migration automatique",
          bullets: [
            "LP automatiquement brûlée et migrée vers Raydium par Pump.fun",
            "Renforcement stratégique de la LP pour stabiliser le prix cible ≈ 0,0005€",
            "Tokens équipe lockés publiquement via Streamflow (vesting 12m + cliff 3m)",
          ],
        },
        {
          tag: "Phase 03",
          title: "PROTOCOL ΔΣ · premières molettes",
          bullets: [
            "Premières molettes verrouillées au fil des achats",
            "Allocations Trésor vers préparation du projet MiCA-compliant",
            "Transmissions prophétiques intensifiées (X + Telegram)",
          ],
        },
        {
          tag: "Phase 04",
          title: "Déclassification",
          bullets: [
            "Six molettes verrouillées · Coffre ouvert",
            "Audit sécurité publié",
            "La Black Op est révélée — transition vers la phase MiCA",
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
          q: "Pourquoi 0% de taxe ? Comment financer le Trésor alors ?",
          a: "Pump.fun interdit les taxes sur les tokens SPL standard — et c'est mieux pour la vélocité. Le Trésor de 30% est scellé en multisig et financé par sa propre valorisation. Chaque vente du Trésor est planifiée, plafonnée et annoncée avant exécution.",
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
          a: "Un memecoin n'est pas un titre financier. Nous adoptons la philosophie MiCA : transparence de l'information sur la structure (tokenomics, allocation, gouvernance), affectation claire des fonds (Coffre), aucune promesse de rendement, disclaimer explicite.",
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
      requestClearance: "Request a clearance level",
      alreadyHaveCode: "I already have an accreditation number",
    },

    terminal: {
      deniedLines: [
        "> VERIFYING CREDENTIALS…",
        "> clearance_level = 01 (WHITELISTED)",
        "> target_resource = PROTOCOL_ΔΣ · TRUE_VAULT",
        "> required_clearance = LEVEL_02",
        "",
        "[ACCESS DENIED]",
        "",
        "Nice try, citizen. The vault you thought you cracked was only a narrative decoy — Level 01 only grants you the public declassified version.",
        "",
        "The REAL vault — the one holding the actual $DEEPOTUS activity stream — requires LEVEL 02 clearance.",
        "",
        "Good news: the Deep State is bureaucratic. Ask for your card. They'll send it.",
      ],
      ctaRequest: "Request Level 02 clearance",
      ctaRetreat: "Withdraw request (go back)",
      formIntro:
        "Identify yourself. The Deep State will file your record and deliver a personal access card with a unique accreditation number.",
      emailLabel: "Contact email",
      emailPlaceholder: "you@email.com",
      nameLabel: "Agent name (optional)",
      namePlaceholder: "AGENT OMEGA-042",
      emailInvalid: "Invalid email. Try again.",
      submit: "Transmit request",
      back: "Back",
      successTitle: "TRANSMISSION RECEIVED. RECORD ARCHIVED.",
      successInbox:
        "Your access card is en route to __EMAIL__ — usual delay: a few seconds.",
      successNext: "Next step — open the real vault",
      openVault: "Open the real vault",
      close: "Close terminal",
      retry: "Retry",
    },

    classifiedVault: {
      gateKicker: "Restricted · LEVEL 02",
      gateTitle: "The real vault.",
      gateSubtitle:
        "Enter your Level 02 accreditation number. It was emailed to you on your Deep State access card.",
      gateLabel: "Accreditation number",
      gateError: "Invalid or expired accreditation.",
      gateHint:
        "Don't have a number yet? Head back to the home page, open the terminal from the vault section and request your Level 02 accreditation.",
      gateHintShort: "Type directly onto the door display ↑",
      gateChannel: "SECURE CHANNEL",
      gateLevel: "LEVEL 02 · PROTOCOL ΔΣ",
      gateIdle: "IDLE",
      gateBack: "Back to site",
      verify: "Verify access",
      verifying: "Verifying…",
      authedKicker: "CLEARANCE GRANTED · LEVEL 02",
      authedTitle: "Welcome to the real $DEEPOTUS vault.",
      authedSubtitle:
        "What you see here is the live on-chain activity stream of the token. No staging. No filter. The combination literally advances with every purchase.",
      liveCombination: "Live combination",
      dials: "dials",
      progress: "progress",
      tokens: "tokens moved",
      microTicks: "micro-rotations",
      treasury: "Treasury (€)",
      mode: "source",
      disclaimer:
        "Warning: the vault evolves based on real on-chain activity (DexScreener). No yield promised. This token is satirical and highly speculative.",
      feedTitle: "Live activity feed",
      externalTitle: "Verify on-chain",
      sessionUntil: "Session until",
      logout: "Logout",
      declassified: {
        kicker: "PROTOCOL ΔΣ · DECLASSIFIED",
        title: "The vault is open. The confession is live.",
        subtitle:
          "The Prophet panics, the crowd rises. Access the full revelation and the GENCOIN launch.",
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
      kicker: "— ALLOCATION & DISCIPLINE",
      title: "Tokenomics · 0% Tax Protocol",
      subtitle: "Fixed supply — 1,000,000,000 tokens · Launched on Pump.fun",
      categories: {
        treasury: {
          name: "Operational Treasury (PROTOCOL ΔΣ)",
          detail: "War reserve for the future MiCA-compliant project. Public multisig. Funded by its OWN valuation — never by your swaps.",
        },
        liquidity: {
          name: "Liquidity & Raydium Ascension",
          detail: "Launched on Pump.fun. Surgical migration to Raydium as soon as the Bonding Curve completes. LP reinforcement stabilizes the ≈€0.0005 target price.",
        },
        marketing: {
          name: "Traction & X/TG Operations",
          detail: "Propaganda and acquisition. A silent prophet is useless in this market.",
        },
        airdrops: {
          name: "Community & Airdrops",
          detail: "For active agents. Targeted, locked distributions rewarding loyalty, not the dump.",
        },
        ai_lore: {
          name: "AI Reserve & Lore",
          detail: "Keeps the simulation servers running and fuels the daily prophecies.",
        },
        team: {
          name: "Team & Prophet",
          detail: "12-month linear vesting + 3-month cliff. Public lock via Streamflow.",
        },
      },
      totalLabel: "Total supply",
      taxTitle: "0% TAX PROTOCOL",
      taxBadge: "Maximum velocity",
      taxIntro: "The Deep State eliminated useless friction. $DEEPOTUS runs a 0% tax structure on buy and sell. No hidden fees, no on-chain bureaucracy.",
      taxCap: "PROTOCOL ΔΣ funding comes from the Treasury's own valuation (30%) — multisig-sealed, sales scheduled and pre-announced.",
      cynicalTitle: "Cynical Transparency",
      cynicalBody: "No tax means we rely solely on the token's growth to fund PROTOCOL ΔΣ. If the price rises, the vault fills. If the vault fills, the truth breaks. That's the only metric that matters.",
    },

    transparency: {
      kicker: "— ON-CHAIN TRANSPARENCY",
      title: "Pump.fun Launch & Treasury Discipline",
      subtitle:
        "From D0 to Raydium Ascension. Every step is published before execution.",
      timeline: [
        {
          phase: "D0",
          title: "Pump.fun Launch · 0% Tax",
          bullets: [
            "Mint 1,000,000,000 $DEEPOTUS · Pump.fun SPL standard",
            "Moderate founder dev-buy for credibility (announced on-chain)",
            "Team tokens immediately locked via Streamflow (12-month vesting + 3-month cliff)",
            "Treasury (30%) sealed in public multisig",
          ],
        },
        {
          phase: "Bonding Curve",
          title: "Climbing the Pump.fun curve",
          bullets: [
            "Price set by the bonding curve — no swap tax",
            "Target: complete 100% of the curve (≈ $60k MC)",
            "Vault dials start locking as buys accumulate",
            "Zero treasury selling until migration is complete",
          ],
        },
        {
          phase: "Raydium Ascension",
          title: "Automatic migration to Raydium",
          bullets: [
            "Pump.fun burns the initial LP and migrates to Raydium (≈ $12k)",
            "Surgical LP reinforcement to stabilize target price ≈ €0.0005",
            "External top-up (€2–4k) + controlled treasury sales pre-announced",
            "Security audit published + on-chain verification open to everyone",
          ],
        },
        {
          phase: "Raydium → ∞",
          title: "Anti-Dump Discipline",
          bullets: [
            "Multisig + timelock on the treasury",
            "Weekly treasury-sale cap publicly posted",
            "Sales broken into small blocks, pre-announced 48h ahead",
            "No mass airdrop synced with LP reinforcements",
          ],
        },
      ],
      proofTitle: "Why this is genuinely serious",
      proof:
        "0% Tax means a vault that fills only through growth. Every treasury action is announced before execution, the community verifies on-chain, and the Prophet mocks everyone in the meantime. The rules hold — even when the narrative is cynical.",
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
      title: "The AI Candidate Campaign",
      phases: [
        {
          tag: "Phase 01",
          title: "The Bonding Curve Trial — Pump.fun Launch",
          bullets: [
            "Mint 1B tokens on Pump.fun · 0% Tax Protocol",
            "The Prophet tests his disciples' faith on the Bonding Curve",
            "Target: complete 100% of the curve (≈ $60k MC)",
          ],
        },
        {
          tag: "Phase 02",
          title: "Raydium Ascension — Automatic Migration",
          bullets: [
            "LP auto-burned and migrated to Raydium by Pump.fun",
            "Strategic LP reinforcement to stabilize target price ≈ €0.0005",
            "Team tokens publicly locked via Streamflow (12-month vesting + 3-month cliff)",
          ],
        },
        {
          tag: "Phase 03",
          title: "PROTOCOL ΔΣ · first dials",
          bullets: [
            "First dials lock as buys accumulate",
            "Treasury allocations towards MiCA-compliant project prep",
            "Prophetic transmissions intensified (X + Telegram)",
          ],
        },
        {
          tag: "Phase 04",
          title: "Declassification",
          bullets: [
            "Six dials locked · Vault open",
            "Security audit published",
            "The Black Op is revealed — transition to MiCA phase",
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
          q: "Why 0% tax? How is the Treasury funded then?",
          a: "Pump.fun forbids transaction taxes on standard SPL tokens — and honestly it's better for velocity. The 30% Treasury is multisig-sealed and funded by its OWN valuation. Every Treasury sale is scheduled, capped and pre-announced.",
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
          a: "A memecoin is not a security. We adopt MiCA philosophy: information transparency on structure (tokenomics, allocation, governance), clear fund allocation (Vault), no yield promise, explicit disclaimer.",
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
