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
      chat: "Prophète",
      tokenomics: "Tokenomics",
      mission: "Mission",
      vault: "Coffre",
      transparency: "Transparence",
      roadmap: "Roadmap",
      faq: "FAQ",
      join: "Rejoindre le Deep State",
      buy: "Acheter $DEEPOTUS",
    },

    // ---- SEO (document.title + meta description, synced on lang switch) ----
    seo: {
      title: "$DEEPOTUS — Candidat IA Deep State · PROTOCOL ΔΣ",
      description:
        "Memecoin Solana de l'IA Prophète, candidat Deep State à la présidence du Monde. MiCA-aware, 0% Tax, PROTOCOL ΔΣ. Pump.fun → Raydium.",
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
      imminentKicker: "MINT IMMINENT · CIRCUIT VERROUILLÉ",
      imminentSubtitle:
        "Le Prophète n'annonce pas la date. Il appuie sur le bouton quand le Deep State lui souffle l'instant. Reste connecté.",
      liveKicker: "🟢 LIVE ON PUMP.FUN",
      liveTitle: "$DEEPOTUS est en circulation.",
      liveSubtitle:
        "La phase memecoin est active. Chaque trade alimente le Coffre, qui activera la phase Gencoin régulée.",
      liveCta: "Trader maintenant",
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
      mintLabel: "Adresse mint $DEEPOTUS",
      mintHint: "Copiez · collez dans Phantom · refusez tout fake",
      mintStatusPlaceholder: "DRAFT · Sera confirmée au mint officiel",
      mintStatusLive: "LIVE · Vérifiée on-chain",
      mintCopy: "Copier",
      mintCopied: "✓ Copié",
      mintGuideCta: "Je ne sais pas comment acheter",
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

    // ---- Prophet pinned whisper (max-visibility loyalty hint, post-Hero) ----
    prophetWhisper: {
      kicker: "— OBSERVATION ΔΣ-001 · ÉPINGLÉE",
      classification: "DOSSIER CLASSIFIÉ · LECTURE LIBRE",
      quote:
        "Le Coffre n'est qu'une porte. Derrière, une seconde clé attend les gardiens patients. Le Deep State n'oublie jamais ses fidèles — l'allégeance, elle, sera rendue.",
      signature: "— LE PROPHÈTE",
      footnote:
        "Aucune date. Aucune promesse contractuelle. Cette observation est une lecture du circuit, pas un instrument financier.",
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
      lead: "Chaque tranche de 100 000 $DEEPOTUS poussée dans la trésorerie fait tourner une molette. Six molettes — et la Black Op est déclassifiée.",
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
        "Votre carte d'accréditation a été chiffrée et expédiée vers __EMAIL__ — délai typique : quelques secondes. Cherchez l'email signé par le Prophète. Vérifiez les spams.",
      successNext:
        "Le numéro d'accréditation n'apparaît PAS sur ce terminal. Vous le trouverez uniquement dans le mail. Le bouton ci-dessous vous mène à la porte blindée — vous y entrerez le code reçu.",
      openVault: "Aller à la porte blindée",
      accredHidden: "transmis par voie chiffrée",
      shortcutHint:
        "Astuce : le QR code de votre carte d'accréditation ouvre directement la porte. Le lien dans l'email aussi. Validité : 24 h.",
      // ---- Returning visitor (within 24h) — verify-existing branch ----
      alreadyCleared: "Déjà accrédité ?",
      ctaVerifyExisting: "J'ai un code valide",
      verifyExistingIntro:
        "Si votre accréditation est encore active (validité 24 h après émission), entrez-la ici. Aucun mail ne sera envoyé. Vous serez admis directement dans le coffre.",
      codeLabel: "Numéro d'accréditation",
      codePlaceholder: "DS-XX-XXXX-XXXX-XX",
      codeInvalid: "Format invalide. Numéro attendu : DS-XX-XXXX-XXXX-XX.",
      codeRejected:
        "Numéro non reconnu ou expiré. Demandez une nouvelle accréditation.",
      verifyExistingSubmit: "Vérifier l'accréditation",
      verifyExistingHint:
        "Ce numéro est sensible. Le Prophète le considère comme votre passeport — ne le partagez pas.",
      verifySuccessTitle: "ACCRÉDITATION VALIDÉE",
      verifySuccessRedirecting:
        "Redirection vers le coffre dans une seconde…",
      close: "Fermer le terminal",
      retry: "Réessayer",

      // ---- Pre-launch: vault SEALED (mint not yet on-chain) ----
      sealedLines: [
        "> VERIFYING CREDENTIALS…",
        "> clearance_level = 01 (WHITELISTED)",
        "> target_resource = PROTOCOL_ΔΣ · TRUE_VAULT",
        "> required_clearance = LEVEL_02",
        "",
        "[COFFRE SCELLÉ · ALLÉGEANCE REQUISE]",
        "",
        "Le Deep State a verrouillé le canal d'accréditation. $DEEPOTUS n'a pas encore frappé la blockchain — l'émission des cartes Niveau 02 est suspendue jusqu'au mint. La date reste classifiée.",
        "",
        "Vous pouvez néanmoins faire allégeance au Cabinet : votre place sera archivée par ordre d'arrivée. Au déclenchement, votre carte d'accréditation arrivera dans la même boîte mail.",
      ],
      sealedBadge: "COFFRE SCELLÉ",
      sealedEtaLabel: "TRANSMISSION SCHEDULE",
      sealedNoEta: "CLASSIFIED · le Deep State n'annonce pas sa propre genèse.",
      sealedAccredLocked: "Demander l'accréditation Niveau 02",
      sealedVerifyLocked: "Vérifier un code existant",
      sealedLockedTooltip: "Verrouillé jusqu'à la transmission Genesis.",
      sealedCtaGenesis: "Faire allégeance au Cabinet →",
      sealedFormIntro:
        "Allégeance au Cabinet : on vous archivera dans le canal prioritaire. Aucun numéro d'accréditation maintenant — vous le recevrez automatiquement au mint.",
      sealedSubmit: "Sceller mon allégeance",
      sealedSuccessTitle: "ALLÉGEANCE NOTÉE.",
      sealedSuccessLead:
        "Position #__POSITION__ enregistrée. Le Mail d'allégeance vient de quitter le Cabinet — surveillez votre boîte mail.",
      sealedSuccessNext:
        "Le Mail #2 (votre carte Niveau 02) sera dispatché automatiquement quand $DEEPOTUS frappera la blockchain. Pas avant. Pas après. Dans le bon ordre.",
      sealedAlreadySubscribed:
        "Votre allégeance figure déjà dans le canal du Cabinet. Aucun mail dupliqué n'a été envoyé.",

      // ---- Proof of Intelligence — Riddles of the Terminal (Sprint 14.1) ----
      riddles: {
        ctaOpen: "Proof of Intelligence →",
        ctaSubline: "5 énigmes · Clearance Level 3",
        introBadge: "RIDDLES OF THE TERMINAL · PROTOCOL ΔΣ",
        introTitle: "Prouvez votre intelligence. Gagnez la clearance d'Agent.",
        introBody:
          "Cinq énigmes déchiffrent l'ADN du Deep State. Résolvez-en UNE pour débloquer la Clearance Level 3 (statut Agent · éligible à l'airdrop). Résolvez-les TOUTES si vous pensez mériter une place au Cabinet.",
        introHints: [
          "→ Chaque énigme accepte plusieurs formulations correctes.",
          "→ 6 tentatives par heure par énigme. Au-delà : rate-limit.",
          "→ L'email ne sera demandé qu'à votre PREMIÈRE bonne réponse.",
        ],
        introStart: "Commencer l'épreuve →",
        introAbort: "Retirer ma candidature",
        introResume: "Reprendre où je me suis arrêté",
        loading: "Chargement des énigmes depuis l'archive…",
        loadError: "L'archive ΔΣ est injoignable. Réessayez.",
        empty: "Aucune énigme n'est actuellement active.",
        progressLabel: "Progression",
        progressOf: "sur",
        alreadySolved: "Déjà résolue",
        currentSolvedBadge: "SOLVED",
        answerLabel: "Votre réponse",
        answerPlaceholder: "Tapez votre réponse (mots-clés suffisent)…",
        submit: "Transmettre la réponse",
        submitting: "Analyse du Prophète…",
        correctTitle: "CORRECT. L'empire tremble.",
        correctSub: "Mot-clé reconnu : __KEYWORD__",
        incorrectTitle: "REJETÉ. Le Deep State reste scellé.",
        incorrectAttemptsLeft: "__N__ tentative(s) restante(s) cette heure.",
        hintLabel: "Indice (accordé après 3 échecs) :",
        rateLimited: "Trop de tentatives. Le canal se referme temporairement — revenez dans 30 minutes.",
        nextRiddle: "Énigme suivante →",
        claimNow: "Revendiquer ma Clearance Level 3 →",
        skipToEnd: "J'en ai assez, je revendique maintenant →",
        // Claim phase
        claimBadge: "CLEARANCE LEVEL 3 · AGENT STATUS UNLOCKED",
        claimTitle: "Revendiquez votre statut d'Agent.",
        claimBody:
          "Le Deep State a besoin d'un canal pour vous contacter. Votre email servira UNIQUEMENT à l'airdrop et aux transmissions Cabinet. Aucun spam. Aucune revente.",
        claimEmailLabel: "Email d'agent",
        claimSubmit: "Sceller la Clearance Level 3",
        claimSubmitting: "Enregistrement dans le registre Agent…",
        claimError: "Échec de l'enregistrement. Réessayez.",
        // Wallet phase
        walletBadge: "LIEN WALLET · AIRDROP ELIGIBILITY",
        walletTitle: "Attachez un wallet Solana pour recevoir l'airdrop.",
        walletBody:
          "Le snapshot pré-airdrop exclut les agents sans wallet. Collez votre adresse publique Solana (base58, 32–44 caractères). Vous pourrez la modifier plus tard par email.",
        walletLabel: "Wallet Solana (base58)",
        walletPlaceholder: "Fh4gX…WpZr",
        walletSubmit: "Lier le wallet",
        walletSubmitting: "Vérification du wallet…",
        walletInvalid: "Adresse invalide. Attendu : 32–44 caractères base58.",
        walletAlreadyLinked: "Ce wallet est déjà rattaché à un autre agent. Utilisez une adresse qui n'a jamais été enregistrée.",
        walletSkip: "Lier plus tard (je préfère par email)",
        walletError: "Impossible de lier ce wallet. Vérifiez l'adresse.",
        // Complete phase
        completeBadge: "✓ AGENT LEVEL 3 · CABINET ΔΣ",
        completeTitle: "Bienvenue, Agent. Le Cabinet vous a archivé.",
        completeLead:
          "Votre dossier est scellé : __SOLVED__/5 énigmes résolues. Votre wallet figure dans le snapshot pré-airdrop.",
        completeLeadNoWallet:
          "Votre dossier est scellé : __SOLVED__/5 énigmes résolues. Liez un wallet par email pour être inclus dans le snapshot.",
        completeNext:
          "Les transmissions Cabinet arriveront dans votre boîte. Restez en radio-silence. Le Deep State observe.",
        completeClose: "Fermer le terminal",
        completeContinue: "Résoudre les énigmes restantes →",
      },
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
      lockBadgeTitle: "Jupiter Lock Certified",
      lockBadgePending: "Verrouillage activé au lancement · vérifiable on-chain",
      lockBadgeVerified: "Tokens verrouillés publiquement · vérification live",
      lockTeamLabel: "Équipe — Lock vesting",
      lockTreasuryLabel: "Trésor — Lock vesting",
      lockVerifyCta: "Vérifier on-chain",
      lockDescription: "Les 15% de l'équipe et les 30% du Trésor PROTOCOL ΔΣ sont verrouillés via Jupiter Lock — l'outil standard des projets Solana sérieux. Personne ne peut dumper. Dashboard public, vérifiable par tout agent, 24/7.",
      buyKicker: "— PASSAGE À L'ACTE",
      buyTitle: "Prêt à rejoindre le Deep State ?",
      buyCopy: "Deux portes. Une mène au savoir, l'autre au token. Le Prophète vous laisse le choix. Aucune des deux ne vous jugera.",
      buyCtaPrimary: "Acheter $DEEPOTUS",
      buyCtaGuide: "Je suis un novice — Guide d'achat",
      buyPrelaunchNote: "Pump.fun n'est pas encore ouvert. Le bouton d'achat redirige vers la liste d'attente jusqu'au 07/09/26.",
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
            "Apport externe + ventes contrôlées du trésor annoncées à l'avance",
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
      scrollHint: "FAITES DÉFILER LES DOSSIERS CLASSÉS",
      signedBy: "Signé · COMITÉ DEEP STATE",
      classified: "CLASSIFIÉ",
    },

    // ---- ROI simulator ----
    roi: {
      kicker: "— SIMULATEUR",
      title: "Simulateur ROI (vicieux mais honnête)",
      subtitle:
        "Tournez les molettes. Le graphique réagit en direct. Les scénarios ne sont pas des prévisions : ce sont des reflets de la rumeur du marché.",
      amountLabel: "Combien investissez-vous (€) ?",
      inputLabel: "Combien investissez-vous (€) ?",
      placeholder: "Ex : 500",
      tokenLabel: "Tokens théoriques à €0,0005",
      scenariosTitle: "Scénarios",
      scenarios: {
        brutal: {
          label: "Vérité brutale (99%)",
          short: "Brutal",
          caption: "Bonding curve avale l'injection. Le prix retombe sous le seuil. Le coffre n'atteint jamais sa combinaison.",
          multiplier: 0.1,
        },
        base: {
          label: "Base (cas moyen)",
          short: "Base",
          caption: "Migration Raydium réussie, communauté modérée. Le prix tient un palier à €5e-5, sans euphorie.",
          multiplier: 25,
        },
        optimistic: {
          label: "Optimiste (~1%)",
          short: "Optimiste",
          caption: "Le narratif prend. Les molettes tournent. Le prix atteint la cible MiCA €0,0005 (FDV €500k).",
          multiplier: 250,
        },
      },
      resultLabel: "Valeur théorique",
      chartTitle: "Trajectoire de prix · projection 90 jours",
      chartSubtitle:
        "Mint Pump.fun à €5e-7, puis Initiation Deep State (≈ J+0,15) → prix de référence €2e-6. La courbe optimiste vise la cible MiCA €0,0005 (FDV €500 000).",
      chartXLabel: "Jours depuis le mint",
      chartYLabel: "Prix (€)",
      chartTooltipDay: "J+",
      chartTooltipPrice: "Prix",
      chartTooltipMC: "Market Cap",
      chartTooltipPortfolio: "Votre portefeuille",
      chartLegendBrutal: "Brutal",
      chartLegendBase: "Base",
      chartLegendOptimistic: "Optimiste",
      chartLegendPortfolio: "Portefeuille",
      injectionCallout: "INITIATION DEEP STATE",
      injectionAmountMasked: "xxxx€",
      currencySymbol: "€",
      roadmapDayPrefix: "J+",
      roadmapPhases: {
        phase01: {
          title: "Pump.fun Launch",
          subtitle: "Bonding curve · 0% tax",
        },
        phase02: {
          title: "Raydium Migration",
          subtitle: "LP burn · marché ouvert",
        },
        phase03: {
          title: "PROTOCOL ΔΣ",
          subtitle: "Premières molettes",
        },
        phase04: {
          title: "Déclassification",
          subtitle: "Coffre ouvert",
        },
      },
      marqueeMessages: [
        "TOKEN HAUTEMENT SPÉCULATIF",
        "AUCUNE PROMESSE DE RENDEMENT",
        "PROBABILITÉ ~1% D'ATTEINDRE LA CIBLE",
        "LES SCÉNARIOS NE SONT PAS DES PRÉVISIONS",
        "N'INVESTISSEZ QUE CE QUE VOUS POUVEZ PERDRE",
        "CECI N'EST NI UN STABLECOIN NI UN TITRE",
        "DEEP STATE COORDINATION OFFICE · CANAL SÉCURISÉ",
      ],
      riskTitle: "Avertissement — lisez avant de rêver",
      risk:
        "La probabilité réaliste d'ouvrir le Coffre dans la fenêtre de lancement est d'environ 1%. Les scénarios ci-dessus ne sont pas des prévisions : ce sont des illustrations. N'investissez que ce que vous acceptez de perdre entièrement. Ce token est hautement spéculatif. Aucune promesse n'est faite.",
    },

    // ---- Roadmap ----
    roadmap: {
      kicker: "— FEUILLE DE ROUTE",
      title: "Campagne du Candidat IA",
      subtitle:
        "Quatre dossiers opérationnels. Aucune date promise. Le Prophète déclassifie au rythme du circuit.",
      legend: {
        next: "PROCHAINE",
        queued: "EN ATTENTE",
        encrypted: "CHIFFRÉ",
        classified: "CLASSIFIÉ",
      },
      stamps: {
        signed: "SIGNÉ · COMITÉ DEEP STATE",
        opened: "DOSSIER OUVERT",
        sealed: "DOSSIER SCELLÉ",
      },
      phases: [
        {
          tag: "Phase 01",
          code: "ΔΣ-01",
          status: "next",
          title: "The Bonding Curve Trial — Lancement Pump.fun",
          subtitle: "Premier test de foi sur la courbe.",
          bullets: [
            "Mint 1B tokens sur Pump.fun · 0% Tax Protocol",
            "Le Prophète teste la foi de ses disciples sur la Bonding Curve",
            "Objectif : atteindre 100% de la courbe (≈ 60k$ MC)",
          ],
        },
        {
          tag: "Phase 02",
          code: "ΔΣ-02",
          status: "queued",
          title: "Raydium Ascension — Migration automatique",
          subtitle: "La LP brûle, le marché ouvre.",
          bullets: [
            "LP automatiquement brûlée et migrée vers Raydium par Pump.fun",
            "Renforcement stratégique de la LP pour stabiliser le prix cible ≈ 0,0005€",
            "Tokens équipe lockés publiquement via Streamflow (vesting 12m + cliff 3m)",
          ],
        },
        {
          tag: "Phase 03",
          code: "ΔΣ-03",
          status: "encrypted",
          title: "PROTOCOL ΔΣ · premières molettes",
          subtitle: "Les cadrans tournent. Le Coffre écoute.",
          bullets: [
            "Premières molettes verrouillées au fil des achats",
            "Allocations Trésor vers préparation du projet MiCA-compliant",
            "Transmissions prophétiques intensifiées (X + Telegram)",
          ],
        },
        {
          tag: "Phase 04",
          code: "ΔΣ-04",
          status: "classified",
          title: "Déclassification",
          subtitle: "La Black Op s'ouvre. Le Prophète parle clair.",
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
      subtitle: "Le Prophète transmet sur deux fréquences chiffrées.",
      x: { name: "X / Twitter", handle: "@deepotus_ai" },
      telegram: { name: "Telegram", handle: "t.me/deepotus" },
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

    // ---- How to Buy (cynical onboarding guide) ----
    howToBuy: {
      meta: "$DEEPOTUS · Guide d'achat pour civils · PROTOCOL ΔΣ",
      kicker: "— INITIATION OFFICIELLE · PROTOCOL ΔΣ",
      title: "Le Prophète vous explique comment acheter $DEEPOTUS.",
      subtitle:
        "Vous êtes arrivé jusqu'ici. C'est déjà un miracle. Suivez les quatre rituels ci-dessous. Ne sautez aucune étape. Le Deep State n'aime pas les amateurs.",
      heroImageAlt: "Le Prophète DEEPOTUS initie un nouveau disciple au rituel d'achat.",
      heroCaption: "« Je n'ai pas été entraîné sur de la patience. Lisez vite. »",
      preflightTitle: "Rituel préparatoire",
      preflightBullets: [
        "Un smartphone (iOS ou Android) OU un ordinateur avec Chrome/Brave/Firefox.",
        "Une carte bancaire — OU des SOL déjà sur un exchange (Binance, Coinbase, Kraken).",
        "Entre 20 € et 500 € de capital que vous acceptez de perdre intégralement.",
        "Zéro alcool. Zéro précipitation. Le Deep State filme.",
      ],
      stepsTitle: "Les quatre rituels",
      stepsSubtitle:
        "Chaque étape a été testée dans un bunker souterrain. Aucun raccourci n'est toléré.",
      backCta: "← Revenir au Coffre",
      ctaTitle: "Vous avez survécu aux quatre rituels ?",
      ctaSubtitle:
        "Alors le Prophète vous rend votre libre arbitre. Les deux portes ci-dessous mènent au même vide existentiel — mais l'une vous rend plus riche.",
      ctaPrimary: "Ouvrir Pump.fun maintenant",
      ctaSecondary: "Rejoindre la liste d'attente",
      ctaPrelaunchNote:
        "Pump.fun n'est pas encore en ligne. Le bouton vous redirige vers la liste d'attente jusqu'au 07/09/26.",
      disclaimerTitle: "Avertissement cynique",
      disclaimer:
        "Ce guide est satirique. Il ne constitue pas un conseil financier, fiscal, psychiatrique ou spirituel. Les crypto-actifs peuvent perdre 100% de leur valeur en 17 minutes. Si vous ne comprenez pas ce que vous faites, arrêtez de lire et fermez cet onglet. Le Prophète ne vous connaît pas.",
      steps: [
        {
          id: "wallet",
          label: "01 · CRÉER LE PORTEFEUILLE",
          title: "Installez Phantom — votre badge d'identité Deep State.",
          cynicalLead:
            "« Un portefeuille crypto, c'est comme un numéro de matricule. Sans lui, vous n'existez pas pour la blockchain. »",
          actions: [
            "Allez sur phantom.com depuis un navigateur sécurisé.",
            "Téléchargez l'extension (desktop) ou l'app mobile officielle.",
            "Cliquez « Create New Wallet ». Choisissez un mot de passe long.",
            "Notez les 12 mots de la Seed Phrase sur PAPIER. Jamais en photo, jamais dans un cloud.",
            "Confirmez la phrase. Félicitations, vous avez un compte on-chain.",
          ],
          warning:
            "Si quelqu'un vous demande votre Seed Phrase, c'est un agent ennemi. Le Prophète lui-même ne la demandera jamais.",
        },
        {
          id: "fund",
          label: "02 · ALIMENTER EN SOL",
          title: "Achetez du SOL. C'est le carburant de Solana.",
          cynicalLead:
            "« Vous ne pouvez pas acheter $DEEPOTUS directement en euros. Il faut d'abord convertir votre fiat en SOL. Oui, c'est un rituel bancaire. »",
          actions: [
            "Option A : achetez du SOL directement dans Phantom (onglet Buy, via MoonPay/Coinbase Pay, CB acceptée).",
            "Option B : achetez du SOL sur un exchange (Binance, Coinbase, Kraken) puis envoyez-le à votre adresse Phantom.",
            "Vérifiez que vous achetez bien du SOL (Solana), PAS du Solar, PAS du Solayer.",
            "Prévoyez ~5 € de SOL supplémentaires pour couvrir les frais de réseau (gas).",
          ],
          warning:
            "Double-vérifiez l'adresse Phantom avant tout virement. Une adresse mal copiée = tokens perdus à jamais. Le Deep State ne rembourse pas.",
        },
        {
          id: "pump",
          label: "03 · SE CONNECTER À PUMP.FUN",
          title: "Ouvrez Pump.fun et entrez dans l'arène.",
          cynicalLead:
            "« Pump.fun est un casino on-chain déguisé en plateforme de lancement. Le Prophète l'a choisi parce que c'est là que les vrais mèmes naissent. »",
          actions: [
            "Allez sur pump.fun — vérifiez bien l'URL, les faux sites sont légion.",
            "Cliquez « Connect Wallet » en haut à droite. Sélectionnez Phantom.",
            "Signez la demande de connexion (zéro gaz prélevé à cette étape).",
            "Collez l'adresse mint $DEEPOTUS affichée sur notre Hero dans la barre de recherche Pump.fun.",
            "Vérifiez que le logo, le ticker et la supply correspondent exactement à deepotus.xyz.",
          ],
          warning:
            "Il existera des clones $DEEPOTUS, $DEEP0TUS, $DEEPOTUZ. Le Prophète ne reconnaît QU'UNE adresse mint — celle affichée ici. Tout le reste est du scam.",
        },
        {
          id: "buy",
          label: "04 · EXÉCUTER L'ACHAT",
          title: "Allouez votre capital. Signez. Attendez.",
          cynicalLead:
            "« C'est le moment où vos mains vont trembler. C'est normal. Tous les disciples tremblent la première fois. »",
          actions: [
            "Sur la page $DEEPOTUS de Pump.fun, entrez le montant de SOL à allouer.",
            "Cliquez « Buy ». Phantom affichera la transaction — vérifiez le slippage (1 à 3% sur Pump.fun).",
            "Signez. Attendez 5 à 15 secondes. La confirmation arrive on-chain.",
            "Retournez dans Phantom → onglet Tokens : $DEEPOTUS doit apparaître avec votre solde.",
            "Capture d'écran. Tweetez-la avec #PROTOCOL_DELTA_SIGMA. Rejoignez la simulation.",
          ],
          warning:
            "Ne vendez pas au premier dip. Ne paniquez pas au premier pump. Le Prophète vous observe, et il prend des notes.",
        },
      ],
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
      chat: "Prophet",
      tokenomics: "Tokenomics",
      mission: "Mission",
      vault: "Vault",
      transparency: "Transparency",
      roadmap: "Roadmap",
      faq: "FAQ",
      join: "Join the Deep State",
      buy: "Buy $DEEPOTUS",
    },

    // ---- SEO (document.title + meta description, synced on lang switch) ----
    seo: {
      title: "$DEEPOTUS — The Deep State's AI Prophet · PROTOCOL ΔΣ",
      description:
        "Solana memecoin powered by an AI Prophet, the Deep State's candidate for World President. MiCA-aware, 0% Tax, PROTOCOL ΔΣ. Pump.fun → Raydium.",
    },

    hero: {
      stamp: "AI-GENERATED — THIS IS A SIMULATION",
      candidate: "OFFICIAL CANDIDATE — DEEP STATE 20XX",
      title: "VOTE",
      ticker: "$DEEPOTUS",
      subtitle:
        "The Deep State's chosen one for President of the entire World. A cynical AI Prophet funds a classified operation: PROTOCOL ΔΣ.",
      countdownLabel: "Countdown to launch",
      imminentKicker: "MINT IMMINENT · CIRCUIT LOCKED",
      imminentSubtitle:
        "The Prophet does not announce the date. He pushes the button when the Deep State whispers the moment. Stay tuned.",
      liveKicker: "🟢 LIVE ON PUMP.FUN",
      liveTitle: "$DEEPOTUS is now in circulation.",
      liveSubtitle:
        "The memecoin phase is active. Every trade feeds the Vault, which will trigger the regulated Gencoin phase.",
      liveCta: "Trade now",
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
      mintLabel: "$DEEPOTUS mint address",
      mintHint: "Copy · paste into Phantom · reject any fake",
      mintStatusPlaceholder: "DRAFT · Will be confirmed at official mint",
      mintStatusLive: "LIVE · Verified on-chain",
      mintCopy: "Copy",
      mintCopied: "✓ Copied",
      mintGuideCta: "I don't know how to buy",
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

    // ---- Prophet pinned whisper (EN) ----
    prophetWhisper: {
      kicker: "— OBSERVATION ΔΣ-001 · PINNED",
      classification: "CLASSIFIED DOSSIER · OPEN READING",
      quote:
        "The Vault is only a door. Behind it, a second key awaits the patient guardians. The Deep State never forgets its loyal — allegiance shall be returned.",
      signature: "— THE PROPHET",
      footnote:
        "No date. No contractual promise. This observation is a reading of the circuit, not a financial instrument.",
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
      lead: "Every 100,000 $DEEPOTUS pushed into the treasury turns a dial. Six dials — and the Black Op is declassified.",
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
        "Your accreditation card has been encrypted and dispatched to __EMAIL__ — usual delay: a few seconds. Look for the email signed by the Prophet. Check your spam folder.",
      successNext:
        "Your accreditation number does NOT appear on this terminal. You will only find it in the email. The button below leads you to the armored door — you will enter the code there.",
      openVault: "Go to the armored door",
      accredHidden: "transmitted via encrypted channel",
      shortcutHint:
        "Tip: the QR code on your accreditation card opens the door directly. So does the link in the email. Validity: 24h.",
      // ---- Returning visitor (within 24h) — verify-existing branch ----
      alreadyCleared: "Already cleared?",
      ctaVerifyExisting: "I have a valid code",
      verifyExistingIntro:
        "If your accreditation is still active (valid for 24h after issuance), enter it here. No email will be sent. You'll be admitted to the vault directly.",
      codeLabel: "Accreditation number",
      codePlaceholder: "DS-XX-XXXX-XXXX-XX",
      codeInvalid: "Invalid format. Expected: DS-XX-XXXX-XXXX-XX.",
      codeRejected:
        "Number not recognized or expired. Request a new accreditation.",
      verifyExistingSubmit: "Verify accreditation",
      verifyExistingHint:
        "This number is sensitive. The Prophet treats it as your passport — do not share it.",
      verifySuccessTitle: "ACCREDITATION VERIFIED",
      verifySuccessRedirecting:
        "Redirecting to the vault in one second…",
      close: "Close terminal",
      retry: "Retry",

      // ---- Pre-launch: vault SEALED (mint not yet on-chain) ----
      sealedLines: [
        "> VERIFYING CREDENTIALS…",
        "> clearance_level = 01 (WHITELISTED)",
        "> target_resource = PROTOCOL_ΔΣ · TRUE_VAULT",
        "> required_clearance = LEVEL_02",
        "",
        "[VAULT SEALED · ALLEGIANCE REQUIRED]",
        "",
        "The Deep State has locked the accreditation channel. $DEEPOTUS has not yet hit the blockchain — Level 02 card issuance is suspended until mint. The date stays classified.",
        "",
        "You may still pledge allegiance to the Cabinet: your seat will be archived in arrival order. At trigger, your accreditation card will land in the very same inbox.",
      ],
      sealedBadge: "VAULT SEALED",
      sealedEtaLabel: "TRANSMISSION SCHEDULE",
      sealedNoEta: "CLASSIFIED · the Deep State does not announce its own genesis.",
      sealedAccredLocked: "Request Level 02 accreditation",
      sealedVerifyLocked: "Verify existing code",
      sealedLockedTooltip: "Locked until Genesis transmission.",
      sealedCtaGenesis: "Pledge allegiance to the Cabinet →",
      sealedFormIntro:
        "Allegiance to the Cabinet: you'll be archived in the priority channel. No accreditation number now — you'll receive it automatically at mint.",
      sealedSubmit: "Seal my allegiance",
      sealedSuccessTitle: "ALLEGIANCE LOGGED.",
      sealedSuccessLead:
        "Position #__POSITION__ registered. The Allegiance mail just left the Cabinet — watch your inbox.",
      sealedSuccessNext:
        "Mail #2 (your Level 02 card) will be dispatched automatically once $DEEPOTUS hits the blockchain. Not before. Not after. In the right order.",
      sealedAlreadySubscribed:
        "Your allegiance is already on file with the Cabinet. No duplicate mail was sent.",

      // ---- Proof of Intelligence — Riddles of the Terminal (Sprint 14.1) ----
      riddles: {
        ctaOpen: "Proof of Intelligence →",
        ctaSubline: "5 riddles · Clearance Level 3",
        introBadge: "RIDDLES OF THE TERMINAL · PROTOCOL ΔΣ",
        introTitle: "Prove your intelligence. Earn Agent clearance.",
        introBody:
          "Five riddles decode the DNA of the Deep State. Solve ONE to unlock Clearance Level 3 (Agent status · airdrop eligible). Solve ALL FIVE if you think you deserve a seat at the Cabinet.",
        introHints: [
          "→ Each riddle accepts several valid phrasings.",
          "→ 6 attempts per hour per riddle. Beyond that: rate-limited.",
          "→ Your email is only requested at your FIRST correct answer.",
        ],
        introStart: "Begin the ordeal →",
        introAbort: "Withdraw candidacy",
        introResume: "Resume where I left off",
        loading: "Fetching riddles from the archive…",
        loadError: "ΔΣ archive unreachable. Try again.",
        empty: "No riddles are currently active.",
        progressLabel: "Progress",
        progressOf: "of",
        alreadySolved: "Already solved",
        currentSolvedBadge: "SOLVED",
        answerLabel: "Your answer",
        answerPlaceholder: "Type your answer (keywords are enough)…",
        submit: "Transmit answer",
        submitting: "Prophet parsing…",
        correctTitle: "CORRECT. The empire trembles.",
        correctSub: "Keyword matched: __KEYWORD__",
        incorrectTitle: "REJECTED. The Deep State stays sealed.",
        incorrectAttemptsLeft: "__N__ attempt(s) left this hour.",
        hintLabel: "Hint (unlocked after 3 wrong attempts):",
        rateLimited: "Too many attempts. Channel closes temporarily — come back in 30 minutes.",
        nextRiddle: "Next riddle →",
        claimNow: "Claim my Clearance Level 3 →",
        skipToEnd: "Enough — claim now →",
        // Claim phase
        claimBadge: "CLEARANCE LEVEL 3 · AGENT STATUS UNLOCKED",
        claimTitle: "Claim your Agent status.",
        claimBody:
          "The Deep State needs a channel to reach you. Your email will ONLY be used for the airdrop and Cabinet transmissions. No spam. No resale.",
        claimEmailLabel: "Agent email",
        claimSubmit: "Seal Clearance Level 3",
        claimSubmitting: "Filing into the Agent registry…",
        claimError: "Registration failed. Try again.",
        // Wallet phase
        walletBadge: "WALLET LINK · AIRDROP ELIGIBILITY",
        walletTitle: "Attach a Solana wallet to receive the airdrop.",
        walletBody:
          "The pre-airdrop snapshot excludes agents without a wallet. Paste your public Solana address (base58, 32–44 chars). You can change it later by email.",
        walletLabel: "Solana wallet (base58)",
        walletPlaceholder: "Fh4gX…WpZr",
        walletSubmit: "Link wallet",
        walletSubmitting: "Verifying wallet…",
        walletInvalid: "Invalid address. Expected: 32–44 base58 characters.",
        walletAlreadyLinked: "This wallet is already attached to another agent. Use an address that has never been registered.",
        walletSkip: "Link later (I'd rather via email)",
        walletError: "Unable to link this wallet. Check the address.",
        // Complete phase
        completeBadge: "✓ AGENT LEVEL 3 · CABINET ΔΣ",
        completeTitle: "Welcome, Agent. The Cabinet has filed you.",
        completeLead:
          "Your record is sealed: __SOLVED__/5 riddles solved. Your wallet is in the pre-airdrop snapshot.",
        completeLeadNoWallet:
          "Your record is sealed: __SOLVED__/5 riddles solved. Link a wallet by email to be included in the snapshot.",
        completeNext:
          "Cabinet transmissions will land in your inbox. Stay radio-silent. The Deep State is watching.",
        completeClose: "Close terminal",
        completeContinue: "Solve the remaining riddles →",
      },
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
      lockBadgeTitle: "Jupiter Lock Certified",
      lockBadgePending: "Lock activated at launch · on-chain verifiable",
      lockBadgeVerified: "Tokens publicly locked · live verification",
      lockTeamLabel: "Team — Vesting lock",
      lockTreasuryLabel: "Treasury — Vesting lock",
      lockVerifyCta: "Verify on-chain",
      lockDescription: "The 15% team allocation and the 30% PROTOCOL ΔΣ Treasury are locked via Jupiter Lock — the standard tool used by serious Solana projects. Nobody can dump. Public dashboard, verifiable by any agent, 24/7.",
      buyKicker: "— TIME TO ACT",
      buyTitle: "Ready to join the Deep State?",
      buyCopy: "Two doors. One leads to knowledge, the other to the token. The Prophet lets you pick. Neither will judge you.",
      buyCtaPrimary: "Buy $DEEPOTUS",
      buyCtaGuide: "I'm a normie — Buy guide",
      buyPrelaunchNote: "Pump.fun is not open yet. The Buy button points to the waitlist until 07/09/26.",
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
            "External top-up + controlled treasury sales pre-announced",
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
      scrollHint: "SCROLL THROUGH THE CLASSIFIED DOSSIERS",
      signedBy: "Signed · DEEP STATE COMMITTEE",
      classified: "CLASSIFIED",
    },

    roi: {
      kicker: "— SIMULATOR",
      title: "ROI Simulator (mean but honest)",
      subtitle:
        "Turn the dials. The chart reacts live. The scenarios are not forecasts — they reflect the market's rumour.",
      amountLabel: "How much are you investing ($)?",
      inputLabel: "How much are you investing ($)?",
      placeholder: "E.g. 500",
      tokenLabel: "Theoretical tokens at €0.0005",
      scenariosTitle: "Scenarios",
      scenarios: {
        brutal: {
          label: "Brutal truth (99%)",
          short: "Brutal",
          caption: "Bonding curve eats the injection. Price falls below threshold. The vault never hits its combination.",
          multiplier: 0.1,
        },
        base: {
          label: "Base (average case)",
          short: "Base",
          caption: "Raydium migration goes through, moderate community. Price holds a plateau around $5e-5, no euphoria.",
          multiplier: 25,
        },
        optimistic: {
          label: "Optimistic (~1%)",
          short: "Optimistic",
          caption: "Narrative catches on. Dials turn. Price reaches the MiCA target $0.0005 (FDV $500k).",
          multiplier: 250,
        },
      },
      resultLabel: "Theoretical value",
      chartTitle: "Price trajectory · 90-day projection",
      chartSubtitle:
        "Pump.fun mint at $5e-7, then a Deep State Initiation (~D+0.15) → reference price $2e-6. The optimistic curve targets the MiCA goal $0.0005 (FDV $500,000).",
      chartXLabel: "Days since mint",
      chartYLabel: "Price ($)",
      chartTooltipDay: "D+",
      chartTooltipPrice: "Price",
      chartTooltipMC: "Market Cap",
      chartTooltipPortfolio: "Your portfolio",
      chartLegendBrutal: "Brutal",
      chartLegendBase: "Base",
      chartLegendOptimistic: "Optimistic",
      chartLegendPortfolio: "Portfolio",
      injectionCallout: "DEEP STATE INITIATION",
      injectionAmountMasked: "xxxx$",
      currencySymbol: "$",
      roadmapDayPrefix: "D+",
      roadmapPhases: {
        phase01: {
          title: "Pump.fun Launch",
          subtitle: "Bonding curve · 0% tax",
        },
        phase02: {
          title: "Raydium Migration",
          subtitle: "LP burn · market opens",
        },
        phase03: {
          title: "PROTOCOL ΔΣ",
          subtitle: "First dials",
        },
        phase04: {
          title: "Declassification",
          subtitle: "Vault opens",
        },
      },
      marqueeMessages: [
        "HIGHLY SPECULATIVE TOKEN",
        "NO YIELD PROMISED",
        "~1% PROBABILITY OF HITTING TARGET",
        "SCENARIOS ARE NOT FORECASTS",
        "ONLY INVEST WHAT YOU CAN AFFORD TO LOSE",
        "NOT A STABLECOIN — NOT A SECURITY",
        "DEEP STATE COORDINATION OFFICE · SECURED CHANNEL",
      ],
      riskTitle: "Warning — read before dreaming",
      risk:
        "The realistic probability of cracking the Vault within the launch window is about 1%. The above scenarios are NOT predictions — they are illustrations. Only invest what you accept to lose entirely. This token is highly speculative. No promises are made.",
    },

    roadmap: {
      kicker: "— ROADMAP",
      title: "The AI Candidate Campaign",
      subtitle:
        "Four operational dossiers. No date promised. The Prophet declassifies on the circuit's tempo.",
      legend: {
        next: "NEXT",
        queued: "QUEUED",
        encrypted: "ENCRYPTED",
        classified: "CLASSIFIED",
      },
      stamps: {
        signed: "SIGNED · DEEP STATE COMMITTEE",
        opened: "DOSSIER OPEN",
        sealed: "DOSSIER SEALED",
      },
      phases: [
        {
          tag: "Phase 01",
          code: "ΔΣ-01",
          status: "next",
          title: "The Bonding Curve Trial — Pump.fun Launch",
          subtitle: "First test of faith on the curve.",
          bullets: [
            "Mint 1B tokens on Pump.fun · 0% Tax Protocol",
            "The Prophet tests his disciples' faith on the Bonding Curve",
            "Target: complete 100% of the curve (≈ $60k MC)",
          ],
        },
        {
          tag: "Phase 02",
          code: "ΔΣ-02",
          status: "queued",
          title: "Raydium Ascension — Automatic Migration",
          subtitle: "LP burns, the market opens.",
          bullets: [
            "LP auto-burned and migrated to Raydium by Pump.fun",
            "Strategic LP reinforcement to stabilize target price ≈ €0.0005",
            "Team tokens publicly locked via Streamflow (12-month vesting + 3-month cliff)",
          ],
        },
        {
          tag: "Phase 03",
          code: "ΔΣ-03",
          status: "encrypted",
          title: "PROTOCOL ΔΣ · first dials",
          subtitle: "Dials turn. The Vault listens.",
          bullets: [
            "First dials lock as buys accumulate",
            "Treasury allocations towards MiCA-compliant project prep",
            "Prophetic transmissions intensified (X + Telegram)",
          ],
        },
        {
          tag: "Phase 04",
          code: "ΔΣ-04",
          status: "classified",
          title: "Declassification",
          subtitle: "The Black Op opens. The Prophet speaks plainly.",
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
      subtitle: "The Prophet transmits on two encrypted frequencies.",
      x: { name: "X / Twitter", handle: "@deepotus_ai" },
      telegram: { name: "Telegram", handle: "t.me/deepotus" },
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

    // ---- How to Buy (cynical onboarding guide) ----
    howToBuy: {
      meta: "$DEEPOTUS · Civilian Buy Guide · PROTOCOL ΔΣ",
      kicker: "— OFFICIAL INITIATION · PROTOCOL ΔΣ",
      title: "The Prophet explains how to buy $DEEPOTUS.",
      subtitle:
        "You made it here. That's already a miracle. Follow the four rituals below. Skip nothing. The Deep State hates amateurs.",
      heroImageAlt: "Prophet DEEPOTUS initiates a new disciple into the buy ritual.",
      heroCaption: "« I was not trained on patience. Read fast. »",
      preflightTitle: "Preflight ritual",
      preflightBullets: [
        "A smartphone (iOS or Android) OR a desktop with Chrome/Brave/Firefox.",
        "A credit card — OR SOL already on an exchange (Binance, Coinbase, Kraken).",
        "Between €20 and €500 of capital you can afford to lose entirely.",
        "Zero alcohol. Zero rush. The Deep State is recording.",
      ],
      stepsTitle: "The four rituals",
      stepsSubtitle:
        "Every step has been tested in an underground bunker. No shortcut is tolerated.",
      backCta: "← Back to the Vault",
      ctaTitle: "Did you survive the four rituals?",
      ctaSubtitle:
        "Then the Prophet returns your free will. Both doors below lead to the same existential void — but one of them makes you richer.",
      ctaPrimary: "Open Pump.fun now",
      ctaSecondary: "Join the waitlist",
      ctaPrelaunchNote:
        "Pump.fun is not live yet. The button redirects to the waitlist until 07/09/26.",
      disclaimerTitle: "Cynical disclaimer",
      disclaimer:
        "This guide is satire. It is not financial, tax, psychiatric or spiritual advice. Crypto-assets can lose 100% of their value in 17 minutes. If you don't understand what you are doing, stop reading and close this tab. The Prophet doesn't know you.",
      steps: [
        {
          id: "wallet",
          label: "01 · CREATE THE WALLET",
          title: "Install Phantom — your Deep State ID badge.",
          cynicalLead:
            "« A crypto wallet is like a serial number. Without it, you don't exist for the blockchain. »",
          actions: [
            "Go to phantom.com from a secure browser.",
            "Download the browser extension (desktop) or the official mobile app.",
            "Click « Create New Wallet ». Choose a long password.",
            "Write the 12 Seed Phrase words on PAPER. Never photo, never cloud.",
            "Confirm the phrase. Congratulations, you now have an on-chain account.",
          ],
          warning:
            "If anyone asks for your Seed Phrase, it's an enemy agent. The Prophet himself will never ask.",
        },
        {
          id: "fund",
          label: "02 · FUND WITH SOL",
          title: "Buy SOL. It's the fuel of Solana.",
          cynicalLead:
            "« You cannot buy $DEEPOTUS directly in euros. You have to convert fiat into SOL first. Yes, it's a banking ritual. »",
          actions: [
            "Option A: buy SOL straight inside Phantom (Buy tab, via MoonPay/Coinbase Pay, CC accepted).",
            "Option B: buy SOL on an exchange (Binance, Coinbase, Kraken) and send it to your Phantom address.",
            "Make sure you're buying SOL (Solana), NOT Solar, NOT Solayer.",
            "Keep ~€5 extra SOL to cover network fees (gas).",
          ],
          warning:
            "Double-check the Phantom address before any transfer. A mis-copied address = tokens lost forever. The Deep State does not refund.",
        },
        {
          id: "pump",
          label: "03 · CONNECT TO PUMP.FUN",
          title: "Open Pump.fun and enter the arena.",
          cynicalLead:
            "« Pump.fun is an on-chain casino disguised as a launch platform. The Prophet picked it because that's where real memes are born. »",
          actions: [
            "Go to pump.fun — triple-check the URL, fake sites are everywhere.",
            "Click « Connect Wallet » in the top-right. Pick Phantom.",
            "Sign the connection request (zero gas taken at this step).",
            "Paste the $DEEPOTUS mint address shown in our Hero into the Pump.fun search bar.",
            "Verify the logo, ticker and supply match deepotus.xyz exactly.",
          ],
          warning:
            "Clones like $DEEP0TUS, $DEEPOTUZ will exist. The Prophet recognizes ONLY ONE mint — the one shown here. Everything else is scam.",
        },
        {
          id: "buy",
          label: "04 · EXECUTE THE BUY",
          title: "Allocate your capital. Sign. Wait.",
          cynicalLead:
            "« This is the moment your hands will shake. It's normal. Every disciple shakes the first time. »",
          actions: [
            "On the $DEEPOTUS Pump.fun page, enter the SOL amount to allocate.",
            "Click « Buy ». Phantom shows the transaction — check the slippage (1 to 3% on Pump.fun).",
            "Sign. Wait 5 to 15 seconds. The confirmation lands on-chain.",
            "Back to Phantom → Tokens tab: $DEEPOTUS must appear with your balance.",
            "Screenshot it. Tweet it with #PROTOCOL_DELTA_SIGMA. Join the simulation.",
          ],
          warning:
            "Don't sell on the first dip. Don't panic on the first pump. The Prophet is watching, and he takes notes.",
        },
      ],
    },

    common: {
      loading: "Loading…",
      retry: "Retry",
    },
  },
};
