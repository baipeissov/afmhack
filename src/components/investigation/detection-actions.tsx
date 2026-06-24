"use client";

import { useRouter } from "@/i18n/navigation";
import { useState } from "react";
import { Check, X } from "lucide-react";
import { submitDecision } from "@/lib/api";

export function DetectionActions({ itemId }: { itemId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState<"approve" | "reject" | null>(null);

  async function handle(decision: "approve" | "reject") {
    setPending(decision);
    await submitDecision(itemId, decision);
    router.refresh();
    setPending(null);
  }

  return (
    <div className="mt-3 flex gap-2 border-t border-border-subtle pt-2.5">
      <button
        disabled={pending !== null}
        onClick={() => handle("reject")}
        className="flex flex-1 items-center justify-center gap-1.5 rounded-md border border-border-strong px-2 py-1.5 text-xs text-text-muted hover:text-text-primary disabled:opacity-50"
      >
        <X className="size-3.5" /> Отклонить
      </button>
      <button
        disabled={pending !== null}
        onClick={() => handle("approve")}
        className="flex flex-1 items-center justify-center gap-1.5 rounded-md bg-brand-500 px-2 py-1.5 text-xs font-semibold text-bg-base hover:bg-brand-400 disabled:opacity-50"
      >
        <Check className="size-3.5" /> На проверку аналитику
      </button>
    </div>
  );
}
