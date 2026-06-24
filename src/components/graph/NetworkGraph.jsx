"use client";

/**
 * NetworkGraph — рабочее место следователя по сетям мошеннических аккаунтов.
 *
 * Граф соц-аккаунтов (TikTok / Instagram), окрашенных по risk_score, связанных
 * общими сигналами (Telegram-канал, реф-ссылка, хэштег, телефон).
 * Ключевой инсайт: один Telegram-канал t.me/quick_profit_kz объединяет несколько
 * внешне независимых аккаунтов в единую схему.
 *
 * Инструменты следователя:
 *  • Поиск по @handle, центрирование на узле
 *  • Фильтры: риск, платформа, класс нарушения, только во флаге
 *  • Заметки, статус расследования и теги по каждому аккаунту (хранятся локально)
 *  • Добавление в кейс (закладки) и экспорт кейса в JSON
 *  • Инструмент «путь между аккаунтами» (как связаны два аккаунта)
 *  • PageRank — поиск центрального аккаунта схемы
 *  • Управление раскладкой: расстояние между узлами, «уместить», сброс
 *
 * Next.js App Router: компонент клиентский, ForceGraph2D грузится через
 * next/dynamic (ssr:false), т.к. тянет canvas/window.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { forceCollide } from "d3-force-3d";

const ForceGraphCanvas = dynamic(() => import("./ForceGraphCanvas"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center text-sm text-text-muted">
      Загрузка графа…
    </div>
  ),
});

/* ─────────────────────────  справочники  ───────────────────────── */

const RISK_BANDS = [
  { max: 0.3, color: "#1D9E75", label: "Низкий" },
  { max: 0.6, color: "#EF9F27", label: "Средний" },
  { max: 0.8, color: "#E24B4A", label: "Высокий" },
  { max: 1.01, color: "#A32D2D", label: "Критический" },
];
function riskColor(r) {
  for (const b of RISK_BANDS) if (r < b.max) return b.color;
  return "#A32D2D";
}
function riskLabel(r) {
  for (const b of RISK_BANDS) if (r < b.max) return b.label;
  return "Критический";
}

const VIOLATION_RU = {
  casino_betting: "Казино / ставки",
  pyramid_investment: "Финансовая пирамида",
  referral_network: "Реферальная сеть",
  urgency_pressure: "Давление срочности",
  hidden_engagement: "Накрутка / скрытая вовлечённость",
  clean: "Нарушений не выявлено",
};
const VIOLATION_COLOR = {
  casino_betting: "#E24B4A",
  pyramid_investment: "#A32D2D",
  referral_network: "#EF9F27",
  urgency_pressure: "#C77DFF",
  hidden_engagement: "#6B7280",
  clean: "#1D9E75",
};

const LINK_STYLE = {
  shared_telegram: { color: "#2AABEE", label: "Общий Telegram" },
  shared_referral_link: { color: "#EF9F27", label: "Общая реф-ссылка" },
  shared_hashtag: { color: "#B6BAC2", label: "Общий хэштег" },
  shared_phone: { color: "#A855F7", label: "Общий телефон" },
};

// статусы расследования по аккаунту
const STATUSES = {
  new: { label: "Новый", color: "#9fa1a7" },
  review: { label: "На проверке", color: "#266df0" },
  confirmed: { label: "Подтверждено", color: "#d92d20" },
  escalated: { label: "Эскалировано", color: "#7f56d9" },
  dismissed: { label: "Ложное", color: "#16a34a" },
};

const GOLD = "#E6B33E";
const PATH_COLOR = "#7f56d9";
const STORAGE_KEY = "afm.network.annotations.v1";

/* ─────────────────────────  демо-данные  ───────────────────────── */

const TELEGRAM = "t.me/quick_profit_kz";

const DEMO_NODES = [
  { id: "quick_profit_official", platform: "tiktok", risk_score: 0.95, violation_class: "pyramid_investment", followers: 210000, created_at: "2024-09-12", telegram: TELEGRAM },
  { id: "easy_earn_kz", platform: "tiktok", risk_score: 0.92, violation_class: "pyramid_investment", followers: 145000, created_at: "2024-10-03", telegram: TELEGRAM },
  { id: "casino_win_astana", platform: "instagram", risk_score: 0.88, violation_class: "casino_betting", followers: 98000, created_at: "2024-08-21", telegram: TELEGRAM },
  { id: "bet_master_kz", platform: "tiktok", risk_score: 0.84, violation_class: "casino_betting", followers: 67000, created_at: "2024-11-15", telegram: TELEGRAM },
  { id: "invest_pro_almaty", platform: "instagram", risk_score: 0.81, violation_class: "pyramid_investment", followers: 54000, created_at: "2024-10-29", telegram: TELEGRAM },
  { id: "crypto_almaty", platform: "tiktok", risk_score: 0.77, violation_class: "pyramid_investment", followers: 41000, created_at: "2025-01-08" },
  { id: "referral_king_kz", platform: "tiktok", risk_score: 0.72, violation_class: "referral_network", followers: 33000, created_at: "2024-12-19" },
  { id: "money_boost_kz", platform: "instagram", risk_score: 0.68, violation_class: "referral_network", followers: 21000, created_at: "2025-02-02" },
  { id: "flash_sale_kz", platform: "tiktok", risk_score: 0.58, violation_class: "urgency_pressure", followers: 26000, created_at: "2025-01-22" },
  { id: "astana_deals", platform: "instagram", risk_score: 0.55, violation_class: "urgency_pressure", followers: 18000, created_at: "2025-02-14" },
  { id: "boost_followers_kz", platform: "tiktok", risk_score: 0.52, violation_class: "hidden_engagement", followers: 15000, created_at: "2025-03-01" },
  { id: "hidden_likes_kz", platform: "instagram", risk_score: 0.49, violation_class: "hidden_engagement", followers: 12000, created_at: "2025-03-10" },
  { id: "travel_kazakhstan", platform: "instagram", risk_score: 0.18, violation_class: "clean", followers: 64000, created_at: "2023-06-04" },
  { id: "lifestyle_astana", platform: "instagram", risk_score: 0.12, violation_class: "clean", followers: 88000, created_at: "2023-02-17" },
  { id: "food_blogger_kz", platform: "tiktok", risk_score: 0.08, violation_class: "clean", followers: 120000, created_at: "2022-11-28" },
];

const DEMO_LINKS = [
  { source: "quick_profit_official", target: "easy_earn_kz", link_type: "shared_telegram", strength: 0.95 },
  { source: "quick_profit_official", target: "casino_win_astana", link_type: "shared_telegram", strength: 0.9 },
  { source: "quick_profit_official", target: "bet_master_kz", link_type: "shared_telegram", strength: 0.85 },
  { source: "quick_profit_official", target: "invest_pro_almaty", link_type: "shared_telegram", strength: 0.88 },
  { source: "easy_earn_kz", target: "casino_win_astana", link_type: "shared_telegram", strength: 0.7 },
  { source: "bet_master_kz", target: "invest_pro_almaty", link_type: "shared_telegram", strength: 0.66 },
  { source: "crypto_almaty", target: "quick_profit_official", link_type: "shared_phone", strength: 0.72 },
  { source: "crypto_almaty", target: "invest_pro_almaty", link_type: "shared_hashtag", strength: 0.5 },
  { source: "referral_king_kz", target: "easy_earn_kz", link_type: "shared_referral_link", strength: 0.6 },
  { source: "referral_king_kz", target: "money_boost_kz", link_type: "shared_referral_link", strength: 0.75 },
  { source: "money_boost_kz", target: "astana_deals", link_type: "shared_referral_link", strength: 0.4 },
  { source: "flash_sale_kz", target: "astana_deals", link_type: "shared_hashtag", strength: 0.55 },
  { source: "boost_followers_kz", target: "flash_sale_kz", link_type: "shared_hashtag", strength: 0.45 },
  { source: "hidden_likes_kz", target: "boost_followers_kz", link_type: "shared_phone", strength: 0.6 },
  { source: "hidden_likes_kz", target: "referral_king_kz", link_type: "shared_phone", strength: 0.5 },
  { source: "lifestyle_astana", target: "food_blogger_kz", link_type: "shared_hashtag", strength: 0.3 },
  { source: "travel_kazakhstan", target: "lifestyle_astana", link_type: "shared_hashtag", strength: 0.25 },
];

/* ─────────────────────────  утилиты графа  ───────────────────────── */

const endId = (e) => (typeof e === "object" && e !== null ? e.id : e);
const keyOf = (a, b) => (a < b ? `${a}|${b}` : `${b}|${a}`);
const nodeRadius = (n) => Math.max(6, Math.sqrt(n.followers) / 10);

function buildAdjacency(nodes, links) {
  const adj = {};
  nodes.forEach((n) => (adj[n.id] = []));
  links.forEach((l) => {
    const s = endId(l.source);
    const t = endId(l.target);
    if (adj[s] && adj[t]) {
      adj[s].push({ to: t, w: l.strength ?? 1 });
      adj[t].push({ to: s, w: l.strength ?? 1 });
    }
  });
  return adj;
}

// Взвешенный неориентированный PageRank.
function pageRank(nodes, links, { iterations = 50, damping = 0.85 } = {}) {
  const ids = nodes.map((n) => n.id);
  const N = ids.length;
  const rank = {};
  const adj = buildAdjacency(nodes, links);
  ids.forEach((id) => (rank[id] = 1 / N));
  for (let it = 0; it < iterations; it++) {
    const next = {};
    ids.forEach((id) => (next[id] = (1 - damping) / N));
    ids.forEach((id) => {
      const edges = adj[id];
      const total = edges.reduce((a, e) => a + e.w, 0);
      if (total === 0) ids.forEach((j) => (next[j] += (damping * rank[id]) / N));
      else edges.forEach((e) => (next[e.to] += damping * rank[id] * (e.w / total)));
    });
    ids.forEach((id) => (rank[id] = next[id]));
  }
  return rank;
}

// BFS — кратчайший путь между двумя аккаунтами.
function shortestPath(nodes, links, aId, bId) {
  if (aId === bId) return null;
  const adj = buildAdjacency(nodes, links);
  const prev = {};
  const seen = new Set([aId]);
  const q = [aId];
  while (q.length) {
    const cur = q.shift();
    if (cur === bId) break;
    for (const { to } of adj[cur]) {
      if (!seen.has(to)) {
        seen.add(to);
        prev[to] = cur;
        q.push(to);
      }
    }
  }
  if (!seen.has(bId)) return null;
  const path = [];
  let c = bId;
  while (c !== undefined) {
    path.unshift(c);
    c = prev[c];
  }
  const nodeIds = new Set(path);
  const linkKeys = new Set();
  for (let i = 0; i < path.length - 1; i++) linkKeys.add(keyOf(path[i], path[i + 1]));
  return { path, nodeIds, linkKeys, hops: path.length - 1 };
}

/* ─────────────────────────  компонент  ───────────────────────── */

export default function NetworkGraph({
  nodes = DEMO_NODES,
  links = DEMO_LINKS,
  onOpenCase,
  onLaunchProbe,
}) {
  const graphData = useMemo(
    () => ({ nodes: nodes.map((n) => ({ ...n })), links: links.map((l) => ({ ...l })) }),
    [nodes, links]
  );

  const fgRef = useRef(null);
  const [ready, setReady] = useState(false);
  const didFit = useRef(false);

  // выбор / панель
  const [selected, setSelected] = useState(null);
  const [caseOpen, setCaseOpen] = useState(false);

  // PageRank
  const [topCentral, setTopCentral] = useState([]);
  const topIds = useMemo(() => new Set(topCentral.map((t) => t.id)), [topCentral]);

  // поиск
  const [search, setSearch] = useState("");
  const searchMatches = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return new Set();
    return new Set(graphData.nodes.filter((n) => n.id.toLowerCase().includes(q)).map((n) => n.id));
  }, [search, graphData]);

  // фильтры
  const [showFilters, setShowFilters] = useState(false);
  const [riskMin, setRiskMin] = useState(0);
  const [platform, setPlatform] = useState("all"); // all | tiktok | instagram
  const [enabledClasses, setEnabledClasses] = useState(() => new Set(Object.keys(VIOLATION_RU)));
  const [onlyFlagged, setOnlyFlagged] = useState(false);

  // путь между аккаунтами
  const [pathMode, setPathMode] = useState(false);
  const [pathPick, setPathPick] = useState([]); // [aId, bId]
  const [pathResult, setPathResult] = useState(null);

  // раскладка
  const [spacing, setSpacing] = useState(340);

  // аннотации следователя (статус / заметки / теги / флаг) — localStorage
  const [annotations, setAnnotations] = useState({});
  const [tagDraft, setTagDraft] = useState("");
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setAnnotations(JSON.parse(raw));
    } catch {
      /* noop */
    }
  }, []);
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(annotations));
    } catch {
      /* noop */
    }
  }, [annotations]);

  const patchAnnotation = useCallback((id, patch) => {
    setAnnotations((prev) => ({
      ...prev,
      [id]: { ...prev[id], ...patch, updated_at: new Date().toISOString() },
    }));
  }, []);

  const pinnedIds = useMemo(
    () => Object.keys(annotations).filter((id) => annotations[id]?.pinned),
    [annotations]
  );
  const flaggedCount = pinnedIds.length;

  /* размер canvas */
  const wrapRef = useRef(null);
  const [size, setSize] = useState({ w: 800, h: 600 });
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({ w: Math.max(320, width), h: Math.max(320, height) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  /* настройка сил d3: отталкивание + длина рёбер + коллизия (узлы не слипаются) */
  const onReady = useCallback((fg) => {
    fgRef.current = fg;
    setReady(true);
  }, []);
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg || !ready) return;
    fg.d3Force("charge")?.strength(-spacing);
    const linkF = fg.d3Force("link");
    if (linkF) linkF.distance((l) => spacing * 0.32 + (1 - (l.strength ?? 0.5)) * 48 + 26);
    fg.d3Force("collide", forceCollide((n) => nodeRadius(n) + 9).strength(0.9));
    fg.d3ReheatSimulation();
    if (!didFit.current) {
      didFit.current = true;
      setTimeout(() => fgRef.current?.zoomToFit(600, 60), 700);
    }
  }, [spacing, ready]);

  /* действия */
  const matchesFilter = useCallback(
    (n) =>
      n.risk_score >= riskMin &&
      (platform === "all" || n.platform === platform) &&
      enabledClasses.has(n.violation_class) &&
      (!onlyFlagged || annotations[n.id]?.pinned),
    [riskMin, platform, enabledClasses, onlyFlagged, annotations]
  );

  function findRingleader() {
    const rank = pageRank(graphData.nodes, graphData.links);
    const top = Object.entries(rank)
      .map(([id, r]) => ({ id, rank: r }))
      .sort((a, b) => b.rank - a.rank)
      .slice(0, 3);
    setTopCentral(top);
    const leader = graphData.nodes.find((n) => n.id === top[0]?.id);
    if (leader) {
      setCaseOpen(false);
      setSelected(leader);
      fgRef.current?.centerAt(leader.x, leader.y, 600);
    }
  }

  function runSearch() {
    const first = graphData.nodes.find((n) => searchMatches.has(n.id));
    if (first) {
      setCaseOpen(false);
      setSelected(first);
      fgRef.current?.centerAt(first.x, first.y, 600);
      fgRef.current?.zoom(2.5, 600);
    }
  }

  function handleNodeClick(node) {
    if (pathMode) {
      const next = pathPick.length >= 2 ? [node.id] : [...pathPick, node.id];
      setPathPick(next);
      if (next.length === 2) {
        setPathResult(shortestPath(graphData.nodes, graphData.links, next[0], next[1]));
      } else {
        setPathResult(null);
      }
      return;
    }
    setCaseOpen(false);
    setSelected(node);
  }

  function togglePathMode() {
    const on = !pathMode;
    setPathMode(on);
    setPathPick([]);
    setPathResult(null);
    if (on) setSelected(null);
  }

  function resetView() {
    setRiskMin(0);
    setPlatform("all");
    setEnabledClasses(new Set(Object.keys(VIOLATION_RU)));
    setOnlyFlagged(false);
    setTopCentral([]);
    setPathMode(false);
    setPathPick([]);
    setPathResult(null);
    setSearch("");
    setSelected(null);
    fgRef.current?.zoomToFit(600, 60);
  }

  function exportCase() {
    const payload = {
      exported_at: new Date().toISOString(),
      pinned: pinnedIds,
      annotations,
      filters: { riskMin, platform, classes: [...enabledClasses], onlyFlagged },
      central_accounts: topCentral,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `network-case-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /* ── отрисовка узла ── */
  const drawNode = (node, ctx, scale) => {
    const r = nodeRadius(node);
    const dimmed = !matchesFilter(node) || (pathResult && !pathResult.nodeIds.has(node.id));
    const baseAlpha = dimmed ? 0.12 : 1;
    const color = riskColor(node.risk_score);
    const ann = annotations[node.id];
    const t = (performance.now() % 1600) / 1600;

    // пульс критического риска
    if (node.risk_score >= 0.8 && !dimmed) {
      const halo = r + r * 1.1 * t;
      ctx.beginPath();
      ctx.arc(node.x, node.y, halo, 0, 2 * Math.PI);
      ctx.strokeStyle = `rgba(163,45,45,${0.45 * (1 - t)})`;
      ctx.lineWidth = 2 / scale;
      ctx.stroke();
    }

    // путь между аккаунтами
    if (pathResult?.nodeIds.has(node.id)) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, r + 4, 0, 2 * Math.PI);
      ctx.strokeStyle = PATH_COLOR;
      ctx.lineWidth = 3 / scale;
      ctx.stroke();
    }

    // золотая обводка топ-3 PageRank
    if (topIds.has(node.id)) {
      ctx.globalAlpha = 0.6 + 0.4 * Math.sin(performance.now() / 300);
      ctx.beginPath();
      ctx.arc(node.x, node.y, r + 3.5, 0, 2 * Math.PI);
      ctx.strokeStyle = GOLD;
      ctx.lineWidth = 3 / scale;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // совпадение поиска
    if (searchMatches.has(node.id)) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, r + 6, 0, 2 * Math.PI);
      ctx.strokeStyle = "#266df0";
      ctx.setLineDash([3 / scale, 3 / scale]);
      ctx.lineWidth = 1.5 / scale;
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // выбранный / выбор для пути
    if (selected?.id === node.id || pathPick.includes(node.id)) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, r + 2, 0, 2 * Math.PI);
      ctx.strokeStyle = pathPick.includes(node.id) ? PATH_COLOR : "#232529";
      ctx.lineWidth = 1.5 / scale;
      ctx.stroke();
    }

    // тело
    ctx.globalAlpha = baseAlpha;
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,0.85)";
    ctx.lineWidth = 1 / scale;
    ctx.stroke();

    // индикатор платформы
    ctx.beginPath();
    ctx.arc(node.x + r * 0.55, node.y - r * 0.55, Math.max(1.4, r * 0.28), 0, 2 * Math.PI);
    ctx.fillStyle = node.platform === "tiktok" ? "#111315" : "#C13584";
    ctx.fill();

    // статус расследования (точка снизу-слева)
    if (ann?.status && ann.status !== "new") {
      ctx.beginPath();
      ctx.arc(node.x - r * 0.6, node.y + r * 0.6, Math.max(1.6, r * 0.3), 0, 2 * Math.PI);
      ctx.fillStyle = STATUSES[ann.status]?.color ?? "#9fa1a7";
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 0.6 / scale;
      ctx.stroke();
    }
    ctx.globalAlpha = 1;

    // флаг «в кейсе»
    if (ann?.pinned) {
      ctx.font = `${Math.max(5, 12 / scale)}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("🚩", node.x + r + 4 / scale, node.y - r - 2 / scale);
    }

    // подпись
    if (scale > 1.2 || topIds.has(node.id) || selected?.id === node.id || searchMatches.has(node.id)) {
      const fontSize = Math.max(3, 11 / scale);
      ctx.globalAlpha = baseAlpha;
      ctx.font = `${fontSize}px "JetBrains Mono", ui-monospace, monospace`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle = "#5c5e63";
      ctx.fillText(`@${node.id}`, node.x, node.y + r + 1.5);
      ctx.globalAlpha = 1;
    }
  };

  const drawPointerArea = (node, color, ctx) => {
    ctx.beginPath();
    ctx.arc(node.x, node.y, nodeRadius(node) + 2, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
  };

  const linkColorFn = (l) => {
    if (pathResult?.linkKeys.has(keyOf(endId(l.source), endId(l.target)))) return PATH_COLOR;
    const s = graphData.nodes.find((n) => n.id === endId(l.source));
    const t = graphData.nodes.find((n) => n.id === endId(l.target));
    const dim = (s && !matchesFilter(s)) || (t && !matchesFilter(t)) || pathResult;
    return dim ? "rgba(159,161,167,0.18)" : LINK_STYLE[l.link_type]?.color ?? "#B6BAC2";
  };

  const usedViolations = useMemo(() => {
    const set = new Set(graphData.nodes.map((n) => n.violation_class));
    return Object.keys(VIOLATION_RU).filter((k) => set.has(k));
  }, [graphData]);

  const activeFilterCount =
    (riskMin > 0 ? 1 : 0) +
    (platform !== "all" ? 1 : 0) +
    (enabledClasses.size !== Object.keys(VIOLATION_RU).length ? 1 : 0) +
    (onlyFlagged ? 1 : 0);

  const ann = selected ? annotations[selected.id] : null;

  return (
    <div className="flex h-full w-full flex-col overflow-hidden rounded-xl border border-border-subtle bg-bg-base">
      {/* ───────── панель инструментов ───────── */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border-subtle bg-bg-surface-1 px-3 py-2">
        {/* поиск */}
        <div className="flex items-center gap-1 rounded-lg border border-border-strong bg-bg-base px-2 py-1">
          <span className="text-text-muted">🔍</span>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && runSearch()}
            placeholder="Поиск @handle…"
            className="w-40 bg-transparent text-sm text-text-primary outline-none placeholder:text-text-muted"
          />
          {search && (
            <button onClick={() => setSearch("")} className="text-text-muted hover:text-text-primary">
              ✕
            </button>
          )}
        </div>

        <Tool onClick={findRingleader}>
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: GOLD }} />
          Найти главный аккаунт
        </Tool>

        <Tool active={pathMode} onClick={togglePathMode}>
          ↔ Путь между аккаунтами
        </Tool>

        <Tool active={showFilters || activeFilterCount > 0} onClick={() => setShowFilters((v) => !v)}>
          ⚙ Фильтры{activeFilterCount > 0 ? ` · ${activeFilterCount}` : ""}
        </Tool>

        <div className="flex items-center gap-2 rounded-lg border border-border-strong bg-bg-base px-2.5 py-1 text-xs text-text-secondary">
          Расстояние
          <input
            type="range"
            min={120}
            max={700}
            step={20}
            value={spacing}
            onChange={(e) => setSpacing(Number(e.target.value))}
            className="h-1 w-24 cursor-pointer accent-brand-500"
          />
        </div>

        <Tool onClick={() => fgRef.current?.zoomToFit(600, 60)}>⤢ Уместить</Tool>

        <Tool active={caseOpen} onClick={() => { setCaseOpen((v) => !v); setSelected(null); }}>
          🚩 Кейс{flaggedCount > 0 ? ` · ${flaggedCount}` : ""}
        </Tool>

        <Tool onClick={exportCase}>⤓ Экспорт</Tool>

        <Tool onClick={resetView}>↺ Сброс</Tool>
      </div>

      {/* ───────── панель фильтров ───────── */}
      {showFilters && (
        <div className="ss-fade-in flex flex-wrap items-center gap-x-6 gap-y-2 border-b border-border-subtle bg-bg-surface-2 px-3 py-2 text-xs">
          <label className="flex items-center gap-2 text-text-secondary">
            Риск ≥ <span className="font-mono text-text-primary">{riskMin.toFixed(2)}</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={riskMin}
              onChange={(e) => setRiskMin(Number(e.target.value))}
              className="h-1 w-28 cursor-pointer accent-brand-500"
            />
          </label>

          <div className="flex items-center gap-1">
            {["all", "tiktok", "instagram"].map((p) => (
              <button
                key={p}
                onClick={() => setPlatform(p)}
                className={`rounded-md px-2 py-1 ${
                  platform === p
                    ? "bg-brand-500 text-white"
                    : "bg-bg-surface-1 text-text-secondary hover:bg-bg-surface-3"
                }`}
              >
                {p === "all" ? "Все" : p === "tiktok" ? "TikTok" : "Instagram"}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-1">
            {usedViolations.map((k) => {
              const on = enabledClasses.has(k);
              return (
                <button
                  key={k}
                  onClick={() =>
                    setEnabledClasses((prev) => {
                      const n = new Set(prev);
                      n.has(k) ? n.delete(k) : n.add(k);
                      return n;
                    })
                  }
                  className={`flex items-center gap-1.5 rounded-full border px-2 py-0.5 ${
                    on
                      ? "border-border-strong bg-bg-surface-1 text-text-primary"
                      : "border-border-subtle bg-transparent text-text-muted line-through"
                  }`}
                >
                  <span className="h-2 w-2 rounded-[2px]" style={{ background: VIOLATION_COLOR[k] }} />
                  {VIOLATION_RU[k]}
                </button>
              );
            })}
          </div>

          <label className="flex cursor-pointer items-center gap-1.5 text-text-secondary">
            <input
              type="checkbox"
              checked={onlyFlagged}
              onChange={(e) => setOnlyFlagged(e.target.checked)}
              className="accent-brand-500"
            />
            Только в кейсе
          </label>
        </div>
      )}

      {/* ───────── граф + панель ───────── */}
      <div className="flex min-h-0 flex-1">
        <div ref={wrapRef} className="relative min-w-0 flex-1">
          {/* контекстные баннеры */}
          <div className="pointer-events-none absolute left-3 top-3 z-10 flex flex-col gap-2">
            {pathMode && (
              <div className="ss-fade-in rounded-lg border border-[#7f56d9]/40 bg-bg-surface-1/95 px-3 py-1.5 text-xs text-text-secondary backdrop-blur">
                {pathResult
                  ? `Путь: ${pathResult.path.map((p) => "@" + p).join(" → ")} · ${pathResult.hops} связей`
                  : pathPick.length === 1
                  ? `Выбран @${pathPick[0]} — кликните второй аккаунт`
                  : "Режим пути: кликните два аккаунта"}
              </div>
            )}
            {topCentral.length > 0 && !pathMode && (
              <div className="ss-fade-in rounded-lg border border-border-subtle bg-bg-surface-1/95 px-3 py-1.5 text-xs text-text-secondary backdrop-blur">
                Центр схемы: <span className="font-mono text-text-primary">@{topCentral[0].id}</span>
                <span className="ml-1 text-text-muted">(+{topCentral.length - 1} узла)</span>
              </div>
            )}
          </div>

          <ForceGraphCanvas
            onReady={onReady}
            width={size.w}
            height={size.h}
            graphData={graphData}
            backgroundColor="#fafafb"
            nodeId="id"
            nodeLabel={(n) => `@${n.id} · риск ${(n.risk_score * 100).toFixed(0)}%`}
            nodeCanvasObject={drawNode}
            nodePointerAreaPaint={drawPointerArea}
            onNodeClick={handleNodeClick}
            onBackgroundClick={() => { setSelected(null); setCaseOpen(false); }}
            linkColor={linkColorFn}
            linkWidth={(l) => (l.strength ?? 0.3) * (l.link_type === "shared_telegram" ? 7 : 5) + 0.8}
            linkLineDash={(l) => (l.link_type === "shared_telegram" ? null : [5, 4])}
            linkDirectionalParticles={(l) =>
              l.link_type === "shared_telegram" && !pathResult ? 3 : 0
            }
            linkDirectionalParticleWidth={(l) => (l.strength ?? 0.5) * 3.5}
            linkDirectionalParticleSpeed={(l) => 0.004 + (l.strength ?? 0.5) * 0.006}
            linkDirectionalParticleColor={() => "#2AABEE"}
            linkLabel={(l) =>
              `${LINK_STYLE[l.link_type]?.label ?? l.link_type} · ${(l.strength * 100).toFixed(0)}%`
            }
            cooldownTicks={Infinity}
            d3VelocityDecay={0.5}
          />

          {/* легенда */}
          <div className="absolute bottom-3 left-3 z-10 rounded-lg border border-border-subtle bg-bg-surface-1/95 p-3 text-[11px] backdrop-blur">
            <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-text-muted">
              Классы нарушений
            </div>
            <div className="flex flex-col gap-1">
              {usedViolations.map((k) => (
                <div key={k} className="flex items-center gap-2 text-text-secondary">
                  <span className="inline-block h-2.5 w-2.5 shrink-0 rounded-[3px]" style={{ background: VIOLATION_COLOR[k] }} />
                  {VIOLATION_RU[k]}
                </div>
              ))}
            </div>
            <div className="mt-2 border-t border-border-subtle pt-2 text-[10px] text-text-muted">
              <span className="font-mono text-[#2AABEE]">━━</span> общий Telegram · цвет узла = риск · 🚩 в кейсе
            </div>
          </div>
        </div>

        {/* ───────── боковая панель ───────── */}
        <aside
          className="flex shrink-0 flex-col overflow-hidden border-l border-border-subtle bg-bg-surface-1 transition-all duration-300"
          style={{ width: selected || caseOpen ? 320 : 0 }}
        >
          {/* режим кейса: список аккаунтов в кейсе */}
          {caseOpen && !selected && (
            <div className="ss-fade-in flex h-full flex-col overflow-y-auto p-4">
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold text-text-primary">Кейс · {flaggedCount}</div>
                <button onClick={() => setCaseOpen(false)} className="rounded-md p-1 text-text-muted hover:bg-bg-surface-2 hover:text-text-primary">✕</button>
              </div>
              <p className="mt-1 text-xs text-text-muted">Аккаунты, добавленные следователем в кейс.</p>
              <div className="mt-3 flex flex-col gap-1.5">
                {pinnedIds.length === 0 && (
                  <div className="rounded-lg border border-dashed border-border-strong p-4 text-center text-xs text-text-muted">
                    Пусто. Откройте аккаунт и нажмите «Добавить в кейс».
                  </div>
                )}
                {pinnedIds.map((id) => {
                  const n = graphData.nodes.find((x) => x.id === id);
                  if (!n) return null;
                  const a = annotations[id];
                  return (
                    <button
                      key={id}
                      onClick={() => { setSelected(n); setCaseOpen(false); }}
                      className="flex items-center gap-2 rounded-lg border border-border-subtle bg-bg-base p-2 text-left transition hover:bg-bg-surface-2"
                    >
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: riskColor(n.risk_score) }} />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-mono text-xs text-text-primary">@{n.id}</span>
                        <span className="block text-[10px] text-text-muted">
                          {a?.status ? STATUSES[a.status]?.label : "Новый"} · риск {n.risk_score.toFixed(2)}
                        </span>
                      </span>
                    </button>
                  );
                })}
              </div>
              {pinnedIds.length > 0 && (
                <button onClick={exportCase} className="mt-4 w-full rounded-lg border border-border-strong px-3 py-2 text-sm text-text-primary hover:bg-bg-surface-2">
                  ⤓ Экспортировать кейс
                </button>
              )}
            </div>
          )}

          {/* режим узла: карточка аккаунта */}
          {selected && (
            <div className="ss-fade-in flex h-full flex-col overflow-y-auto p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate font-mono text-base font-semibold text-text-primary">@{selected.id}</div>
                  <div className="mt-0.5 flex items-center gap-1.5 text-xs text-text-muted">
                    <span className="inline-block h-2 w-2 rounded-full" style={{ background: selected.platform === "tiktok" ? "#111315" : "#C13584" }} />
                    {selected.platform === "tiktok" ? "TikTok" : "Instagram"}
                    <span className="text-border-strong">·</span>
                    {selected.followers.toLocaleString("ru-RU")} подписчиков
                  </div>
                </div>
                <button onClick={() => setSelected(null)} className="shrink-0 rounded-md p-1 text-text-muted hover:bg-bg-surface-2 hover:text-text-primary" aria-label="Закрыть">✕</button>
              </div>

              {topIds.has(selected.id) && (
                <div className="mt-3 flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium" style={{ background: "rgba(230,179,62,0.14)", color: "#8a6a16" }}>
                  <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: GOLD }} />
                  Центральный узел схемы (PageRank)
                </div>
              )}

              {/* статус расследования */}
              <div className="mt-4">
                <div className="mb-1 text-xs text-text-muted">Статус расследования</div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(STATUSES).map(([key, s]) => {
                    const on = (ann?.status ?? "new") === key;
                    return (
                      <button
                        key={key}
                        onClick={() => patchAnnotation(selected.id, { status: key })}
                        className={`flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] ${
                          on ? "border-transparent text-white" : "border-border-strong text-text-secondary hover:bg-bg-surface-2"
                        }`}
                        style={on ? { background: s.color } : undefined}
                      >
                        <span className="h-1.5 w-1.5 rounded-full" style={{ background: on ? "#fff" : s.color }} />
                        {s.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* risk score */}
              <div className="mt-4">
                <div className="mb-1.5 flex items-center justify-between text-xs text-text-muted">
                  <span>Risk score</span>
                  <span className="rounded-md px-2 py-0.5 font-mono text-xs font-semibold text-white" style={{ background: riskColor(selected.risk_score) }}>
                    {selected.risk_score.toFixed(2)} · {riskLabel(selected.risk_score)}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-bg-surface-3">
                  <div className="h-full rounded-full" style={{ width: `${selected.risk_score * 100}%`, background: riskColor(selected.risk_score) }} />
                </div>
              </div>

              {/* класс нарушения */}
              <div className="mt-4">
                <div className="text-xs text-text-muted">Класс нарушения</div>
                <div className="mt-1 flex items-center gap-2 text-sm font-medium text-text-primary">
                  <span className="inline-block h-2.5 w-2.5 rounded-[3px]" style={{ background: VIOLATION_COLOR[selected.violation_class] }} />
                  {VIOLATION_RU[selected.violation_class]}
                </div>
              </div>

              {/* мета */}
              <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="text-text-muted">Создан</div>
                  <div className="mt-0.5 font-mono text-text-primary">{new Date(selected.created_at).toLocaleDateString("ru-RU")}</div>
                </div>
                <div>
                  <div className="text-text-muted">Подписчики</div>
                  <div className="mt-0.5 font-mono text-text-primary">{selected.followers.toLocaleString("ru-RU")}</div>
                </div>
              </div>

              {selected.telegram && (
                <div className="mt-4 rounded-lg border border-[#2AABEE]/30 bg-[#2AABEE]/8 p-3">
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-[#1c8fce]">Общий Telegram-канал</div>
                  <div className="mt-1 break-all font-mono text-xs text-text-primary">{selected.telegram}</div>
                  <div className="mt-1 text-[11px] text-text-secondary">Связывает аккаунт с другими участниками схемы.</div>
                </div>
              )}

              {/* заметки следователя */}
              <div className="mt-4">
                <div className="mb-1 flex items-center justify-between text-xs text-text-muted">
                  <span>Заметки следователя</span>
                  {ann?.updated_at && (
                    <span className="text-[10px]">{new Date(ann.updated_at).toLocaleString("ru-RU")}</span>
                  )}
                </div>
                <textarea
                  value={ann?.notes ?? ""}
                  onChange={(e) => patchAnnotation(selected.id, { notes: e.target.value })}
                  placeholder="Наблюдения, связи, гипотезы…"
                  rows={4}
                  className="w-full resize-y rounded-lg border border-border-strong bg-bg-base p-2 text-sm text-text-primary outline-none placeholder:text-text-muted focus:border-brand-500"
                />
              </div>

              {/* теги */}
              <div className="mt-3">
                <div className="mb-1 text-xs text-text-muted">Теги</div>
                <div className="flex flex-wrap items-center gap-1.5">
                  {(ann?.tags ?? []).map((tg) => (
                    <span key={tg} className="flex items-center gap-1 rounded-full bg-bg-surface-3 px-2 py-0.5 text-[11px] text-text-secondary">
                      {tg}
                      <button
                        onClick={() => patchAnnotation(selected.id, { tags: (ann?.tags ?? []).filter((x) => x !== tg) })}
                        className="text-text-muted hover:text-text-primary"
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                  <input
                    value={tagDraft}
                    onChange={(e) => setTagDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && tagDraft.trim()) {
                        const cur = ann?.tags ?? [];
                        if (!cur.includes(tagDraft.trim())) patchAnnotation(selected.id, { tags: [...cur, tagDraft.trim()] });
                        setTagDraft("");
                      }
                    }}
                    placeholder="+ тег"
                    className="w-20 bg-transparent text-[11px] text-text-primary outline-none placeholder:text-text-muted"
                  />
                </div>
              </div>

              {/* действия */}
              <div className="mt-auto space-y-2 pt-5">
                <button
                  onClick={() => patchAnnotation(selected.id, { pinned: !ann?.pinned })}
                  className={`w-full rounded-lg border px-3 py-2 text-sm font-medium transition active:scale-[0.99] ${
                    ann?.pinned
                      ? "border-[#E24B4A]/40 bg-[#E24B4A]/10 text-[#b03a39]"
                      : "border-border-strong text-text-primary hover:bg-bg-surface-2"
                  }`}
                >
                  {ann?.pinned ? "🚩 Убрать из кейса" : "🚩 Добавить в кейс"}
                </button>
                <button
                  onClick={() => onOpenCase?.(selected)}
                  className="w-full rounded-lg bg-brand-500 px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand-600 active:scale-[0.99]"
                >
                  Открыть карточку кейса
                </button>
                <button
                  onClick={() => onLaunchProbe?.(selected)}
                  disabled={selected.risk_score < 0.7}
                  title={selected.risk_score < 0.7 ? "Доступно при risk_score ≥ 0.70" : undefined}
                  className="w-full rounded-lg border border-border-strong px-3 py-2 text-sm font-medium text-text-primary transition hover:bg-bg-surface-2 active:scale-[0.99] disabled:cursor-not-allowed disabled:border-border-subtle disabled:bg-bg-surface-2 disabled:text-text-muted disabled:active:scale-100"
                >
                  Запустить зондировщика
                </button>
                {selected.risk_score < 0.7 && (
                  <p className="text-center text-[11px] text-text-muted">Зондировщик доступен при risk_score ≥ 0.70</p>
                )}
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

/* маленькая кнопка панели инструментов */
function Tool({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-sm font-medium transition active:scale-[0.98] ${
        active
          ? "border-brand-500 bg-brand-glow text-brand-600"
          : "border-border-strong bg-bg-surface-1 text-text-primary hover:bg-bg-surface-2"
      }`}
    >
      {children}
    </button>
  );
}

export { DEMO_NODES, DEMO_LINKS };
