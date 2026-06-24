import type { SchemeType } from "@/types/investigation";
import type { Severity } from "@/lib/severity";

export interface Detection {
  id: string;
  handle: string;
  platform: "TikTok" | "Instagram" | "YouTube";
  followers: string;
  scheme: SchemeType;
  severity: Severity;
  confidence: number;
  ageMinutes: number;
  signals: number;
  modalities: { ocr: boolean; asr: boolean; vision: boolean };
  flag: string;
}

export const detections: Detection[] = [
  { id: "DET-9912", handle: "@lux.invest.club", platform: "TikTok", followers: "312k", scheme: "pyramid", severity: "critical", confidence: 0.94, ageMinutes: 2, signals: 5, modalities: { ocr: true, asr: true, vision: true }, flag: "guaranteed 300%, recruit-to-earn" },
  { id: "DET-9908", handle: "@bigwin_casino", platform: "TikTok", followers: "88k", scheme: "casino", severity: "high", confidence: 0.88, ageMinutes: 5, signals: 4, modalities: { ocr: true, asr: true, vision: true }, flag: "guaranteed wins, deposit bonus" },
  { id: "DET-9901", handle: "@crypto.mentor_x", platform: "Instagram", followers: "44k", scheme: "scam", severity: "medium", confidence: 0.71, ageMinutes: 11, signals: 3, modalities: { ocr: true, asr: false, vision: true }, flag: "fake testimonials" },
  { id: "DET-9897", handle: "@passive.income.daily", platform: "Instagram", followers: "120k", scheme: "pyramid", severity: "medium", confidence: 0.66, ageMinutes: 14, signals: 3, modalities: { ocr: true, asr: true, vision: false }, flag: "downline earnings screenshots" },
  { id: "DET-9890", handle: "@fx.signals.pro", platform: "YouTube", followers: "61k", scheme: "scam", severity: "high", confidence: 0.83, ageMinutes: 21, signals: 4, modalities: { ocr: false, asr: true, vision: true }, flag: "VIP signal group, upfront fee" },
  { id: "DET-9885", handle: "@golden.roulette", platform: "TikTok", followers: "33k", scheme: "casino", severity: "low", confidence: 0.42, ageMinutes: 38, signals: 2, modalities: { ocr: true, asr: false, vision: true }, flag: "off-platform link" },
];
