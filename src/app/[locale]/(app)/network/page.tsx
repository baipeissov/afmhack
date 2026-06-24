"use client";

import { toast } from "sonner";
import NetworkGraph from "@/components/graph/NetworkGraph";

type AccountNode = {
  id: string;
  platform: "tiktok" | "instagram";
  risk_score: number;
};

export default function NetworkPage() {
  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <div>
        <h1 className="text-lg font-semibold tracking-tight text-text-primary">
          Сеть аккаунтов
        </h1>
        <p className="mt-0.5 text-sm text-text-secondary">
          Связи между аккаунтами соцсетей по общим сигналам. Один Telegram-канал
          может объединять несколько внешне независимых аккаунтов в единую схему.
        </p>
      </div>

      <div className="min-h-0 flex-1">
        <NetworkGraph
          onOpenCase={(node: AccountNode) =>
            toast.success(`Карточка кейса: @${node.id}`, {
              description: `Риск ${node.risk_score.toFixed(2)} · ${node.platform}`,
            })
          }
          onLaunchProbe={(node: AccountNode) =>
            toast(`Зондировщик запущен по @${node.id}`, {
              description: "Активный сбор доказательств начат.",
            })
          }
        />
      </div>
    </div>
  );
}
