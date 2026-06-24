import type { KnowledgeGraph } from "@/types/graph";

/** Precomputed layout in a 0..100 x 0..100 viewBox (radial around target). */
export const caseGraph: KnowledgeGraph = {
  nodes: [
    { id: "target", label: "@lux.invest.club", type: "account", centrality: 0.81, target: true, x: 50, y: 42 },
    { id: "recruiter", label: "@recruiter_ana", type: "account", centrality: 0.54, x: 22, y: 30 },
    { id: "mentor", label: "@mentor_x", type: "account", centrality: 0.47, x: 78, y: 30 },
    { id: "wallet", label: "0x4a3f…e1", type: "wallet", centrality: 0.63, x: 50, y: 66 },
    { id: "phone", label: "+34 6•• ••• ••", type: "phone", centrality: 0.31, x: 80, y: 58 },
    { id: "exchange", label: "Bybit", type: "exchange", centrality: 0.4, x: 50, y: 88 },
    { id: "cluster", label: "Known pyramid cluster", type: "cluster", centrality: 0.7, x: 20, y: 75 },
    { id: "v1", label: "victim", type: "victim", centrality: 0.1, x: 10, y: 46 },
    { id: "v2", label: "victim", type: "victim", centrality: 0.1, x: 8, y: 56 },
    { id: "v3", label: "victim", type: "victim", centrality: 0.1, x: 14, y: 64 },
    { id: "v4", label: "victim", type: "victim", centrality: 0.1, x: 6, y: 38 },
  ],
  edges: [
    { source: "recruiter", target: "target", kind: "admin" },
    { source: "target", target: "mentor", kind: "promotes" },
    { source: "target", target: "wallet", kind: "money", weight: 3 },
    { source: "mentor", target: "phone", kind: "device" },
    { source: "wallet", target: "exchange", kind: "money", weight: 2 },
    { source: "wallet", target: "cluster", kind: "money", weight: 2 },
    { source: "recruiter", target: "v1", kind: "referral" },
    { source: "recruiter", target: "v2", kind: "referral" },
    { source: "recruiter", target: "v3", kind: "referral" },
    { source: "recruiter", target: "v4", kind: "referral" },
  ],
};
