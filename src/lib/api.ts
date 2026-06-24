import type { SchemeType } from "@/types/investigation";
import type { Severity } from "@/lib/severity";
import { confToSeverity } from "@/lib/severity";

// Сервер (Server Components) и браузер (Client Components с кнопками
// approve/reject) дёргают один и тот же FastAPI-бэкенд (api/main.py).
// На сервере используем internal URL, в браузере — public (CORS открыт
// для localhost:3000 в api/main.py).
const API_URL =
  typeof window === "undefined"
    ? process.env.API_URL ?? "http://localhost:8000"
    : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface QueueRecord {
  item_id: string;
  source: string;
  account_handle: string;
  platform: "TikTok" | "Instagram" | "YouTube";
  video_path: string;
  risk_score: number;
  risk_level: "HIGH" | "MEDIUM" | "LOW";
  top_class: string;
  top_class_ru: string;
  contributions: Record<string, number>;
  explanations: string[];
  recommendation: string;
  modalities: { asr: boolean; ocr: boolean; vision: boolean };
  discovered_at: string;
  status: "pending_review" | "approve" | "reject" | "request_review";
  analyst_comment: string | null;
}

// top_class (схема из data/label_schema.py) -> SchemeType фронта.
const CLASS_TO_SCHEME: Record<string, SchemeType> = {
  casino_betting: "casino",
  pyramid_investment: "pyramid",
  referral_network: "scam",
  urgency_pressure: "scam",
  hidden_engagement: "phishing",
  clean: "scam",
};

export function classToScheme(topClass: string): SchemeType {
  return CLASS_TO_SCHEME[topClass] ?? "scam";
}

export function riskToSeverity(riskScore: number): Severity {
  return confToSeverity(riskScore);
}

export function ageMinutesSince(isoTs: string): number {
  return Math.max(0, (Date.now() - new Date(isoTs).getTime()) / 60000);
}

export async function fetchQueue(): Promise<QueueRecord[]> {
  const res = await fetch(`${API_URL}/queue`, { cache: "no-store" });
  if (!res.ok) return [];
  return res.json();
}

export async function fetchQueueItem(itemId: string): Promise<QueueRecord | null> {
  const res = await fetch(`${API_URL}/queue/${itemId}`, { cache: "no-store" });
  if (!res.ok) return null;
  const data = await res.json();
  if (data.error) return null;
  return data;
}

export async function submitDecision(
  itemId: string,
  decision: "approve" | "reject" | "request_review",
  analystComment?: string
): Promise<void> {
  await fetch(`${API_URL}/queue/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: itemId, decision, analyst_comment: analystComment }),
  });
}

export async function analyzeVideo(formData: FormData): Promise<QueueRecord> {
  const res = await fetch(`${API_URL}/analyze`, { method: "POST", body: formData });
  if (!res.ok) throw new Error(`analyze failed: ${res.status}`);
  return res.json();
}
