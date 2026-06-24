# SwarmShield AI — Design System & Product Specification

> **Product class:** Autonomous AI Investigation Platform (financial intelligence / cyber).
> **Not** a content-moderation tool. **Not** a generic SaaS admin panel.
> **Design lineage:** Palantir Gotham · CrowdStrike Falcon · SentinelOne · Splunk ES · Datadog Security · Recorded Future · Arkham Intelligence.
> **Stack:** Next.js 16 (App Router) · React 19 · Tailwind v4 (`@theme`) · shadcn/ui · Radix.

---

## 0. Design Thesis — why it must feel like an intelligence platform

An investigation platform sells **trust in a verdict**. The UI's job is to make the operator feel that a machine did relentless, defensible work and is now handing over evidence — not a "score." Three principles govern every screen:

1. **Evidence over opinion.** Every claim is clickable down to a source artifact (frame, transcript line, message). No floating numbers without provenance.
2. **Adversarial framing.** The product is a *prosecutor*, not a *moderator*. Language, color, and layout convey investigation, contradiction, and proof — not "flagging."
3. **Density with hierarchy.** Operators scan, not read. High information density (Splunk/Gotham) but with a strict typographic and color hierarchy so the eye lands on risk first.

---

## 1. Information Architecture

```
SwarmShield AI
│
├── 01  Command Center (Dashboard)          /                      global situational awareness
├── 02  Detection Feed                       /detections            inbound suspicious media stream
│       └── Detection Detail                 /detections/[id]
├── 03  Investigations                       /investigations        case management
│       ├── Investigation Center             /investigations/[id]   the case workspace (hub)
│       ├── Agent War Room                   /investigations/[id]/agents
│       ├── Contradiction Matrix             /investigations/[id]/contradictions
│       ├── Knowledge Graph                  /investigations/[id]/graph
│       ├── Evidence Timeline                /investigations/[id]/timeline
│       └── AI Prosecutor Report             /investigations/[id]/report
├── 04  Targets / Entities                   /entities              accounts, channels, wallets, phones
│       └── Entity Profile                   /entities/[id]
├── 05  Risk Analytics                        /analytics             org-level risk dashboards
├── 06  Agents (Fleet)                        /agents                agent roster, personas, health
├── 07  Evidence Vault                        /evidence              all artifacts, chain-of-custody
├── 08  Reports & Exports                     /reports               generated dossiers, share
└── 09  Settings / Admin / Audit              /settings              models, sources, RBAC, audit log
```

**Object model (mental model the IA encodes):**

```
Detection ──promotes──▶ Investigation ──spawns──▶ Agents ──produce──▶ Conversations
                              │                                            │
                              ▼                                            ▼
                          Entities ◀──linked──── Knowledge Graph ◀──── Evidence ──▶ Contradictions
                              │                                            │
                              └──────────────▶ AI Prosecutor Report ◀──────┘
```

The IA is **case-centric**, like Gotham. Everything ladders up to an *Investigation*; the dashboard and feed are funnels into it; the graph, timeline, and report are *views over the same case object*.

---

## 2. Page Inventory (all screens)

| # | Screen | Primary job | Persona |
|---|--------|-------------|---------|
| 1 | Command Center | "What needs me right now?" | Analyst / Lead |
| 2 | Detection Feed | Triage inbound suspicious media | Analyst |
| 3 | Detection Detail | Decide: dismiss / promote to case | Analyst |
| 4 | Investigations List | Manage caseload | Lead |
| 5 | Investigation Center | Run a single case (hub) | Analyst |
| 6 | Agent War Room | Watch swarm interrogate live | Analyst |
| 7 | Contradiction Matrix | Find lies across agent threads | Analyst |
| 8 | Knowledge Graph | See the network | Analyst / Lead |
| 9 | Evidence Timeline | Reconstruct sequence of facts | Analyst |
| 10 | AI Prosecutor Report | Read/export the verdict | Lead / Legal |
| 11 | Risk Analytics | Org trends, cohorts, exposure | Lead / Exec |
| 12 | Entity Profile | Everything on one account | Analyst |
| 13 | Agent Fleet | Configure/monitor agents | Admin |
| 14 | Evidence Vault | Search all artifacts | Analyst |
| 15 | Settings/Audit | Govern the platform | Admin |
| — | Auth / SSO | Enter | All |
| — | Empty / Onboarding | First run | All |

---

## 3. Core User Flow

```
                    ┌──────────────────────────────────────────────────────┐
                    │                    INGEST (autonomous)                 │
                    │  crawlers → TikTok / IG / YT → media queue             │
                    └───────────────────────────┬──────────────────────────┘
                                                 ▼
   ┌─────────────────┐   AI media analysis   ┌─────────────────┐
   │  DETECTION FEED │◀──(ASR+OCR+vision+   │ Risk classifier │  pyramid? casino? scam?
   │  risk-sorted    │   subtitle+audio)─────│  → risk score   │
   └────────┬────────┘                       └─────────────────┘
            │ analyst triage
            ▼
   ┌─────────────────┐    promote     ┌──────────────────────────────────────┐
   │ DETECTION DETAIL│───────────────▶│         INVESTIGATION CENTER          │
   └─────────────────┘                │  define objective, deploy swarm       │
            │ dismiss                  └───────────────┬──────────────────────┘
            ▼                                          ▼  deploy N agents
        archived                          ┌────────────────────────────┐
                                          │       AGENT WAR ROOM        │ live multi-thread
                                          │  agent_1 … agent_N talk to  │ interrogation
                                          │  the suspect independently  │
                                          └──────────────┬─────────────┘
                                                         ▼ on completion
        ┌──────────────────────┬─────────────────────────┼────────────────────────┐
        ▼                      ▼                          ▼                        ▼
 CONTRADICTION MATRIX   KNOWLEDGE GRAPH          EVIDENCE TIMELINE         RISK ANALYSIS
 (compare answers,      (entities, money,        (chronology of           (manipulation
  detect lies)           links, wallets)          proof)                    techniques)
        └──────────────────────┴─────────────────────────┼────────────────────────┘
                                                          ▼
                                              ┌────────────────────────┐
                                              │   AI PROSECUTOR REPORT  │  verdict + evidence
                                              │   export / share / case │  chain → handoff
                                              └────────────────────────┘
```

**Flow narrative:** the system works while the human sleeps (ingest + analysis are autonomous). The human enters at **triage**, makes the one high-judgment call (*promote to investigation*), then becomes a **director of a swarm** rather than a chat operator. The four analysis surfaces are parallel lenses on the same evidence, converging into one exportable verdict.

---

## 4. Command Center (Dashboard) — Layout

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ [◣ SWARMSHIELD]   Command Center  Detections  Investigations  Entities  Analytics  ⌘K │  ← top bar
│                                                          ◷ live   ⬤ 14 agents active  ⚙ │
├──────────┬─────────────────────────────────────────────────────────────────┬─────────┤
│          │  THREAT POSTURE                              ELEVATED ▲           │ LIVE OPS│
│ NAV RAIL │  ┌───────────┬───────────┬───────────┬───────────┐               │ ┌─────┐ │
│          │  │ ACTIVE     │ AGENTS    │ NEW DETECT│ CONTRAD.  │               │ │a_03 │ │
│ ◳ Cmd    │  │ CASES  23  │ LIVE  14  │ 24h   312 │ FOUND 47  │               │ │typing│ │
│ ⊞ Detect │  │ ▲3 vs 7d   │ 9 talking │ ▲18%      │ ▲ high    │               │ ├─────┤ │
│ ⌖ Invest │  └───────────┴───────────┴───────────┴───────────┘               │ │a_07 │ │
│ ⬡ Entity │  ┌──────────────────────────────────┐ ┌────────────────────────┐ │ │reply │ │
│ ⊟ Graph  │  │ RISK INFLOW (72h)                 │ │ SCHEME MIX             │ │ ├─────┤ │
│ ▦ Analyt │  │   ▁▂▃▅▇█▇▅▃  area chart, gradient  │ │ ◐ Pyramid      48%     │ │ │a_11 │ │
│ ◎ Agents │  │   critical ─ high ─ med overlaid   │ │ ◐ Illegal cas. 31%     │ │ │idle  │ │
│ ⛁ Vault  │  └──────────────────────────────────┘ │ ◐ Phishing     14%     │ │ └─────┘ │
│ ⎙ Report │  ┌──────────────────────────────────────────────────────────┐  │ ───────  │
│ ⚙ Admin  │  │ PRIORITY QUEUE — needs analyst decision                   │  │ ALERTS  │
│          │  │  ●CRIT  @lux.invest.club   pyramid 0.94   3 agents  2m →  │  │ ⚠ contra│
│ ──────── │  │  ●HIGH  @bigwin_casino     casino  0.88   deploy?   5m →  │  │ ⚠ wallet│
│ ⊕ New    │  │  ○MED   @crypto.mentor_x   scam    0.71   review    11m→  │  │ ⓘ report│
│  case    │  │  ○MED   @passive.income…   pyramid 0.66   review    14m→  │  │  ready  │
│          │  └──────────────────────────────────────────────────────────┘  │         │
├──────────┴─────────────────────────────────────────────────────────────────┴─────────┤
│ status: ingest ⬤ healthy · models ⬤ nominal · 312 items/h · region EU-W · v0.9.2-rc   │  ← status strip
└────────────────────────────────────────────────────────────────────────────────────┘
```

**Block purposes**
- **Threat Posture KPIs** — the four numbers a lead checks in 3 seconds: caseload, swarm activity, inbound pressure, lies found. Deltas (`▲3 vs 7d`) give trend, not just state.
- **Risk Inflow chart** — temporal pressure; stacked area by severity. This is the "are we under attack" signal.
- **Scheme Mix** — composition of threats; tells the org where to invest.
- **Priority Queue** — the only *actionable* block: items demanding a human decision, sorted by risk × age. Each row is a one-click route into triage.
- **Live Ops / Alerts rail** — ambient awareness of the swarm; agents currently typing, contradictions just detected, reports ready.
- **Status strip** — system health, throughput, build. Borrowed directly from SOC consoles; signals "this is operational infrastructure, not a webapp."

**Why it reads as cybersecurity:** dark canvas, monospaced metrics, a persistent global status strip, severity dots, and a "needs decision" queue instead of a marketing-style hero. **Why it amplifies AI/investigation perception:** the *Live Ops* rail shows machines *working autonomously right now* (agents typing), and KPIs frame output as "lies found / cases run," not vanity metrics.

---

## 5. Investigation Center (the case hub)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ ◂ Investigations / CASE-2041   @lux.invest.club        ●CRITICAL  pyramid  0.94  ⬤LIVE │
│ Objective: Confirm Ponzi structure & identify operators        ⏱ 00:42:11   ⋯  Export │
├───────────────────────────────────────────────────┬────────────────────────────────┤
│  ┌── TABS ─────────────────────────────────────┐  │  CASE DOSSIER                    │
│  │ Overview · War Room · Contradictions · Graph │  │  ┌────────────────────────────┐ │
│  │ · Timeline · Evidence · Report               │  │  │ TARGET                     │ │
│  └──────────────────────────────────────────────┘  │  │ @lux.invest.club           │ │
│  CASE SUMMARY                                       │  │ TikTok · 312k · joined 4mo │ │
│  ┌──────────────────────────────────────────────┐  │  │ ⬡ 6 linked entities        │ │
│  │ Confidence  ████████████████░░  94%  ▲        │  │  └────────────────────────────┘ │
│  │ Scheme: Financial pyramid (Ponzi)             │  │  RISK FACTORS                    │
│  │ Stage: SWARM ENGAGED · 4/6 agents complete    │  │  ✓ guaranteed returns "300%"     │
│  │ Lead theory: recruit-to-earn + locked payout  │  │  ✓ recruit-to-unlock payout      │
│  └──────────────────────────────────────────────┘  │  ✓ pressure / urgency language   │
│  AGENT PROGRESS                                     │  │  ✓ off-platform payment (USDT)   │
│  ┌──────────────────────────────────────────────┐  │  ⚠ 47 contradictions detected    │
│  │ a_03 skeptic     ███████████ done   12 msgs   │  │  ────────────────────────────    │
│  │ a_07 eager       ████████░░░ live    9 msgs   │  │  NEXT BEST ACTION (AI)           │
│  │ a_11 due-dilig.  ██████████░ live   14 msgs   │  │  ▸ Deploy 2 more agents on       │
│  │ a_02 high-networth done       8 msgs          │  │    payout-mechanics angle        │
│  └──────────────────────────────────────────────┘  │  ▸ Pull wallet 0x4a..e1 history  │
│  KEY FINDINGS (auto)                                │  └──────────────────────────────┘ │
│  • Payout requires recruiting ≥3 (pyramid signal)   │                                  │
│  • Story changed: "regulated" → "offshore" (lie)    │  [ ⊕ Deploy agents ] [ ⎙ Report ]│
└───────────────────────────────────────────────────┴────────────────────────────────┘
```

**Block purposes**
- **Case header** — identity, severity, scheme class, confidence, and a *live timer* — the case is a running operation.
- **Tab bar** — the seven lenses on the case; the Center is the orchestration shell.
- **Case Summary** — the verdict-in-progress: confidence meter, scheme classification, current stage of the swarm, lead theory.
- **Agent Progress** — per-agent bars; turns the abstract "swarm" into observable, accountable workers.
- **Key Findings** — auto-surfaced bullets, each a deep link to evidence.
- **Case Dossier (right)** — target identity, enumerated risk factors (checklist = defensibility), contradiction count, and **Next Best Action** (the AI recommending the operator's next move — the strongest "this thing is thinking" signal).

**Why cyber / why AI:** the live timer + stage machine ("SWARM ENGAGED 4/6") makes it a *running investigation*, not a report. Risk factors as a verifiable checklist = forensic credibility. *Next Best Action* positions the AI as co-investigator.

---

## 6. Agent War Room

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ CASE-2041 · AGENT WAR ROOM            6 agents deployed · 4 live   ⏱  ▮▮ pause  ▷ speed │
├──────────────────────┬──────────────────────┬──────────────────────┬─────────────────┤
│ ⬤ a_03  SKEPTIC      │ ⬤ a_07  EAGER NOVICE │ ◐ a_11 DUE-DILIGENCE │ AGENT INTEL     │
│ persona: distrustful │ persona: easily sold │ persona: asks proofs │ ┌─────────────┐ │
│ goal: pricing terms  │ goal: payout speed   │ goal: legal status   │ │ Strategy map│ │
│ ───────────────────  │ ───────────────────  │ ───────────────────  │ │ a_03→terms  │ │
│ ▸suspect: "300% in   │ ▸suspect:"easy money"│ ▸a_11: "are you SEC  │ │ a_07→speed  │ │
│  60d, guaranteed"    │ ▸a_07: "how fast?"   │  registered?"        │ │ a_11→legal  │ │
│ ◂a_03: "guaranteed   │ ▸suspect:"24h after  │ ▸suspect: "fully     │ └─────────────┘ │
│  by whom?"           │  you bring 3 friends"│  regulated, EU"      │ CROSS-SIGNALS   │
│ ▸suspect: "our fund  │   ⚑ recruit-to-earn  │ ◂a_11: "license no.?"│ ⚠ "regulated"   │
│  is regulated"       │                      │ ▸suspect:"offshore,  │  vs "offshore"  │
│   ⚑ claim: regulated │ [typing··· ]         │  no number needed"   │  → CONTRADICTS  │
│ ◂a_03: "license?"    │                      │   ⚑ evasion + lie    │  a_03 vs a_11   │
│ [typing··· ]         │                      │                      │ ⚑ 7 flags live  │
├──────────────────────┴──────────────────────┴──────────────────────┴─────────────────┤
│ SWARM CONSOLE  ▸ deploy agent  ▸ inject persona  ▸ set objective   12 msgs/min · 0 errs│
└────────────────────────────────────────────────────────────────────────────────────┘
```

**Block purposes**
- **Parallel thread columns** — one per agent, each with **persona + goal** chips so the operator understands each agent's interrogation angle. Independent conversations run simultaneously (the "swarm").
- **Inline flags (`⚑`)** — the system tags manipulative claims *as they happen*: "recruit-to-earn," "evasion + lie."
- **Live "typing…" indicators** — make the autonomy visceral.
- **Cross-Signals rail** — real-time contradiction detection *across* threads ("regulated" in a_03 vs "offshore" in a_11). This is the product's magic moment.
- **Swarm Console** — director controls: deploy more agents, inject a persona, set objectives; plus throughput telemetry.

**Why cyber / why AI:** a multi-column live "war room" looks like a SOC incident bridge. Showing *independent* agents converging on the same target, with the system catching them in inconsistencies live, is the single most powerful demonstration that this is autonomous multi-agent intelligence — not a chatbot.

---

## 7. Contradiction Detection Screen (Matrix)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ CASE-2041 · CONTRADICTION MATRIX            47 contradictions   ▾filter  severity ▾    │
├────────────────────────────────────────────────────────────────────────────────────┤
│            │ a_03 skeptic │ a_07 eager │ a_11 due-dil │ a_02 hnw │  ◀ claims by topic │
│ ───────────┼──────────────┼────────────┼──────────────┼──────────┤   cell = stated   │
│ Regulation │ "regulated"  │     —      │ "offshore"   │"licensed"│   ●=hard contradict│
│            │      ●━━━━━━━━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━●         │   ○=soft / drift  │
│ Returns    │ "300%/60d"   │"easy money"│ "varies"     │"500% VIP"│                   │
│            │      ○━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━○         │                   │
│ Payout     │ "instant"    │"after 3    │ "30 day      │ "instant"│                   │
│ terms      │              │ referrals" │  lockup"     │          │                   │
│            │      ●━━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━━●              │                   │
├────────────────────────────────────────────────────────────────────────────────────┤
│ SELECTED CONTRADICTION                                              CONFIDENCE 0.97    │
│ Topic: Regulation status                                          severity ●CRITICAL  │
│ ┌────────────────────────────────────┬─────────────────────────────────────────────┐ │
│ │ a_03 · 14:02:11                     │ a_11 · 14:09:47                              │ │
│ │ "We are fully regulated in the EU." │ "We're offshore, no license number needed." │ │
│ │ ▸ play clip ▸ source msg            │ ▸ play clip ▸ source msg                     │ │
│ └────────────────────────────────────┴─────────────────────────────────────────────┘ │
│ Manipulation technique: FALSE AUTHORITY + GOALPOST SHIFT     [ + Add to Report ]      │
└────────────────────────────────────────────────────────────────────────────────────┘
```

**Block purposes**
- **Matrix grid** — topics (rows) × agents (columns); each cell holds the claim that agent extracted. Connector lines link contradicting cells; `●` hard contradiction, `○` soft/drift.
- **Selected Contradiction panel** — the two statements side by side with timestamps, confidence, severity, and **deep links to the source message/clip** (provenance = defensibility).
- **Manipulation technique tag** — names the tactic ("False Authority + Goalpost Shift").
- **Add to Report** — promotes the contradiction into the evidence dossier.

**Why cyber / why AI:** a contradiction *matrix* is a forensic/analyst artifact (think link-analysis crosstabs in Gotham). Naming manipulation techniques and quantifying contradiction confidence makes the AI's reasoning legible and prosecutable, not a black box.

---

## 8. Knowledge Graph Screen

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ CASE-2041 · KNOWLEDGE GRAPH      ◉ force  ◍ radial  ⊞ geo     filter ▾  layers ▾   ⤢   │
├───────────────────────────────────────────────────────────────────┬────────────────┤
│                            ╭───────────╮                            │ NODE INSPECTOR │
│                  ┌────────▶│ @lux.invest│◀────────┐                 │ ┌────────────┐ │
│                  │  admin  │  (TARGET)  │ promotes │                 │ │@lux.invest │ │
│            ╭─────┴────╮    ╰─────┬─────╯    ╭──────┴────╮            │ │ TARGET     │ │
│            │ @recruiter│         │ pays    │ @mentor_x  │            │ │ centrality │ │
│            │  _ana     │     ╭───┴────╮    │ (linked)   │            │ │ ████ 0.81  │ │
│            ╰─────┬────╯     │ wallet  │    ╰─────┬─────╯            │ │ 6 edges    │ │
│           victims│          │0x4a..e1 │  shares  │ phone           │ │ ───────────│ │
│            ●●●●●● ●          ╰───┬────╯  device   ●                 │ │ EVIDENCE   │ │
│          (47 inbound)            │ 3 hops to known                  │ │ 12 msgs    │ │
│                          ╭───────┴───────╮  pyramid cluster ▒▒▒     │ │ 3 clips    │ │
│                          │ exchange:Bybit │                         │ │ 1 wallet   │ │
│                          ╰───────────────╯                         │ │ ▸ open     │ │
│   legend: ⬡account ◆wallet ▢phone ●victim ▒cluster   edge=money/ref │ └────────────┘ │
├───────────────────────────────────────────────────────────────────┴────────────────┤
│ ▸ expand neighbors  ▸ shortest path  ▸ find communities  ▸ timeline scrub ◁───────▷  │
└────────────────────────────────────────────────────────────────────────────────────┘
```

**Block purposes**
- **Force/link graph** — entities as typed nodes (account ◆ wallet ▢ phone ● victim), edges typed by relation (pays / recruits / shares-device). The target is visually anchored/centered.
- **Clusters** — community detection highlights a known pyramid cluster N hops away.
- **Node Inspector** — selected node's centrality, edge count, attached evidence, with a route to the entity profile.
- **Graph tools** — expand neighbors, shortest path, find communities, and a **timeline scrubber** to animate the network's growth over time.

**Why cyber / why AI:** link analysis *is* the visual signature of Gotham / Arkham / Recorded Future. Money + recruitment edges, wallet nodes, and community detection say "financial intelligence." The timeline scrubber demonstrates the AI reconstructing a network's evolution.

---

## 9. Evidence Timeline

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ CASE-2041 · EVIDENCE TIMELINE        ◷ absolute  ⟲ relative      filter: all ▾   ⎙     │
├────────────────────────────────────────────────────────────────────────────────────┤
│  13:40 ─────●  DETECTION  video ingested · pyramid 0.94                    [clip ▸]   │
│             │  ASR + OCR extracted "300% guaranteed"                                  │
│  13:52 ─────●  CASE OPENED  objective set · 6 agents deployed                         │
│  14:02 ─────●  CLAIM (a_03)  "fully regulated in EU"            ⚑ false authority     │
│             │     └─ links to → 14:09 contradiction                                   │
│  14:09 ─────◆  CONTRADICTION  a_03 "regulated" ✕ a_11 "offshore"   ●CRIT conf .97    │
│  14:15 ─────●  CLAIM (a_07)  "payout after 3 referrals"        ⚑ recruit-to-earn      │
│  14:22 ─────◆  EVIDENCE  wallet 0x4a..e1 surfaced · 3 hops to known cluster           │
│  14:31 ─────●  TECHNIQUE  urgency/pressure detected across 3 threads                  │
│  14:42 ─────▣  MILESTONE  confidence crossed 0.90 → CRITICAL                          │
│       now ─────◔  4/6 agents complete · report draft generating…                      │
├────────────────────────────────────────────────────────────────────────────────────┤
│  ◀━━━━━━━━━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▶  scrub  13:40 ───── now        │
│  layers: ◉detections ◉claims ◉contradictions ◉evidence ◉techniques ◉milestones        │
└────────────────────────────────────────────────────────────────────────────────────┘
```

**Block purposes**
- **Vertical event spine** — chronologically ordered facts; node glyph encodes type (● claim, ◆ contradiction, ▣ milestone, ◔ in-progress).
- **Cross-links** — events reference each other ("links to → 14:09 contradiction"), reconstructing causality.
- **Scrubber + layer toggles** — replay the investigation; isolate event types; this is the "story" view used in court-style narration.

**Why cyber / why AI:** timeline reconstruction is core to incident response (Splunk/Falcon "attack story"). Showing the machine *building a chronology of proof in real time* — with confidence crossing a threshold into CRITICAL — dramatizes autonomous reasoning.

---

## 10. AI Prosecutor Report

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ CASE-2041 · AI PROSECUTOR REPORT                       ⎙ PDF  ⤓ JSON  🔗 Share  ⌥ Sign │
├──────────────┬─────────────────────────────────────────────────────────────────────┤
│ CONTENTS     │  VERDICT                                                              │
│ ▸ Verdict    │  ┌─────────────────────────────────────────────────────────────────┐ │
│ ▸ Summary    │  │ FINANCIAL PYRAMID (PONZI) — CONFIRMED          confidence 0.94   │ │
│ ▸ Evidence   │  │ Target @lux.invest.club · 6-agent swarm · 47 contradictions     │ │
│ ▸ Techniques │  │ Recommendation: ESCALATE — report to FIU + platform takedown    │ │
│ ▸ Network    │  └─────────────────────────────────────────────────────────────────┘ │
│ ▸ Timeline   │  EXECUTIVE SUMMARY                                                    │
│ ▸ Appendix   │  The target operates a recruit-to-earn structure with locked payouts │
│ ──────────── │  contingent on enrolling ≥3 members — a hallmark Ponzi mechanic. …    │
│ EVIDENCE  47 │  COUNTS / FINDINGS                                                    │
│ ●CRIT   12   │  ┌─ Count 1 ── FALSE AUTHORITY ───────────────────────── conf .97 ─┐  │
│ ●HIGH   21   │  │ Claimed "EU regulated" (a_03) then "offshore, no license"(a_11) │  │
│ ○MED    14   │  │ Exhibits: [E-04 clip] [E-09 transcript] [E-11 msg]             │  │
│              │  └────────────────────────────────────────────────────────────────┘  │
│              │  ┌─ Count 2 ── RECRUIT-TO-EARN ───────────────────────── conf .93 ─┐  │
│              │  │ Payout requires 3 referrals (a_07). Exhibits: [E-14][E-16]      │  │
│              │  └────────────────────────────────────────────────────────────────┘  │
│              │  CHAIN OF CUSTODY  ✓ 47 artifacts hashed · model v0.9.2 · analyst ✎  │
└──────────────┴─────────────────────────────────────────────────────────────────────┘
```

**Block purposes**
- **Verdict banner** — classification, confidence, and a concrete **recommendation/escalation path** (FIU report, takedown).
- **Counts/Findings** — structured like a legal indictment: each "count" names a technique, states the evidence, cites **exhibits** (deep-linked artifacts), carries its own confidence.
- **Chain of custody** — artifacts hashed, model version, analyst sign-off — the defensibility footer.
- **Export bar** — PDF/JSON/share/cryptographic sign — handoff to humans and downstream systems.

**Why cyber / why AI:** "Prosecutor report" with counts, exhibits, and chain-of-custody is the language of forensics and intelligence dossiers (Recorded Future intel reports). It frames the AI output as *evidence prepared for action*, the entire product's reason to exist.

---

## 11. Risk Analysis Dashboard

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ RISK ANALYTICS                              range 30d ▾   segment: all schemes ▾   ⎙   │
├────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─ EXPOSURE INDEX ─────────┐ ┌─ MANIPULATION TECHNIQUES (freq) ──────────────────────┐│
│ │   72 ▲  ELEVATED         │ │ urgency        ██████████████████ 312               ││
│ │   ◔ gauge                │ │ false authority██████████████ 244                   ││
│ │   blended risk score     │ │ recruit-to-earn███████████ 198                      ││
│ └──────────────────────────┘ │ guaranteed ROI ████████ 141   sunk-cost ██████ 97   ││
│ ┌─ SCHEME TREND (stacked) ─────────────────┐ └──────────────────────────────────────┘│
│ │ pyramid ▇▇▇▇  casino ▅▅▅  scam ▃▃▃         │ ┌─ COHORTS / HOTSPOTS ─────────────────┐│
│ │  area over 30d, severity color            │ │ platform   cases  conf  Δ            ││
│ └────────────────────────────────────────────┘ │ TikTok      141   .88  ▲            ││
│ ┌─ AGENT EFFICACY ─────────────────────────┐   │ Instagram    96   .82  ▲            ││
│ │ persona      win%  avg msgs  contra/case  │   │ YouTube      40   .79  ▬            ││
│ │ skeptic       74     11        3.1        │   │ ───────────────────────────────────││
│ │ due-diligence 81      9        4.4 ★      │   │ geo: EU-W 38% · MENA 21% · SEA 18%  ││
│ │ eager novice  52     14        1.2        │   └──────────────────────────────────────┘│
│ └────────────────────────────────────────────┘                                        │
└────────────────────────────────────────────────────────────────────────────────────┘
```

**Block purposes**
- **Exposure Index** — single blended org-risk gauge (the "are we exposed" number).
- **Manipulation Techniques frequency** — what tactics dominate (drives playbooks).
- **Scheme Trend** — stacked area of scheme types over time.
- **Agent Efficacy** — which personas extract the most contradictions per case (operational tuning; due-diligence persona starred as best).
- **Cohorts/Hotspots** — by platform and geography.

**Why cyber / why AI:** SOC/threat-intel dashboards quantify *the adversary* and *your own tooling's performance*. Measuring agent efficacy proves the swarm is a managed, optimizable instrument — reinforcing the autonomous-system narrative.

---

## 12. Navigation Structure

- **Top bar (global):** logo/wordmark · primary section tabs · global `⌘K` command palette · live clock · active-agent count · settings/profile. Always-on.
- **Left nav rail (icon + label, collapsible to 56px icons):** Command · Detections · Investigations · Entities · Graph · Analytics · Agents · Vault · Reports · Admin. Bottom: **⊕ New Case** primary action + system health dot.
- **In-case tab bar:** Overview · War Room · Contradictions · Graph · Timeline · Evidence · Report — context navigation *within* an investigation.
- **Right contextual panel:** inspector/dossier that changes per screen (node inspector, case dossier, live ops).
- **Command palette (`⌘K`):** jump to case, search entity, deploy agents, run report — the analyst's keyboard-first highway (Linear/Gotham pattern).
- **Breadcrumbs:** `Investigations / CASE-2041 / War Room`.

Three-zone shell (rail · canvas · contextual panel) + global top bar + status strip = the canonical intelligence-console frame.

---

## 13. Mobile Version

Mobile is **monitoring & decision**, not full investigation. Operators triage and approve on the go; deep graph/war-room work stays desktop.

```
┌───────────────────────┐   ┌───────────────────────┐
│ ◣ SwarmShield   ⌘  ⚙  │   │ ◂ CASE-2041   ●CRIT    │
│ ───────────────────── │   │ @lux.invest  0.94 ▲    │
│ THREAT  ELEVATED ▲    │   │ ───────────────────── │
│ ┌────────┬──────────┐ │   │ [Sum][War][Graph][Rep]│  ← swipeable tabs
│ │cases 23│agents 14 │ │   │ AGENTS 4/6 complete    │
│ └────────┴──────────┘ │   │ ▰▰▰▰▱▱                 │
│ PRIORITY QUEUE        │   │ ┌───────────────────┐ │
│ ●CRIT @lux.invest     │   │ │a_03 ✓ a_07 live…  │ │
│  pyramid 0.94    2m → │   │ └───────────────────┘ │
│ ●HIGH @bigwin    5m → │   │ KEY FINDINGS          │
│ ○MED  @crypto…  11m → │   │ • recruit-to-unlock   │
│ ───────────────────── │   │ • "regulated"→lie     │
│ LIVE OPS              │   │ ⚠ 47 contradictions   │
│ ⬤ a_07 typing…        │   │ ───────────────────── │
│ ⚠ contradiction found │   │ [ Approve escalate ]  │
└───────────────────────┘   └───────────────────────┘
  bottom nav: ◳ ⊞ ⌖ ▦ ◎
```

- Left nav rail → **bottom tab bar** (5 max). Right panels → **bottom sheets**.
- Tables → **stacked cards**. Graph → read-only pan/zoom snapshot with "open on desktop" CTA.
- War Room → single-column swipe between agent threads; live indicators preserved.
- Push: contradiction found, report ready, case crossed CRITICAL.

**Why:** field leads need to *approve escalation* and *stay aware*; the investigation labor is desktop-bound. This mirrors Falcon/Datadog mobile companions.

---

## 14. Dark Theme (default & primary)

Dark is the **default**, not an option — SOC rooms are dark, and dark canvases make severity color and data viz pop. A light theme exists only for printed reports.

- **Base canvas** near-black blue-tinted (`#070B11`) — not pure black (reduces halation).
- **Elevation by lightness, not shadow:** surfaces step up `#0B1119 → #0F1722 → #141E2B`; hairline borders `#1C2836`.
- **Glow as signal:** critical elements get a subtle outer glow (`box-shadow` with severity color at low alpha) — used sparingly for live/critical only.
- **Text:** primary `#E6EDF5`, secondary `#9FB0C3`, muted `#5E7governmental → #5E7387`. Monospace for all metrics/IDs/hashes.

---

## 15. Color Palette

**Primitive tokens (HSL/HEX):**

```
/* Canvas & surfaces (cool, intelligence-console) */
--bg-base       #070B11   /* app canvas            */
--bg-surface-1  #0B1119   /* cards                 */
--bg-surface-2  #0F1722   /* raised / popovers     */
--bg-surface-3  #141E2B   /* hover / active rows   */
--border-subtle #1C2836
--border-strong #2A3A4D

/* Text */
--text-primary  #E6EDF5
--text-secondary#9FB0C3
--text-muted    #5E7387

/* Brand — "shield cyan" (cold, technical, trustworthy) */
--brand-500     #2DD4BF   /* primary accent / actions   */
--brand-400     #5EEAD4
--brand-600     #14B8A6
--brand-glow    rgba(45,212,191,.25)

/* Severity / risk scale (the product's spine) */
--sev-critical  #FF3B5C   /* red-magenta, alarming      */
--sev-high      #FF8A3D   /* orange                     */
--sev-medium    #FFC53D   /* amber                      */
--sev-low       #3DD68C   /* green (safe / cleared)     */
--sev-info      #4DA3FF   /* blue (informational)       */

/* Investigation semantics */
--agent-live    #2DD4BF   /* swarm active               */
--contradiction #C264FF   /* violet — "lie detected"    */
--evidence      #4DA3FF
--manipulation  #FF8A3D

/* Data-viz categorical (graph nodes/series) */
--viz-1 #2DD4BF  --viz-2 #4DA3FF  --viz-3 #C264FF
--viz-4 #FFC53D  --viz-5 #FF8A3D  --viz-6 #FF3B5C
```

**Semantic mapping:** Red-magenta `#FF3B5C` is reserved *exclusively* for CRITICAL/confirmed-fraud — scarcity keeps it alarming. Cyan brand = system/actions = "the machine." Violet = contradictions/lies (a distinct, memorable signal unique to this product). The cool-base + hot-severity contrast is the Palantir/Falcon signature: calm infrastructure, hot threats.

---

## 16. Typography

```
Display / UI:  "Geist Sans" (already in scaffold) — geometric, neutral, technical
Mono:          "Geist Mono" — ALL numerals, IDs, hashes, timestamps, confidence, code
                (monospace numerals = instrument-panel feel; tabular alignment in tables)

Type scale (rem):
  display   2.25 / 1.1  600   page titles ("CONTRADICTION MATRIX")
  h1        1.75 / 1.2  600
  h2        1.375/ 1.25 600
  h3        1.125/ 1.3  600
  body      0.875/ 1.5  400   default UI text (14px — dense console default)
  small     0.8125/1.4  400   metadata, captions
  micro     0.6875/1.3  500   labels, chip text, axis
  mono-kpi  1.5  / 1.0  500   big metrics
  mono-data 0.8125/1.4  450   table cells, ids

Treatments:
  • Section labels: micro, UPPERCASE, letter-spacing .08em, text-muted ("LIVE OPS").
  • Confidence/score: mono, often with tabular-nums + leading sign (▲/▼).
  • Never pure-white body on pure-black; use --text-primary on --bg-base.
```

**Why:** monospace numerals everywhere = the instrument-panel/terminal heritage of Splunk/Falcon. Uppercase letter-spaced micro labels = the "telemetry" texture. 14px default body keeps density high without strain.

---

## 17. Interface Components (catalog)

shadcn/ui base, themed via tokens. Custom/extended components marked ★.

- **Severity Badge ★** — dot + label, color from `--sev-*`; sizes sm/md; pulsing variant for LIVE.
- **Confidence Meter ★** — horizontal bar + mono % + trend arrow; color ramps by value.
- **KPI Stat ★** — label (micro upper) + mono value + delta chip.
- **Agent Chip ★** — avatar/status dot + persona + state (live/idle/done); "typing…" animation.
- **Risk Score Pill ★** — scheme icon + score, severity-tinted.
- **Command Palette** (`cmdk` via shadcn) — global `⌘K`.
- **Data Table ★** (TanStack Table) — sticky header, density toggle, severity row accents, mono cells, row-hover reveal actions.
- **Graph Canvas ★** — see §20.
- **Timeline ★** — see §9.
- **Evidence Card ★** — see §18.
- **Inspector Panel ★** — right-side detail drawer.
- **Status Strip ★** — bottom system-health bar with heartbeat dots.
- **Tabs / Breadcrumb / Tooltip / Dialog / Sheet / Popover / Dropdown / Toast (Sonner) / Progress / Skeleton / Resizable panels / ScrollArea** — shadcn primitives.
- **Empty State ★**, **Loading Shell ★** — §22/§23.
- **Live Pulse Dot ★** — animated ring for active agents/critical.

State matrix for every interactive element: `default · hover · focus-visible (cyan ring) · active · disabled · loading · error`. Focus ring = `0 0 0 2px var(--brand-glow)`.

---

## 18. Cards

```
┌─ EVIDENCE CARD ──────────── E-04 ●CRIT ─┐   ┌─ DETECTION CARD ────────────────────┐
│ ▣ video clip  00:00–00:12      ▸ play   │   │ ●HIGH  @bigwin_casino               │
│ ┌────────────────────────────────────┐ │   │ ┌──────┐ illegal casino    0.88     │
│ │  [thumbnail / waveform / frame]    │ │   │ │ thumb│ TikTok · 88k · 2h ago       │
│ └────────────────────────────────────┘ │   │ └──────┘ ⚑ guaranteed wins, deposit │
│ "fully regulated in the EU"   a_03      │   │ signals: 4 · OCR ✓ ASR ✓ vision ✓   │
│ 14:02:11 · transcript ✓ · hash 9f3a…   │   │ ───────────────────────────────────│
│ ── tags: false-authority · regulation   │   │ [ Dismiss ]        [ Promote → ]    │
│ [ ▸ source ] [ + add to report ]        │   └─────────────────────────────────────┘
└──────────────────────────────────────────┘
```

**Anatomy (consistent across all cards):** severity rail (left 3px color) → header (id + severity + entity) → media/thumbnail → primary content (claim/finding) → metadata row (mono: time, hash, signals) → tag row → action footer (reveal on hover for table-embedded cards).

**Card types:** Evidence, Detection, Case (caseload grid), Agent, Entity, Finding/Count, Insight (AI "Next Best Action").

**Why:** every card is a *provenance container* — it always shows source + hash + timestamp, never a naked claim. This is what separates an investigation tool from a feed.

---

## 19. Tables

```
┌ INVESTIGATIONS ─────────────────────────────────── density ▤ ▥   ⌕ filter   ⎙ ┐
│ ▢  SEV   CASE       TARGET            SCHEME    CONF   AGENTS  CONTRA  AGE   ⋯  │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ▢ ●CRIT  CASE-2041  @lux.invest.club  pyramid   0.94   4/6 ⬤   47      42m   ⋯ │
│ ▢ ●HIGH  CASE-2039  @bigwin_casino     casino    0.88   6/6     31      3h    ⋯ │
│ ▢ ○MED   CASE-2034  @crypto.mentor_x   scam      0.71   2/4 ⬤    8      6h    ⋯ │
│ ─────────────────────────────────────────────────────────────────────────────│
│ 3 of 23 · selected 0          rows ⟨ 1 2 3 … ⟩          export csv/json        │
└────────────────────────────────────────────────────────────────────────────────┘
```

**Spec:** sticky header; left checkbox column; **severity dot as first data cell**; mono tabular numerals for CONF/AGE/counts; live agent dot inline; row hover lightens to `--bg-surface-3` and reveals `⋯` actions; sortable headers; density toggle (comfortable/compact); column show/hide; saved views; right-click context menu (open, add to watchlist, export). Empty/loading variants per §22–23. Virtualized for large sets (TanStack Virtual).

**Why:** dense, sortable, mono-aligned, severity-led tables are the analyst's primary triage surface — pure Splunk/Falcon ergonomics.

---

## 20. Graphs (network + charts)

**Network graph** (Knowledge Graph): rendered with **Cytoscape.js** (or `react-force-graph` for WebGL at scale).
- **Nodes typed by shape + color:** ⬡ account, ◆ wallet, ▢ phone/device, ● victim, ▒ cluster halo. Size ∝ centrality; target node pinned/haloed.
- **Edges typed by style:** solid=money, dashed=referral, dotted=shared-device; thickness ∝ weight; directional arrows.
- **Interactions:** hover highlights ego-network + dims rest; click → inspector; double-click expands neighbors; lasso multi-select; shortest-path mode; community detection toggle; **time scrubber** animates growth.
- **Layouts:** force-directed (default), radial (target-centric), geo (when location data).
- **Performance:** progressive loading, level-of-detail labels (hide labels when zoomed out), edge bundling for dense clusters.

**Charts** (dashboards): **Recharts** or **visx**, themed.
- Stacked area (risk inflow / scheme trend), horizontal bars (technique frequency), radial gauge (exposure index), sparthan-lines/sparklines in KPI cards, heat-matrix (contradiction matrix). Severity colors only; grid lines `--border-subtle`; mono axis labels; tooltip = dark popover with mono values.

**Why:** typed nodes/edges, centrality sizing, community detection, and temporal replay are the exact vocabulary of Gotham/Arkham link analysis — instantly legible as "intelligence," not "BI dashboard."

---

## 21. Animations

Motion = **system feedback and liveness**, never decoration. Durations short, easing crisp.

```
tokens:
  --ease-out      cubic-bezier(.16,1,.3,1)     /* enter            */
  --ease-in-out   cubic-bezier(.65,0,.35,1)    /* move             */
  --dur-fast      120ms   --dur-base 200ms   --dur-slow 320ms

patterns:
  • Live pulse:    agent/critical dot → 2s infinite ring expand+fade (the heartbeat).
  • Typing dots:   3-dot bounce in agent threads (autonomy cue).
  • Count-up:      KPIs animate to value on load (mono, 400ms, ease-out).
  • Contradiction flash: when detected, both source cells flash violet → settle (300ms).
  • Graph settle:  force layout eases to rest; new nodes scale-in 0→1.
  • Confidence fill:bar animates left→right on update.
  • Route change:  canvas cross-fade 120ms; panels slide-in from right.
  • Timeline grow: new events slide down + node draw-in as investigation runs.
  • Reduced-motion: respect prefers-reduced-motion → disable pulses/flash, keep fades.
```

**Why:** pulses, typing, and contradiction flashes make the AI feel *alive and working*. Restraint (no bouncy/playful motion) keeps the serious, operational tone.

---

## 22. Empty States

Each is purposeful, on-brand, and routes to the next action — never a shrug.

```
┌─ NO INVESTIGATIONS ─────────────────────┐   ┌─ WAR ROOM (no agents yet) ──────────┐
│            ◌                             │   │           ◎ ◎ ◎                       │
│      ⬡  ──  ⬡  ──  ⬡   (faint graph)    │   │   Swarm not deployed                 │
│   No active investigations               │   │   Deploy agents to begin             │
│   Promote a detection or start a case    │   │   independent interrogation.         │
│   [ ⊕ New investigation ]                │   │   [ ⊕ Deploy swarm ]                  │
└──────────────────────────────────────────┘   └──────────────────────────────────────┘
```

Variants: empty feed ("monitoring — 0 detections in range, ingest healthy ⬤"), no contradictions yet ("agents still gathering — 0 found"), empty graph, no evidence, no search results (with "clear filters"), first-run onboarding (connect sources). Tone: operational, confident, directive. Always show *system is healthy* so emptiness reads as "nothing to act on," not "broken."

---

## 23. Loading States

- **Skeletons matching layout** (not spinners) for tables, cards, charts — shimmer in `--bg-surface-2→3`.
- **Streaming/progressive:** War Room and Timeline stream in as agents act; show partial data immediately.
- **Staged investigation loader** (the hero loading moment when a case opens):

```
┌─ DEPLOYING SWARM ──────────────────────────────────┐
│  ⬤ Ingesting media & transcripts        ✓          │
│  ⬤ Analyzing audio · OCR · vision        ✓          │
│  ◔ Spawning 6 agents…              ▰▰▰▰▱▱  4/6      │
│  ○ Establishing contact                              │
│  ○ Cross-referencing entities                        │
│        elapsed 00:08 · est 00:30                     │
└──────────────────────────────────────────────────────┘
```

- **Inline:** confidence bar pulses while recomputing; mono "computing…" with elapsed timer.
- **Graph:** progressive node reveal with "resolving N relationships…".
- **Optimistic UI** for analyst actions (dismiss/promote) with toast confirm + undo.

**Why:** a *staged* loader that narrates "spawning agents → establishing contact → cross-referencing" sells the autonomy and gravity of the operation far better than a spinner.

---

## 24. Micro-interactions

- **Hover-to-reveal** row actions and evidence source links (keeps tables clean).
- **Click-to-trace:** clicking any finding pulses + scrolls the linked evidence/timeline node into view (cross-surface linking).
- **Copy affordances:** hover any ID/hash/wallet → copy icon + toast "copied".
- **Severity-aware focus ring:** cyan default; critical contexts shift ring to severity color.
- **Keyboard:** `⌘K` palette, `j/k` row nav, `e` add-to-report, `g` then `g` to graph, `?` shortcuts sheet.
- **Drag:** reorder report counts; drag evidence card → report.
- **Scrub feedback:** timeline/graph scrubber shows live timestamp tooltip + ghosts future state.
- **Live deltas:** numbers tick up with a subtle highlight when new data arrives.
- **Confidence hover:** shows contributing factors breakdown popover.
- **Toasts (Sonner):** "Contradiction detected (a_03 ✕ a_11)", "Report ready", "Agent a_07 completed" — routed, dismissible, with action buttons.

**Why:** click-to-trace and cross-surface linking make the evidence feel *interconnected and verifiable* — the core trust mechanic of an investigation platform.

---

# Frontend Project Structure (Next.js 16 · App Router · Tailwind v4 · shadcn/ui)

> ⚠ This repo's `AGENTS.md` warns that Next.js 16 has breaking changes vs prior versions. **Read `node_modules/next/dist/docs/` before writing route/layout/server-component code.** The structure below is conventional App Router; verify specifics (params typing, `cookies()`/`headers()` async APIs, route handlers) against the local docs.

```
src/
├── app/
│   ├── layout.tsx                     # root: fonts, theme, providers, dark default
│   ├── globals.css                    # Tailwind v4 @theme tokens (see design-tokens.css)
│   ├── page.tsx                       # redirect → /command or render Command Center
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── layout.tsx                 # centered auth shell
│   ├── (app)/                         # authenticated shell (rail + topbar + status strip)
│   │   ├── layout.tsx                 # AppShell: TopBar, NavRail, StatusStrip, <slot>
│   │   ├── command/page.tsx           # Command Center (dashboard)
│   │   ├── detections/
│   │   │   ├── page.tsx               # Detection Feed
│   │   │   └── [id]/page.tsx          # Detection Detail
│   │   ├── investigations/
│   │   │   ├── page.tsx               # Investigations list (table)
│   │   │   └── [id]/
│   │   │       ├── layout.tsx         # case header + in-case tab bar + dossier panel
│   │   │       ├── page.tsx           # Investigation Center (Overview)
│   │   │       ├── agents/page.tsx    # Agent War Room
│   │   │       ├── contradictions/page.tsx
│   │   │       ├── graph/page.tsx     # Knowledge Graph
│   │   │       ├── timeline/page.tsx  # Evidence Timeline
│   │   │       └── report/page.tsx    # AI Prosecutor Report
│   │   ├── entities/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx          # Entity Profile
│   │   ├── analytics/page.tsx         # Risk Analytics
│   │   ├── agents/page.tsx            # Agent Fleet
│   │   ├── evidence/page.tsx          # Evidence Vault
│   │   ├── reports/page.tsx
│   │   └── settings/
│   │       ├── page.tsx
│   │       ├── sources/page.tsx
│   │       ├── models/page.tsx
│   │       ├── rbac/page.tsx
│   │       └── audit/page.tsx
│   └── api/                           # route handlers (mock/stream during hackathon)
│       ├── detections/route.ts
│       ├── investigations/route.ts
│       └── agents/stream/route.ts     # SSE for live War Room
│
├── components/
│   ├── ui/                            # shadcn/ui primitives (button, dialog, table, …)
│   ├── shell/
│   │   ├── top-bar.tsx
│   │   ├── nav-rail.tsx
│   │   ├── status-strip.tsx
│   │   ├── command-palette.tsx        # cmdk ⌘K
│   │   └── inspector-panel.tsx
│   ├── data/
│   │   ├── data-table.tsx             # TanStack Table wrapper
│   │   ├── kpi-stat.tsx
│   │   ├── confidence-meter.tsx
│   │   └── severity-badge.tsx
│   ├── investigation/
│   │   ├── case-header.tsx
│   │   ├── case-dossier.tsx
│   │   ├── agent-chip.tsx
│   │   ├── agent-thread.tsx           # War Room column
│   │   ├── contradiction-matrix.tsx
│   │   ├── contradiction-detail.tsx
│   │   ├── evidence-card.tsx
│   │   ├── finding-count.tsx          # report "count"
│   │   └── next-best-action.tsx
│   ├── graph/
│   │   ├── knowledge-graph.tsx        # Cytoscape/force-graph canvas
│   │   ├── graph-controls.tsx
│   │   ├── node-inspector.tsx
│   │   └── time-scrubber.tsx
│   ├── timeline/
│   │   ├── evidence-timeline.tsx
│   │   └── timeline-event.tsx
│   ├── charts/
│   │   ├── risk-inflow-area.tsx
│   │   ├── scheme-mix.tsx
│   │   ├── technique-bars.tsx
│   │   └── exposure-gauge.tsx
│   ├── feedback/
│   │   ├── empty-state.tsx
│   │   ├── loading-shell.tsx
│   │   ├── swarm-deploy-loader.tsx    # staged loader
│   │   └── live-pulse-dot.tsx
│   └── report/
│       ├── verdict-banner.tsx
│       ├── report-toc.tsx
│       └── chain-of-custody.tsx
│
├── lib/
│   ├── utils.ts                       # cn(), formatters (mono numbers, hashes, time)
│   ├── severity.ts                    # severity↔color/label mapping
│   ├── api-client.ts
│   ├── stream.ts                      # SSE/websocket helpers for live data
│   └── graph-layout.ts
│
├── hooks/
│   ├── use-agent-stream.ts            # live War Room subscription
│   ├── use-command-palette.ts
│   ├── use-investigation.ts
│   └── use-media-query.ts
│
├── stores/                            # zustand
│   ├── investigation-store.ts
│   ├── ui-store.ts                    # rail collapse, density, theme
│   └── selection-store.ts             # graph/table selection
│
├── types/
│   ├── investigation.ts               # Investigation, Agent, Contradiction, Evidence…
│   ├── entity.ts
│   └── detection.ts
│
└── mocks/                             # hackathon seed data + scripted swarm
    ├── investigations.ts
    ├── agents-script.ts               # timed messages to fake live interrogation
    └── graph.ts
```

**Recommended dependencies**

```
shadcn/ui (radix)         # component primitives, themed via tokens
@tanstack/react-table     # dense tables
@tanstack/react-virtual   # virtualized rows
cytoscape + layout-cose   # knowledge graph (or react-force-graph for WebGL)
recharts (or @visx)       # dashboards/charts
cmdk                      # ⌘K palette
zustand                   # client state
framer-motion             # pulse/typing/flash/scrub motion (respect reduced-motion)
sonner                    # toasts
lucide-react              # icons (geometric, technical)
date-fns                  # time formatting
```

**Tailwind v4 token wiring** — extend the existing `@theme` block in `globals.css` with the palette from §15 (`--color-bg-base`, `--color-sev-critical`, …) so utilities like `bg-bg-base`, `text-sev-critical`, `ring-brand-glow` work directly. A ready-to-paste token file ships at `docs/design-tokens.css`.

**Hackathon build order (for max demo impact):**
1. AppShell (rail + topbar + status strip) + tokens + dark theme.
2. Command Center with mock KPIs + priority queue.
3. **Agent War Room with scripted live streaming** ← the demo centerpiece.
4. Contradiction Matrix + Knowledge Graph (wow factors).
5. AI Prosecutor Report (the payoff / export).
6. Timeline + Analytics polish.

Lead the demo with the War Room → live contradiction flash → graph → prosecutor report. That arc tells the autonomous-investigation story in 90 seconds.
