"""
NetworkMapper (Агент 4) и PredictiveScorer (Агент 0).

NetworkMapper строит граф связей между мошенническими аккаунтами по общим
сигналам (Telegram-канал, реф-ссылка, хэштеги Jaccard, общие упоминания),
считает PageRank и отдаёт {nodes, links} в формате фронтенда NetworkGraph.
PredictiveScorer — упреждающая эвристика риска для молодых аккаунтов.

Вынесено в agents/ (раньше жило в backend/orchestrator.py со стабами).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

TELEGRAM_RE = re.compile(r"(?:https?://)?(?:t\.me|telegram\.me)/[A-Za-z0-9_+/]+", re.I)
HASHTAG_RE = re.compile(r"#([A-Za-z0-9_а-яёА-ЯЁ]+)")
MENTION_RE = re.compile(r"@([A-Za-z0-9_.]+)")
URL_RE = re.compile(r"https?://[^\s)]+", re.I)


def _norm_tg(link: str) -> str:
    return link.lower().split("t.me/")[-1].split("telegram.me/")[-1].strip("/")


def _parse_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _key(a: str, b: str) -> tuple:
    return (a, b) if a < b else (b, a)


class NetworkMapper:
    def __init__(self) -> None:
        self.graph: dict[str, dict] = {}  # handle -> {connections, metadata}

    def add_account(self, account: dict) -> None:
        handle = (account.get("handle") or "").lstrip("@")
        if not handle:
            return
        self.graph[handle] = self.graph.get(handle, {"connections": [], "metadata": {}})
        self.graph[handle]["metadata"] = account

    @staticmethod
    def _signals(account: dict) -> dict[str, set[str]]:
        text = " ".join(str(account.get(k, "") or "") for k in ("bio", "bio_text", "caption", "url", "bio_url"))
        telegram = {_norm_tg(m.group(0)) for m in TELEGRAM_RE.finditer(text)}
        if account.get("telegram"):
            telegram.add(_norm_tg(str(account["telegram"])))
        referrals = {u for u in URL_RE.findall(text) if "ref" in u.lower()}
        if account.get("referral"):
            referrals.add(str(account["referral"]))
        hashtags = {h.lower() for h in HASHTAG_RE.findall(text)} | {
            str(h).lstrip("#").lower() for h in (account.get("hashtags") or [])
        }
        mentions = {m.lower() for m in MENTION_RE.findall(text)} | {
            str(m).lstrip("@").lower() for m in (account.get("mentions") or [])
        }
        mentions.discard((account.get("handle") or "").lstrip("@").lower())
        return {"telegram": telegram, "referral": referrals, "hashtags": hashtags, "mentions": mentions}

    @staticmethod
    def _jaccard(a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def find_connections(self, account: dict) -> list[dict]:
        handle = (account.get("handle") or "").lstrip("@")
        sa = self._signals(account)
        out: list[dict] = []
        for other, data in self.graph.items():
            if other == handle:
                continue
            sb = self._signals(data["metadata"])
            if sa["telegram"] & sb["telegram"]:
                out.append({"handle": other, "link_type": "shared_telegram", "strength": 0.9,
                            "shared": sorted(sa["telegram"] & sb["telegram"])})
            if sa["referral"] & sb["referral"]:
                out.append({"handle": other, "link_type": "shared_referral_link", "strength": 0.8,
                            "shared": sorted(sa["referral"] & sb["referral"])})
            jac = self._jaccard(sa["hashtags"], sb["hashtags"])
            if jac > 0.5:
                out.append({"handle": other, "link_type": "shared_hashtag", "strength": round(jac, 2),
                            "shared": sorted(sa["hashtags"] & sb["hashtags"])})
            if sa["mentions"] & sb["mentions"]:
                out.append({"handle": other, "link_type": "shared_mention",
                            "strength": round(min(0.7, 0.3 + 0.1 * len(sa["mentions"] & sb["mentions"])), 2),
                            "shared": sorted(sa["mentions"] & sb["mentions"])})
        if handle in self.graph:
            self.graph[handle]["connections"] = out
        return out

    def _all_links(self) -> list[dict]:
        seen: set[tuple] = set()
        links: list[dict] = []
        for handle, data in self.graph.items():
            for c in self.find_connections(data["metadata"]):
                a, b = _key(handle, c["handle"])
                k = (a, b, c["link_type"])
                if k in seen:
                    continue
                seen.add(k)
                links.append({"source": a, "target": b, "link_type": c["link_type"], "strength": c["strength"]})
        return links

    def to_graph_json(self) -> dict:
        nodes = []
        for handle, data in self.graph.items():
            m = data["metadata"]
            nodes.append({
                "id": handle,
                "platform": m.get("platform", "tiktok"),
                "risk_score": float(m.get("risk_score", 0.0)),
                "violation_class": m.get("violation_class", "clean"),
                "followers": int(m.get("followers", 0)),
                "created_at": str(m.get("created_at", "")),
            })
        return {"nodes": nodes, "links": self._all_links()}

    def get_central_accounts(self, top_n: int = 3) -> list[dict]:
        ids = list(self.graph.keys())
        if not ids:
            return []
        links = self._all_links()
        adj: dict[str, list[tuple[str, float]]] = {i: [] for i in ids}
        for l in links:
            adj[l["source"]].append((l["target"], l["strength"]))
            adj[l["target"]].append((l["source"], l["strength"]))
        N = len(ids)
        rank = {i: 1 / N for i in ids}
        d = 0.85
        for _ in range(50):
            nxt = {i: (1 - d) / N for i in ids}
            for i in ids:
                edges = adj[i]
                total = sum(w for _, w in edges)
                if total == 0:
                    for j in ids:
                        nxt[j] += d * rank[i] / N
                else:
                    for to, w in edges:
                        nxt[to] += d * rank[i] * (w / total)
            rank = nxt
        top = sorted(rank.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
        return [{"handle": h, "centrality": round(r, 4),
                 "risk_score": float(self.graph[h]["metadata"].get("risk_score", 0.0)),
                 "platform": self.graph[h]["metadata"].get("platform", "tiktok")} for h, r in top]


class PredictiveScorer:
    """Агент 0 — упреждающая оценка риска молодого аккаунта до явных сигналов."""

    RISK_TERMS = ["доход", "гарант", "депозит", "вывод", "реферал", "пригласи",
                  "инвест", "казино", "ставк", "бонус", "%", "t.me/", "пассивн"]

    def score(self, account: dict) -> float:
        text = " ".join(str(account.get(k, "") or "") for k in ("bio", "bio_text", "caption")).lower()
        score = min(0.6, sum(1 for t in self.RISK_TERMS if t in text) * 0.12)
        created = _parse_dt(account.get("created_at"))
        if created:
            age = (datetime.now(timezone.utc) - created).days
            if age < 7:
                score += 0.25
            elif age < 30:
                score += 0.15
            if age < 30 and int(account.get("followers", 0) or 0) > 30000:
                score += 0.2
        return round(min(score, 1.0), 3)
