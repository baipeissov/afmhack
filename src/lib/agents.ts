// Клиент к агентному слою СУНКАР (FastAPI api/main.py, роутер agents/routes.py).
// Все вызовы из браузера (Client Components) — CORS открыт для localhost:3000.

const API_URL =
  typeof window === "undefined"
    ? process.env.API_URL ?? "http://localhost:8000"
    : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function postJSON<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export interface AgentsHealth {
  status: string;
  llm_available: boolean;
  llm_models: string[];
  network_nodes: number;
  dataset: { curated_text_rows: number; labeled_videos: number };
}

export async function agentsHealth(): Promise<AgentsHealth | null> {
  try {
    const res = await fetch(`${API_URL}/agents/health`, { cache: "no-store" });
    return res.ok ? res.json() : null;
  } catch {
    return null;
  }
}

// ── liaison ──
export interface LiaisonAnswer {
  ok: boolean;
  answer: string;
  llm_used?: boolean;
  model?: string;
}

export function liaisonChat(
  itemId: string,
  question: string,
  history?: { role: string; content: string }[]
): Promise<LiaisonAnswer> {
  return postJSON(`/liaison/${itemId}/chat`, { question, history });
}

export async function downloadReport(itemId: string, analyst: string): Promise<string> {
  const res = await fetch(`${API_URL}/liaison/${itemId}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analyst }),
  });
  if (!res.ok) throw new Error(`report -> ${res.status}`);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

// ── engagement ──
export interface EngagementMessage {
  from: "investigator" | "fraudster";
  text: string;
  status?: string;
  approved_by?: string;
  simulated?: boolean;
  ts: string;
}
export interface Conversation {
  case_id: string;
  scheme?: string;
  persona?: { name?: string; legend?: string; goals?: string[] };
  transport?: string;
  status?: string;
  messages: EngagementMessage[];
  pending_draft?: { text: string; ts: string; kind?: string } | null;
  intelligence?: Record<string, unknown> | null;
}

export const engagement = {
  start: (id: string) => postJSON<{ ok: boolean; convo?: Conversation; reason?: string }>(`/engagement/${id}/start`),
  draftNext: (id: string) => postJSON<{ ok: boolean; pending_draft?: { text: string } }>(`/engagement/${id}/draft-next`),
  approve: (id: string, analyst: string, edited_text?: string) =>
    postJSON<{ ok: boolean; sent: boolean; reply?: string; simulated?: boolean }>(`/engagement/${id}/approve`, { analyst, edited_text }),
  reject: (id: string, analyst: string) => postJSON<{ ok: boolean }>(`/engagement/${id}/reject`, { analyst }),
  summarize: (id: string) => postJSON<{ ok: boolean; intelligence?: Record<string, unknown> }>(`/engagement/${id}/summarize`),
  async get(id: string): Promise<Conversation | null> {
    const res = await fetch(`${API_URL}/engagement/${id}`, { cache: "no-store" });
    return res.ok ? res.json() : null;
  },
};
