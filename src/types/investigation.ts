import type { Severity } from "@/lib/severity";

export type SchemeType = "pyramid" | "casino" | "scam" | "phishing";

export type CaseStage =
  | "triage"
  | "swarm-engaged"
  | "analysis"
  | "report-ready";

export type AgentState = "live" | "idle" | "done" | "queued";

export type ManipulationTechnique =
  | "false-authority"
  | "recruit-to-earn"
  | "urgency"
  | "guaranteed-roi"
  | "goalpost-shift"
  | "sunk-cost"
  | "evasion";

export interface AgentPersona {
  id: string;
  name: string;
  persona: string;
  goal: string;
  state: AgentState;
  progress: number; // 0..1
  messages: number;
}

export type Speaker = "agent" | "suspect";

export interface ChatMessage {
  id: string;
  speaker: Speaker;
  text: string;
  ts: string; // HH:MM:SS
  flag?: ManipulationTechnique;
}

export interface AgentThread {
  agent: AgentPersona;
  messages: ChatMessage[];
}

export interface Contradiction {
  id: string;
  topic: string;
  severity: Severity;
  confidence: number;
  technique: ManipulationTechnique[];
  a: { agentId: string; agentName: string; ts: string; quote: string };
  b: { agentId: string; agentName: string; ts: string; quote: string };
}

export interface RiskFactor {
  label: string;
  present: boolean;
}

export interface Finding {
  id: string;
  text: string;
}

export interface TimelineEvent {
  id: string;
  ts: string;
  kind:
    | "detection"
    | "case-opened"
    | "claim"
    | "contradiction"
    | "evidence"
    | "technique"
    | "milestone"
    | "in-progress";
  title: string;
  detail?: string;
  agentName?: string;
  flag?: ManipulationTechnique;
  severity?: Severity;
  linksTo?: string;
}

export interface ReportCount {
  id: string;
  technique: ManipulationTechnique;
  confidence: number;
  summary: string;
  exhibits: string[];
  severity: Severity;
}

export interface Investigation {
  id: string;
  target: string;
  platform: "TikTok" | "Instagram" | "YouTube";
  followers: string;
  scheme: SchemeType;
  severity: Severity;
  confidence: number;
  stage: CaseStage;
  objective: string;
  leadTheory: string;
  ageMinutes: number;
  elapsed: string; // HH:MM:SS
  agentsTotal: number;
  agentsDone: number;
  contradictions: number;
  riskFactors: RiskFactor[];
  findings: Finding[];
  threads: AgentThread[];
  contradictionList: Contradiction[];
  timeline: TimelineEvent[];
  report: {
    verdict: string;
    confirmed: boolean;
    recommendation: string;
    summary: string;
    counts: ReportCount[];
  };
}
