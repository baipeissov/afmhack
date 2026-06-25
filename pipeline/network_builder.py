"""
Строит граф связей между аккаунтами из risk_queue.jsonl: узел — аккаунт
(handle+platform), ребро — общий сигнал (Telegram-канал, реферальная
ссылка, хэштег, номер Kaspi), извлечённый entity_extractor'ом /
kaspi_normalizer'ом в api/dossier.py и сохранённый в записи очереди как
item["entities"].

Формат вывода — то же, что фронт уже умеет рисовать в NetworkGraph.jsx
(DEMO_NODES/DEMO_LINKS): nodes[{id, platform, risk_score, violation_class}],
links[{source, target, link_type, strength}].
"""

from collections import defaultdict
from itertools import combinations

ENTITY_TO_LINK_TYPE = {
    "telegram": "shared_telegram",
    "referral_links": "shared_referral_link",
    "hashtags": "shared_hashtag",
    "phones": "shared_phone",
}


def _account_key(item: dict) -> tuple[str, str]:
    return (item.get("account_handle") or "unknown", item.get("platform") or "")


def build_network(items: list[dict]) -> dict:
    nodes: dict[tuple[str, str], dict] = {}
    entity_to_accounts: dict[tuple[str, str], set] = defaultdict(set)

    for item in items:
        key = _account_key(item)
        node = nodes.setdefault(
            key,
            {
                "id": key[0],
                "platform": key[1].lower(),
                "risk_score": 0.0,
                "violation_class": "clean",
            },
        )
        score = item.get("risk_score") or 0.0
        if score >= node["risk_score"]:
            node["risk_score"] = score
            node["violation_class"] = item.get("top_class") or node["violation_class"]

        for entity_type, values in (item.get("entities") or {}).items():
            for value in values:
                entity_to_accounts[(entity_type, value)].add(key)

    link_strength: dict[tuple[tuple[str, str], tuple[str, str], str], int] = defaultdict(int)
    for (entity_type, _value), accounts in entity_to_accounts.items():
        link_type = ENTITY_TO_LINK_TYPE.get(entity_type)
        if not link_type or len(accounts) < 2:
            continue
        for a, b in combinations(sorted(accounts), 2):
            link_strength[(a, b, link_type)] += 1

    max_strength = max(link_strength.values(), default=1)
    links = [
        {
            "source": a[0],
            "target": b[0],
            "link_type": link_type,
            "strength": round(0.4 + 0.6 * count / max_strength, 2),
        }
        for (a, b, link_type), count in link_strength.items()
    ]

    return {"nodes": list(nodes.values()), "links": links}
