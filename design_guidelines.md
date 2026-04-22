{
  "design_personality": {
    "brand_archetype": "Satirical-but-credible presidential campaign for an AI candidate; top-of-page feels institutional/MiCA-aware, bottom-of-page devolves into brutalist degen propaganda.",
    "keywords": [
      "institutional clarity",
      "terminal-grade transparency",
      "deepfake/glitch patina",
      "neo-brutalist meme energy",
      "cynical prophecy tone",
      "audit-like data blocks",
      "campaign poster pastiche"
    ],
    "layout_principle": "Hybrid: Swiss grid + terminal panels (top 60%) → asymmetrical brutalist collage + sticker-like callouts (bottom 40%).",
    "content_strategy": {
      "above_fold": "Hook + credibility: candidate poster, key numbers, countdown, primary CTA, MiCA disclaimers preview.",
      "mid_page": "Interactive proof: chat, prophecies feed, tokenomics chart, transparency timeline.",
      "below": "Degen payoff: brutal truth probabilities, ROI simulator with warnings, meme slogans, socials, full disclaimers."
    }
  },

  "inspiration_refs": {
    "web_search_refs": [
      {
        "title": "Brutalist crypto UI references (Dribbble tag/search)",
        "url": "https://dribbble.com/search/brutalist"
      },
      {
        "title": "Bloomberg/terminal-style UI references (Dribbble search)",
        "url": "https://dribbble.com/search/bloomberg-terminal"
      },
      {
        "title": "Terminal-style UI references (Dribbble search)",
        "url": "https://dribbble.com/search/terminal-style"
      },
      {
        "title": "Behance crypto design references", 
        "url": "https://www.behance.net/search/projects/crypto%20design"
      }
    ],
    "fusion_recipe": "Typography + spacing discipline from Swiss/editorial layouts; data density + color accents from Bloomberg Terminal; glitch/scanline overlays from CRT UI; brutalist sticker/collage blocks for degen sections."
  },

  "typography": {
    "google_fonts": {
      "display": {
        "family": "Space Grotesk",
        "weights": [400, 500, 600, 700],
        "usage": "Headlines, nav, section titles (campaign poster feel without being cheesy)."
      },
      "body": {
        "family": "IBM Plex Sans",
        "weights": [400, 500, 600],
        "usage": "Body copy, disclaimers, UI labels (institutional readability)."
      },
      "mono": {
        "family": "IBM Plex Mono",
        "weights": [400, 500, 600],
        "usage": "Terminal panels, numbers, probabilities, token stats, prophecies feed."
      }
    },
    "tailwind_font_tokens": {
      "font-display": "'Space Grotesk', ui-sans-serif, system-ui",
      "font-body": "'IBM Plex Sans', ui-sans-serif, system-ui",
      "font-mono": "'IBM Plex Mono', ui-monospace, SFMono-Regular"
    },
    "text_size_hierarchy": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl",
      "h2": "text-base md:text-lg",
      "body": "text-sm md:text-base",
      "small": "text-xs md:text-sm",
      "numeric": "tabular-nums tracking-tight"
    },
    "type_rules": [
      "Use ALL CAPS sparingly: only for campaign stamps (e.g., 'AI-GENERATED', 'THIS IS A SIMULATION').",
      "Numbers (supply, FDV, probabilities) always in mono with tabular-nums.",
      "Disclaimers: IBM Plex Sans, text-xs, leading-relaxed, max-w-prose for readability."
    ]
  },

  "color_system": {
    "notes": "Avoid purple. Use institutional neutrals + terminal green + warning amber + campaign red used as a small accent only.",
    "palette": {
      "paper": "#F6F2EA",
      "ink": "#0B0D10",
      "slate": "#111827",
      "panel": "#0E141B",
      "border": "#1F2937",
      "muted": "#6B7280",
      "terminal_green": "#33FF33",
      "terminal_green_dim": "#18C964",
      "ocean": "#2DD4BF",
      "amber": "#F59E0B",
      "campaign_red": "#E11D48",
      "danger": "#DC2626",
      "success": "#16A34A"
    },
    "semantic_tokens_hsl_for_shadcn": {
      "light": {
        "--background": "40 33% 94%",
        "--foreground": "222 47% 11%",
        "--card": "40 33% 96%",
        "--card-foreground": "222 47% 11%",
        "--popover": "40 33% 96%",
        "--popover-foreground": "222 47% 11%",
        "--primary": "222 47% 11%",
        "--primary-foreground": "40 33% 96%",
        "--secondary": "210 20% 92%",
        "--secondary-foreground": "222 47% 11%",
        "--muted": "210 20% 92%",
        "--muted-foreground": "215 16% 35%",
        "--accent": "173 80% 40%",
        "--accent-foreground": "222 47% 11%",
        "--destructive": "0 72% 51%",
        "--destructive-foreground": "40 33% 96%",
        "--border": "215 20% 80%",
        "--input": "215 20% 80%",
        "--ring": "173 80% 40%",
        "--radius": "0.9rem",
        "--chart-1": "173 80% 40%",
        "--chart-2": "142 71% 45%",
        "--chart-3": "38 92% 50%",
        "--chart-4": "0 72% 51%",
        "--chart-5": "222 47% 11%"
      },
      "dark": {
        "--background": "222 47% 7%",
        "--foreground": "40 33% 96%",
        "--card": "222 47% 9%",
        "--card-foreground": "40 33% 96%",
        "--popover": "222 47% 9%",
        "--popover-foreground": "40 33% 96%",
        "--primary": "40 33% 96%",
        "--primary-foreground": "222 47% 11%",
        "--secondary": "215 28% 17%",
        "--secondary-foreground": "40 33% 96%",
        "--muted": "215 28% 17%",
        "--muted-foreground": "215 20% 70%",
        "--accent": "173 80% 40%",
        "--accent-foreground": "222 47% 11%",
        "--destructive": "0 72% 51%",
        "--destructive-foreground": "40 33% 96%",
        "--border": "215 28% 17%",
        "--input": "215 28% 17%",
        "--ring": "173 80% 40%",
        "--radius": "0.9rem",
        "--chart-1": "173 80% 40%",
        "--chart-2": "142 71% 45%",
        "--chart-3": "38 92% 50%",
        "--chart-4": "0 72% 51%",
        "--chart-5": "40 33% 96%"
      }
    },
    "gradients": {
      "allowed_usage": "Hero background overlay only (<=20% viewport). Decorative corner washes behind poster portrait.",
      "gradient_1": "linear-gradient(135deg, rgba(45,212,191,0.18) 0%, rgba(51,255,51,0.10) 45%, rgba(245,158,11,0.10) 100%)",
      "gradient_2": "radial-gradient(60% 60% at 20% 10%, rgba(45,212,191,0.18) 0%, rgba(0,0,0,0) 60%)",
      "restriction": "Never use saturated purple/pink gradients; never apply gradients to text-heavy panels; never on small UI elements (<100px)."
    }
  },

  "design_tokens_css": {
    "instructions": "Main agent should update /app/frontend/src/index.css :root and .dark tokens to match semantic_tokens_hsl_for_shadcn. Add extra custom properties below.",
    "extra_css_custom_properties": {
      "--font-display": "Space Grotesk",
      "--font-body": "IBM Plex Sans",
      "--font-mono": "IBM Plex Mono",
      "--shadow-elev-1": "0 1px 0 rgba(0,0,0,0.08), 0 10px 30px rgba(0,0,0,0.10)",
      "--shadow-elev-2": "0 2px 0 rgba(0,0,0,0.10), 0 18px 50px rgba(0,0,0,0.18)",
      "--noise-opacity": "0.06",
      "--scanline-opacity": "0.08",
      "--focus-ring": "0 0 0 3px rgba(45,212,191,0.35)",
      "--btn-radius": "12px",
      "--btn-shadow": "0 1px 0 rgba(0,0,0,0.12), 0 10px 24px rgba(0,0,0,0.14)",
      "--btn-press-scale": "0.98"
    }
  },

  "grid_and_layout": {
    "container": "max-w-6xl mx-auto px-4 sm:px-6 lg:px-8",
    "section_spacing": "py-14 sm:py-18 lg:py-24",
    "top_to_bottom_structure": {
      "top_60_percent": "Clean campaign + terminal panels; consistent grid; restrained accents.",
      "bottom_40_percent": "Asymmetry: rotated stamps, sticker badges, rough borders, louder copy; still readable."
    },
    "patterns": [
      "Use a 12-col grid on desktop; collapse to single column on mobile.",
      "Use 'bento' clusters for stats: 2x2 cards on desktop, stacked on mobile.",
      "Keep long text blocks max-w-prose to avoid wall-of-text."
    ]
  },

  "components": {
    "component_path": {
      "shadcn": {
        "button": "/app/frontend/src/components/ui/button.jsx",
        "card": "/app/frontend/src/components/ui/card.jsx",
        "badge": "/app/frontend/src/components/ui/badge.jsx",
        "tabs": "/app/frontend/src/components/ui/tabs.jsx",
        "accordion": "/app/frontend/src/components/ui/accordion.jsx",
        "input": "/app/frontend/src/components/ui/input.jsx",
        "textarea": "/app/frontend/src/components/ui/textarea.jsx",
        "separator": "/app/frontend/src/components/ui/separator.jsx",
        "progress": "/app/frontend/src/components/ui/progress.jsx",
        "tooltip": "/app/frontend/src/components/ui/tooltip.jsx",
        "scroll_area": "/app/frontend/src/components/ui/scroll-area.jsx",
        "navigation_menu": "/app/frontend/src/components/ui/navigation-menu.jsx",
        "sheet": "/app/frontend/src/components/ui/sheet.jsx",
        "sonner": "/app/frontend/src/components/ui/sonner.jsx"
      }
    },
    "custom_components_to_build": [
      {
        "name": "LanguageToggle",
        "description": "FR/EN switch (segmented control). Persist in localStorage.",
        "base": "Tabs or ToggleGroup",
        "data_testid": "language-toggle"
      },
      {
        "name": "DeepfakePosterHero",
        "description": "Hero with portrait, glitch overlay, campaign stamps, countdown, CTA.",
        "data_testid": "hero-section"
      },
      {
        "name": "PropheciesTicker",
        "description": "Auto-rotating one-liners with terminal vibe + subtle glitch.",
        "data_testid": "prophecies-feed"
      },
      {
        "name": "ProphetChat",
        "description": "Chat UI with cynical AI Prophet persona; message bubbles styled as terminal logs.",
        "data_testid": "prophet-chat"
      },
      {
        "name": "TokenomicsPie",
        "description": "Interactive pie chart with hover tooltips + legend cards.",
        "data_testid": "tokenomics-chart"
      },
      {
        "name": "TransparencyTimeline",
        "description": "J0 → J+2 timeline with LP scaling + anti-dump measures.",
        "data_testid": "transparency-timeline"
      },
      {
        "name": "ROISimulator",
        "description": "Input € amount → tokens + scenarios + risk warning.",
        "data_testid": "roi-simulator"
      },
      {
        "name": "BrutalTruthBlock",
        "description": "Probability stats presented proudly with dark humor.",
        "data_testid": "brutal-truth"
      }
    ]
  },

  "section_blueprints": {
    "sticky_nav": {
      "layout": "Sticky top bar with logo left, anchors center (desktop), language toggle + Buy CTA right. Mobile uses Sheet drawer.",
      "ui": ["navigation-menu", "sheet", "button", "badge"],
      "data_testids": {
        "nav": "top-nav",
        "buy_cta": "nav-buy-button",
        "join_cta": "nav-join-button",
        "lang_toggle": "nav-language-toggle"
      },
      "styles": {
        "bar": "backdrop-blur-md bg-background/70 border-b border-border",
        "logo": "font-display tracking-tight",
        "cta": "rounded-[var(--btn-radius)]"
      }
    },

    "hero": {
      "layout": "Split: left copy + stats chips; right portrait poster card. On mobile: portrait first then copy.",
      "must_include": ["countdown", "primary CTA", "key stats", "mini disclaimer"],
      "ui": ["card", "badge", "button", "separator"],
      "copy_notes": "Slogan must be bilingual and punchy. Add 'AI-GENERATED' stamp + 'THIS IS A SIMULATION' microcopy.",
      "styles": {
        "hero_bg": "relative overflow-hidden",
        "hero_overlay": "before:absolute before:inset-0 before:bg-[image:var(--hero-gradient)] before:opacity-100",
        "poster_card": "bg-card border border-border shadow-[var(--shadow-elev-2)]",
        "stamps": "uppercase font-mono text-[10px] tracking-[0.22em]"
      },
      "data_testids": {
        "countdown": "hero-countdown",
        "join_button": "hero-join-button",
        "buy_button": "hero-buy-button"
      }
    },

    "manifesto": {
      "layout": "Editorial block with pull-quote + short paragraphs; include a 'Prophecy ID' hash-like string.",
      "ui": ["card", "separator"],
      "data_testids": {
        "manifesto": "manifesto-section"
      }
    },

    "chat": {
      "layout": "Two-column: left instructions + persona rules; right chat panel. Mobile: stacked.",
      "ui": ["card", "textarea", "button", "scroll-area", "badge"],
      "interaction": "Enter to send; Shift+Enter newline; typing indicator skeleton; toast on error.",
      "data_testids": {
        "input": "prophet-chat-input",
        "send": "prophet-chat-send-button",
        "messages": "prophet-chat-messages"
      }
    },

    "prophecies_feed": {
      "layout": "Ticker-like carousel (no heavy video). Use Carousel or custom framer-motion crossfade.",
      "ui": ["carousel", "badge", "tooltip"],
      "data_testids": {
        "ticker": "prophecies-ticker"
      }
    },

    "mission_gencoin": {
      "layout": "Institutional: left narrative, right 'MiCA compliance checklist' cards.",
      "ui": ["card", "badge", "accordion"],
      "data_testids": {
        "mission": "mission-section"
      }
    },

    "tokenomics": {
      "layout": "Pie chart left, allocation cards right; on mobile chart first then cards.",
      "library": "recharts",
      "ui": ["card", "tooltip", "badge"],
      "data_testids": {
        "chart": "tokenomics-pie",
        "legend": "tokenomics-legend"
      }
    },

    "liquidity_treasury_timeline": {
      "layout": "Horizontal timeline on desktop; vertical on mobile. Each node is a Card with mono numbers.",
      "ui": ["card", "badge", "separator"],
      "data_testids": {
        "timeline": "lp-treasury-timeline"
      }
    },

    "roi_simulator": {
      "layout": "Input panel + results panel + warning panel. Include scenario tabs (base / optimistic / brutal truth).",
      "ui": ["card", "input", "tabs", "badge", "alert"],
      "data_testids": {
        "amount": "roi-amount-input",
        "results": "roi-results",
        "warning": "roi-risk-warning"
      }
    },

    "roadmap": {
      "layout": "Campaign-style milestones with 'phase cards' and a thin progress line.",
      "ui": ["card", "progress", "badge"],
      "data_testids": {
        "roadmap": "roadmap-section"
      }
    },

    "brutal_truth": {
      "layout": "Full-width block with rough border + big mono percentages; dark humor captions.",
      "ui": ["card", "badge"],
      "data_testids": {
        "truth": "brutal-truth-section"
      }
    },

    "faq": {
      "layout": "Accordion with MiCA-first questions; include tax, treasury, vesting.",
      "ui": ["accordion"],
      "data_testids": {
        "faq": "faq-section"
      }
    },

    "whitelist": {
      "layout": "Email capture with campaign copy 'Claim your seat in the cabinet'.",
      "ui": ["card", "input", "button"],
      "data_testids": {
        "email": "whitelist-email-input",
        "submit": "whitelist-submit-button",
        "success": "whitelist-success-message"
      }
    },

    "socials": {
      "layout": "3 cards with platform mock previews; include QR placeholder.",
      "ui": ["card", "button", "badge"],
      "data_testids": {
        "socials": "socials-section",
        "x": "social-x-link",
        "telegram": "social-telegram-link",
        "discord": "social-discord-link"
      }
    },

    "footer_disclaimer": {
      "layout": "Dense legal block with language toggle redundancy + links.",
      "ui": ["separator"],
      "data_testids": {
        "footer": "footer",
        "disclaimer": "mica-disclaimer"
      }
    }
  },

  "motion_and_microinteractions": {
    "library": "framer-motion",
    "principles": [
      "Use motion to imply 'broadcast' and 'terminal refresh'—not playful bounces.",
      "Prefer opacity/blur/clipPath reveals; avoid heavy transforms on large containers.",
      "Respect prefers-reduced-motion: disable glitch jitter and auto-rotations."
    ],
    "recipes": {
      "button": {
        "hover": "shadow intensifies + slight translateY(-1px)",
        "press": "scale(var(--btn-press-scale))",
        "tailwind": "transition-[background-color,border-color,box-shadow,opacity] duration-200"
      },
      "glitch_stamp": {
        "effect": "Occasional 120ms RGB split + scanline flicker on hover only",
        "implementation_hint": "Use CSS pseudo-elements with mix-blend-mode: screen; animate background-position"
      },
      "prophecies": {
        "effect": "Crossfade + subtle typewriter caret",
        "implementation_hint": "Framer Motion AnimatePresence + CSS caret animation"
      },
      "section_reveal": {
        "effect": "On-scroll reveal: y=12 → 0, opacity 0 → 1",
        "implementation_hint": "whileInView with viewport once:true"
      }
    }
  },

  "visual_effects": {
    "no_video_background": true,
    "crt_scanlines_css": "background-image: repeating-linear-gradient(to bottom, rgba(0,0,0,var(--scanline-opacity)) 0px, rgba(0,0,0,var(--scanline-opacity)) 1px, rgba(0,0,0,0) 3px, rgba(0,0,0,0) 6px);",
    "noise_overlay_css": "background-image: url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"120\" height=\"120\"><filter id=\"n\"><feTurbulence type=\"fractalNoise\" baseFrequency=\"0.9\" numOctaves=\"3\" stitchTiles=\"stitch\"/></filter><rect width=\"120\" height=\"120\" filter=\"url(%23n)\" opacity=\"0.35\"/></svg>');",
    "usage": "Apply noise overlay only to hero + brutal truth block (<=20% viewport each).",
    "poster_treatment": "Use portrait image inside Card with grayscale + contrast + slight hue-rotate; add 'AI GENERATED' stamp overlay."
  },

  "data_visualization": {
    "library": "recharts",
    "pie_chart_rules": [
      "Use 5–6 slices max; group small allocations if needed.",
      "Hover shows Tooltip with allocation %, vesting notes, and purpose.",
      "Legend cards clickable to highlight slice (opacity dim others)."
    ],
    "colors_for_slices": {
      "treasury": "#2DD4BF",
      "liquidity": "#33FF33",
      "marketing": "#F59E0B",
      "airdrops": "#E11D48",
      "ai_lore": "#16A34A",
      "team": "#0B0D10"
    }
  },

  "accessibility": {
    "aa_contrast": true,
    "rules": [
      "All text on dark panels must be >= text-sm with sufficient contrast; avoid low-contrast gray on dark.",
      "Focus states: visible ring using --ring; never remove outline without replacement.",
      "Language toggle must be keyboard accessible and announce current language.",
      "Chat: aria-live for new messages; ensure scroll area is reachable by keyboard.",
      "Respect prefers-reduced-motion: disable ticker auto-rotate and glitch flicker."
    ]
  },

  "testing_attributes": {
    "rule": "All interactive and key informational elements MUST include data-testid in kebab-case.",
    "examples": [
      "data-testid=\"hero-join-button\"",
      "data-testid=\"tokenomics-pie\"",
      "data-testid=\"roi-amount-input\"",
      "data-testid=\"mica-disclaimer\""
    ]
  },

  "image_urls": {
    "hero_portrait_options": [
      {
        "url": "https://images.pexels.com/photos/10482161/pexels-photo-10482161.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "description": "Abstract glitch portrait (AI Prophet poster base).",
        "category": "hero"
      },
      {
        "url": "https://images.unsplash.com/photo-1701958212633-17fa6aa37a4d?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85",
        "description": "Painterly suited figure (use with heavy glitch overlay).",
        "category": "hero"
      }
    ],
    "background_texture": [
      {
        "url": "https://images.pexels.com/photos/9817422/pexels-photo-9817422.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "description": "Glitch ripple texture for small decorative overlays (not full-screen).",
        "category": "decor"
      }
    ]
  },

  "libraries_and_installation": {
    "required": [
      {
        "name": "framer-motion",
        "usage": "Section reveals, ticker transitions, subtle hover microinteractions.",
        "install": "npm i framer-motion"
      },
      {
        "name": "recharts",
        "usage": "Tokenomics pie chart + small sparkline-like charts if needed.",
        "install": "npm i recharts"
      },
      {
        "name": "react-i18next",
        "usage": "Bilingual FR/EN with context + language persistence.",
        "install": "npm i i18next react-i18next"
      }
    ],
    "optional": [
      {
        "name": "@studio-freight/lenis",
        "usage": "Premium smooth scroll (ensure reduced motion fallback).",
        "install": "npm i @studio-freight/lenis"
      }
    ]
  },

  "instructions_to_main_agent": [
    "Replace CRA default App.css usage; avoid centering containers globally.",
    "Update /app/frontend/src/index.css tokens to match semantic_tokens_hsl_for_shadcn; keep shadcn structure.",
    "Implement bilingual copy via i18n dictionary; every string must be translatable.",
    "Top sections should feel credible: clean grid, restrained accents, clear disclaimers.",
    "Bottom sections can be louder/brutalist: rotated stamps, rough borders, terminal green highlights.",
    "No video backgrounds. Use CSS noise + scanlines overlays only in hero and brutal truth blocks (<=20% viewport each).",
    "All interactive and key informational elements must include data-testid attributes (kebab-case).",
    "Use shadcn components from /app/frontend/src/components/ui (JS files) for inputs, accordions, dialogs, etc."
  ]
}

---

<General UI UX Design Guidelines>  
    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms
    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text
   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json

 **GRADIENT RESTRICTION RULE**
NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc
NEVER use dark gradients for logo, testimonial, footer etc
NEVER let gradients cover more than 20% of the viewport.
NEVER apply gradients to text-heavy content or reading areas.
NEVER use gradients on small UI elements (<100px width).
NEVER stack multiple gradient layers in the same viewport.

**ENFORCEMENT RULE:**
    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors

**How and where to use:**
   • Section backgrounds (not content backgrounds)
   • Hero section header content. Eg: dark to light to dark color
   • Decorative overlays and accent elements only
   • Hero section with 2-3 mild color
   • Gradients creation can be done for any angle say horizontal, vertical or diagonal

- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**

</Font Guidelines>

- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. 
   
- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.

- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.
   
- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly
    Eg: - if it implies playful/energetic, choose a colorful scheme
           - if it implies monochrome/minimal, choose a black–white/neutral scheme

**Component Reuse:**
	- Prioritize using pre-existing components from src/components/ui when applicable
	- Create new components that match the style and conventions of existing components when needed
	- Examine existing components to understand the project's component patterns before creating new ones

**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component

**Best Practices:**
	- Use Shadcn/UI as the primary component library for consistency and accessibility
	- Import path: ./components/[component-name]

**Export Conventions:**
	- Components MUST use named exports (export const ComponentName = ...)
	- Pages MUST use default exports (export default function PageName() {...})

**Toasts:**
  - Use `sonner` for toasts"
  - Sonner component are located in `/app/src/components/ui/sonner.tsx`

Use 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.
</General UI UX Design Guidelines>
