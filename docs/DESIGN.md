# QALQAN — Design System

> **QALQAN** (қалқан, "shield") — autonomous AI investigation platform for social-media fraud.
> **Design language:** Attio-inspired. Light, minimal, editorial, data-dense-but-airy.
> Clean white surfaces on an off-white canvas, hairline borders, soft pastel status pills,
> Inter + serif accents + monospace numerals, a single blue accent, near-black ink actions.
> **Stack:** Next.js 16 · React 19 · Tailwind v4 (`@theme`) · shadcn-style primitives.

---

## 0. Principles

1. **Quiet by default, loud only for signal.** The interface is calm white and grey; saturated
   colour appears *only* on risk, status, and live activity. Colour = meaning, never decoration.
2. **Whitespace is structure.** Generous padding (`p-6`), clear vertical rhythm (`space-y-5/6`),
   hairline separators instead of boxes-in-boxes.
3. **Plain language.** Every screen explains itself in one human sentence. No cryptic glyphs.
4. **Provenance over opinion.** Numbers link to evidence; cards always carry source + time.
5. **Soft, fast motion.** Short, crisp transitions; gentle pulses for "live". Nothing bouncy.

---

## 1. Colour

### Canvas & surfaces (cool neutrals)
```
--bg-base        #FAFAFB   /* app canvas (off-white)        */
--bg-surface-1   #FFFFFF   /* cards, panels, chrome         */
--bg-surface-2   #F7F8F9   /* insets, hover wells           */
--bg-surface-3   #F1F2F4   /* active rows, pressed          */
--border-subtle  #EEEFF1   /* hairlines inside components   */
--border-strong  #E4E7EC   /* card edges, dividers          */
--ink            #1C1D1F   /* near-black: primary buttons   */
```

### Text
```
--text-primary   #232529   /* headings, key values         */
--text-secondary #5C5E63   /* body, labels                 */
--text-muted     #9FA1A7   /* captions, meta, placeholders */
```

### Accent — "QALQAN blue" (links, active, focus)
```
--brand-400 #5C93F7   --brand-500 #266DF0   --brand-600 #1B57CF
--brand-glow rgba(38,109,240,0.18)
```

### Severity / risk — saturated dot + text, soft pill bg
The spine of the product. Used as a dot, as text, and as a soft pill (`bg/border` light).
```
critical  text #D92D20  pill bg #FEE4E2  border #FECDCA   (confirmed fraud)
high      text #E8590C  pill bg #FEEEE1  border #FEE0C8
medium    text #CA8A04  pill bg #FFF3CC  border #FFEBAD
low       text #067647  pill bg #DDF9E4  border #C7F4D3   (safe / cleared)
info      text #266DF0  pill bg #E5EEFF  border #D6E5FF
```

### Investigation semantics
```
--agent-live    #16A34A   /* green "online" pulse          */
--contradiction #7F56D9   /* violet — a caught lie          */
--evidence      #266DF0
--manipulation  #E8590C
```

### Data-viz categorical
```
#266DF0  #16A34A  #7F56D9  #CA8A04  #E8590C  #D92D20
```

**Rules:** red `#D92D20` is reserved for CRITICAL / confirmed fraud — scarcity keeps it loud.
Blue = the system & navigation. Violet = contradictions/lies (the product's signature signal).

---

## 2. Typography

```
Sans   "Inter"          — UI, body, headings (geometric, neutral)
Serif  "Newsreader"     — editorial accent: wordmark, hero/section titles (used sparingly)
Mono   "JetBrains Mono" — ALL numerals, IDs, hashes, timestamps, confidence, code

Scale (rem):
  display   2.0 / 1.15  640   page hero (serif optional)
  h1        1.5 / 1.2   600
  h2        1.25/ 1.25  600
  body      0.875/1.55  400   (14px default — dense but comfortable)
  small     0.8125/1.45 400
  micro     0.6875/1.3  500   UPPERCASE labels, tracking .06em, text-muted
  mono-kpi  1.5 / 1.0   500   tabular-nums
```

Treatments: section labels are `micro` UPPERCASE muted (e.g. `NEEDS YOUR DECISION`).
Confidence/scores are mono + `tabular-nums`. Never pure-black on pure-white — use `--text-primary`.

---

## 3. Shape, elevation, motion

- **Radius:** controls `rounded-[10px]`, cards `rounded-xl` (12px), pills `rounded-lg`.
- **Elevation = soft shadow, not heavy borders.** Cards: 1px subtle border + tiny shadow
  `0 1px 2px rgba(28,40,64,.04), 0 2px 6px rgba(28,40,64,.04)`.
- **Dividers:** hairline `--border-subtle`; long structural lines may be **dashed** (Attio motif).
- **Motion tokens:** `--ease-out cubic-bezier(.16,1,.3,1)`, `--dur-fast 120ms / base 200ms`.
  Live pulse (2s ring), typing dots, count-up KPIs, contradiction flash (violet → settle).
  Respect `prefers-reduced-motion`.

---

## 4. Components

shadcn-style primitives in `src/components/ui`, themed with the tokens above.

- **Button** — `primary` = ink (`--ink`) + white; `outline` = white + `border-strong`;
  `ghost` = transparent → `bg-surface-2`. `h-9`, `rounded-[10px]`, blue focus ring.
- **Card** — white, `border-strong`, soft shadow, `rounded-xl`. Header = micro label row.
- **SeverityBadge** — dot + UPPERCASE label in severity colour; pill variant uses soft bg+border.
- **ConfidenceMeter** — thin track + mono % + trend, fill colour from severity bucket.
- **KpiStat** — micro label, mono value, green delta.
- **AgentChip / LivePulseDot / TypingDots** — green "online" pulse, 3-dot typing.
- **PageIntro** — plain-language title + one-sentence lead, hairline underline.
- **HowItWorks** — 4-step pipeline (Detect → Investigate → Cross-examine → Verdict).
- **Tables** — sticky header, severity dot first cell, mono tabular cells, row hover `surface-3`,
  reveal-on-hover actions, optional dashed column guides.
- **Knowledge graph** — typed node shapes (hexagon account / diamond wallet / square phone /
  circle victim / dashed cluster), typed edges (solid money, dashed referral, dotted device),
  white canvas, dotted background grid, node inspector.
- **Toaster (sonner)** — light theme, top-right, for "lie caught / report ready".

State matrix per interactive element: `default · hover · focus-visible (blue ring) · active ·
disabled · loading`.

---

## 5. Layout

Three-zone shell on light chrome: **left nav rail (white, hairline border)** · **top bar
(white, search + clock + live count)** · **content (off-white canvas)** · **bottom status strip**.
In a case: header + tab bar (Overview · War Room · Contradictions · Graph · Timeline · Report).
Right contextual panel (dossier / inspector / live ops) per screen.

**Pages:** Command Center · Detections feed/detail · Investigations list · Investigation Center ·
Agent War Room · Contradiction Matrix · Knowledge Graph · Evidence Timeline · AI Prosecutor Report ·
Risk Analytics · Entities · Agents · Evidence Vault · Reports · Settings.

---

## 6. Voice & naming

Product is **QALQAN** (shield). Tone: operational, confident, human. Prefer "Lies caught",
"Needs your decision", "Where the story falls apart" over jargon. Mono for every machine value.

---

## 7. Tailwind v4 wiring

Tokens live in `src/app/globals.css` under `:root` + `@theme inline`, so utilities like
`bg-bg-base`, `bg-bg-surface-1`, `text-text-primary`, `border-border-strong`, `text-sev-critical`,
`text-contradiction`, `ring-brand-glow`, `bg-ink` work directly. Light is the only theme
(no dark media query). Fonts: Inter (`--font-sans`), Newsreader (`--font-serif`),
JetBrains Mono (`--font-mono`) via `next/font/google` in the root layout.
