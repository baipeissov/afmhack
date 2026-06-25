"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import NetworkGraph from "@/components/graph/NetworkGraph";
import { fetchNetwork, type NetworkGraphData } from "@/lib/api";

type AccountNode = {
  id: string;
  platform: "tiktok" | "instagram";
  risk_score: number;
};

// Реальный граф из очереди показываем только когда в нём есть хоть одна
// связь — иначе аналитик увидит пустой/одноточечный граф ещё до того, как
// Collector наберёт достаточно видео, и решит, что фича не работает.
function isUsable(data: NetworkGraphData | null): data is NetworkGraphData {
  return !!data && data.nodes.length >= 2 && data.links.length >= 1;
}

export default function NetworkPage() {
  const [live, setLive] = useState<NetworkGraphData | null>(null);

  useEffect(() => {
    fetchNetwork().then(setLive);
  }, []);

  const usingLiveData = isUsable(live);

  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-text-primary">
            Сеть аккаунтов
          </h1>
          <p className="mt-0.5 text-sm text-text-secondary">
            Связи между аккаунтами соцсетей по общим сигналам. Один Telegram-канал
            может объединять несколько внешне независимых аккаунтов в единую схему.
          </p>
        </div>
        {!usingLiveData && (
          <span className="shrink-0 rounded border border-border-strong px-2 py-1 text-[11px] text-text-muted">
            демо-данные · очередь пока не даёт связей
          </span>
        )}
      </div>

      <div className="min-h-0 flex-1">
        <NetworkGraph
          {...(usingLiveData
            ? {
                nodes: live.nodes.map((n) => ({
                  ...n,
                  followers: n.followers ?? 0,
                  created_at: n.created_at ?? "",
                })),
                links: live.links,
              }
            : {})}
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
