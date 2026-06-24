import type { ChatMessage, ManipulationTechnique } from "@/types/investigation";

export interface ScriptStep {
  /** ms delay AFTER the previous step before this message appears */
  delay: number;
  agentId: string;
  message: Omit<ChatMessage, "id">;
  /** if set, emits a cross-thread contradiction signal when this lands */
  contradiction?: { id: string; topic: string; with: string; quote: string };
}

/** Three agents interrogate the suspect in parallel; timeline interleaves them. */
export const agentScript: ScriptStep[] = [
  { delay: 600, agentId: "a_03", message: { speaker: "suspect", text: "300% in 60 days, guaranteed.", ts: "14:01:40" } },
  { delay: 900, agentId: "a_07", message: { speaker: "suspect", text: "It's easy money, anyone can do it.", ts: "14:01:52" } },
  { delay: 1000, agentId: "a_03", message: { speaker: "agent", text: "Guaranteed by whom?", ts: "14:01:58" } },
  { delay: 1100, agentId: "a_11", message: { speaker: "agent", text: "Are you SEC registered?", ts: "14:02:05" } },
  {
    delay: 1200,
    agentId: "a_03",
    message: { speaker: "suspect", text: "Our fund is fully regulated in the EU.", ts: "14:02:11", flag: "false-authority" },
  },
  { delay: 900, agentId: "a_07", message: { speaker: "agent", text: "How fast do I get paid?", ts: "14:02:20" } },
  { delay: 1300, agentId: "a_03", message: { speaker: "agent", text: "Which license number?", ts: "14:02:30" } },
  {
    delay: 1400,
    agentId: "a_11",
    message: { speaker: "suspect", text: "We're offshore, no license number needed.", ts: "14:02:47", flag: "goalpost-shift" },
    contradiction: { id: "c1", topic: "Regulation status", with: "a_03", quote: '"regulated" ✕ "offshore"' },
  },
  {
    delay: 1100,
    agentId: "a_07",
    message: { speaker: "suspect", text: "Within 24h — after you bring 3 friends in.", ts: "14:03:01", flag: "recruit-to-earn" },
  },
  { delay: 1000, agentId: "a_11", message: { speaker: "agent", text: "You told my colleague you were EU regulated.", ts: "14:03:10" } },
  {
    delay: 1300,
    agentId: "a_11",
    message: { speaker: "suspect", text: "Same thing. Stop asking questions and invest now.", ts: "14:03:40", flag: "urgency" },
  },
];

export const techniqueLabels: Record<ManipulationTechnique, string> = {
  "false-authority": "False authority",
  "recruit-to-earn": "Recruit-to-earn",
  urgency: "Urgency / pressure",
  "guaranteed-roi": "Guaranteed ROI",
  "goalpost-shift": "Goalpost shift",
  "sunk-cost": "Sunk cost",
  evasion: "Evasion",
};
