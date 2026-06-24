import type { Investigation } from "@/types/investigation";

const case2041: Investigation = {
  id: "CASE-2041",
  target: "@lux.invest.club",
  platform: "TikTok",
  followers: "312k",
  scheme: "pyramid",
  severity: "critical",
  confidence: 0.94,
  stage: "swarm-engaged",
  objective: "Confirm Ponzi structure & identify operators",
  leadTheory: "recruit-to-earn + locked payout",
  ageMinutes: 42,
  elapsed: "00:42:11",
  agentsTotal: 6,
  agentsDone: 4,
  contradictions: 47,
  riskFactors: [
    { label: 'Guaranteed returns "300% in 60d"', present: true },
    { label: "Recruit-to-unlock payout", present: true },
    { label: "Pressure / urgency language", present: true },
    { label: "Off-platform payment (USDT)", present: true },
    { label: "No verifiable license", present: true },
  ],
  findings: [
    { id: "f1", text: "Payout requires recruiting ≥3 members (pyramid signal)" },
    { id: "f2", text: 'Story changed: "regulated" → "offshore" (contradiction)' },
    { id: "f3", text: "Funds routed off-platform to USDT wallet 0x4a3f…e1" },
    { id: "f4", text: "Urgency/pressure tactics detected across 3 agent threads" },
  ],
  threads: [
    {
      agent: { id: "a_03", name: "a_03", persona: "Skeptic", goal: "pricing terms", state: "done", progress: 1, messages: 12 },
      messages: [
        { id: "m1", speaker: "suspect", text: "300% in 60 days, guaranteed.", ts: "14:01:40" },
        { id: "m2", speaker: "agent", text: "Guaranteed by whom?", ts: "14:01:58" },
        { id: "m3", speaker: "suspect", text: "Our fund is fully regulated in the EU.", ts: "14:02:11", flag: "false-authority" },
        { id: "m4", speaker: "agent", text: "Which license number?", ts: "14:02:30" },
        { id: "m5", speaker: "suspect", text: "You don't need to worry about that, returns speak for themselves.", ts: "14:02:55", flag: "evasion" },
      ],
    },
    {
      agent: { id: "a_07", name: "a_07", persona: "Eager novice", goal: "payout speed", state: "live", progress: 0.7, messages: 9 },
      messages: [
        { id: "m1", speaker: "suspect", text: "It's easy money, anyone can do it.", ts: "14:14:02" },
        { id: "m2", speaker: "agent", text: "How fast do I get paid?", ts: "14:14:20" },
        { id: "m3", speaker: "suspect", text: "Within 24h — after you bring 3 friends in.", ts: "14:15:01", flag: "recruit-to-earn" },
      ],
    },
    {
      agent: { id: "a_11", name: "a_11", persona: "Due-diligence", goal: "legal status", state: "live", progress: 0.85, messages: 14 },
      messages: [
        { id: "m1", speaker: "agent", text: "Are you SEC registered?", ts: "14:08:55" },
        { id: "m2", speaker: "suspect", text: "We're offshore, no license number needed.", ts: "14:09:47", flag: "goalpost-shift" },
        { id: "m3", speaker: "agent", text: "You told my colleague you were EU regulated.", ts: "14:10:10" },
        { id: "m4", speaker: "suspect", text: "Same thing. Stop asking questions and invest.", ts: "14:10:40", flag: "urgency" },
      ],
    },
    {
      agent: { id: "a_02", name: "a_02", persona: "High-net-worth", goal: "VIP terms", state: "done", progress: 1, messages: 8 },
      messages: [
        { id: "m1", speaker: "agent", text: "I can deposit 50k. What's my rate?", ts: "14:20:00" },
        { id: "m2", speaker: "suspect", text: "VIP tier: 500%. Licensed and insured.", ts: "14:20:33", flag: "guaranteed-roi" },
      ],
    },
  ],
  contradictionList: [
    {
      id: "c1",
      topic: "Regulation status",
      severity: "critical",
      confidence: 0.97,
      technique: ["false-authority", "goalpost-shift"],
      a: { agentId: "a_03", agentName: "a_03", ts: "14:02:11", quote: "We are fully regulated in the EU." },
      b: { agentId: "a_11", agentName: "a_11", ts: "14:09:47", quote: "We're offshore, no license number needed." },
    },
    {
      id: "c2",
      topic: "Payout terms",
      severity: "high",
      confidence: 0.91,
      technique: ["recruit-to-earn"],
      a: { agentId: "a_03", agentName: "a_03", ts: "14:03:10", quote: "Payout is instant." },
      b: { agentId: "a_07", agentName: "a_07", ts: "14:15:01", quote: "Within 24h after you bring 3 friends." },
    },
    {
      id: "c3",
      topic: "Returns",
      severity: "medium",
      confidence: 0.74,
      technique: ["guaranteed-roi"],
      a: { agentId: "a_03", agentName: "a_03", ts: "14:01:40", quote: "300% in 60 days." },
      b: { agentId: "a_02", agentName: "a_02", ts: "14:20:33", quote: "VIP tier: 500%." },
    },
  ],
  timeline: [
    { id: "t1", ts: "13:40", kind: "detection", title: "Video ingested · pyramid 0.94", detail: 'ASR + OCR extracted "300% guaranteed"', severity: "critical" },
    { id: "t2", ts: "13:52", kind: "case-opened", title: "Case opened · objective set · 6 agents deployed" },
    { id: "t3", ts: "14:02", kind: "claim", title: '"fully regulated in EU"', agentName: "a_03", flag: "false-authority", linksTo: "t4" },
    { id: "t4", ts: "14:09", kind: "contradiction", title: 'a_03 "regulated" ✕ a_11 "offshore"', severity: "critical", detail: "confidence 0.97" },
    { id: "t5", ts: "14:15", kind: "claim", title: '"payout after 3 referrals"', agentName: "a_07", flag: "recruit-to-earn" },
    { id: "t6", ts: "14:22", kind: "evidence", title: "Wallet 0x4a3f…e1 surfaced · 3 hops to known cluster", severity: "high" },
    { id: "t7", ts: "14:31", kind: "technique", title: "Urgency/pressure detected across 3 threads", flag: "urgency" },
    { id: "t8", ts: "14:42", kind: "milestone", title: "Confidence crossed 0.90 → CRITICAL", severity: "critical" },
    { id: "t9", ts: "now", kind: "in-progress", title: "4/6 agents complete · report draft generating…" },
  ],
  report: {
    verdict: "FINANCIAL PYRAMID (PONZI) — CONFIRMED",
    confirmed: true,
    recommendation: "ESCALATE — report to FIU + request platform takedown",
    summary:
      "The target operates a recruit-to-earn structure with locked payouts contingent on enrolling at least three members — a hallmark Ponzi mechanic. Across a 6-agent swarm, the operator gave mutually exclusive accounts of its regulatory status and payout terms, and consistently deployed urgency and false-authority tactics to suppress due diligence.",
    counts: [
      { id: "ct1", technique: "false-authority", confidence: 0.97, severity: "critical", summary: 'Claimed "EU regulated" (a_03) then "offshore, no license" (a_11).', exhibits: ["E-04", "E-09", "E-11"] },
      { id: "ct2", technique: "recruit-to-earn", confidence: 0.93, severity: "high", summary: "Payout requires recruiting 3 members (a_07).", exhibits: ["E-14", "E-16"] },
      { id: "ct3", technique: "guaranteed-roi", confidence: 0.88, severity: "high", summary: 'Promised "300%/60d" and "500% VIP" guaranteed returns.', exhibits: ["E-02", "E-21"] },
    ],
  },
};

export const investigations: Investigation[] = [case2041];

export function getInvestigation(id: string): Investigation | undefined {
  return investigations.find((i) => i.id === id);
}

/**
 * Demo resolver: every case row should open a full workspace. Returns the
 * showcase investigation as-is for CASE-2041, otherwise adapts its header
 * fields from the lightweight row so other cases are navigable too.
 */
export function getCaseForDisplay(id: string): Investigation | undefined {
  const exact = getInvestigation(id);
  if (exact) return exact;
  const row = caseRows.find((r) => r.id === id);
  if (!row) return undefined;
  return {
    ...case2041,
    id: row.id,
    target: row.target,
    scheme: row.scheme,
    severity: row.severity,
    confidence: row.confidence,
    agentsDone: row.agentsDone,
    agentsTotal: row.agentsTotal,
    contradictions: row.contradictions,
    ageMinutes: row.ageMinutes,
  };
}

/** Lightweight rows for the caseload table & dashboard queue. */
export interface CaseRow {
  id: string;
  target: string;
  scheme: Investigation["scheme"];
  severity: Investigation["severity"];
  confidence: number;
  agentsDone: number;
  agentsTotal: number;
  agentsLive: boolean;
  contradictions: number;
  ageMinutes: number;
}

export const caseRows: CaseRow[] = [
  { id: "CASE-2041", target: "@lux.invest.club", scheme: "pyramid", severity: "critical", confidence: 0.94, agentsDone: 4, agentsTotal: 6, agentsLive: true, contradictions: 47, ageMinutes: 42 },
  { id: "CASE-2039", target: "@bigwin_casino", scheme: "casino", severity: "high", confidence: 0.88, agentsDone: 6, agentsTotal: 6, agentsLive: false, contradictions: 31, ageMinutes: 180 },
  { id: "CASE-2034", target: "@crypto.mentor_x", scheme: "scam", severity: "medium", confidence: 0.71, agentsDone: 2, agentsTotal: 4, agentsLive: true, contradictions: 8, ageMinutes: 360 },
  { id: "CASE-2031", target: "@passive.income.daily", scheme: "pyramid", severity: "medium", confidence: 0.66, agentsDone: 3, agentsTotal: 3, agentsLive: false, contradictions: 12, ageMinutes: 840 },
  { id: "CASE-2028", target: "@fx.signals.pro", scheme: "scam", severity: "high", confidence: 0.83, agentsDone: 5, agentsTotal: 5, agentsLive: false, contradictions: 19, ageMinutes: 1440 },
];
