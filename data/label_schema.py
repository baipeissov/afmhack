"""
Единая схема из 6 классов. Используется и build_dataset.py, и text_classifier.py,
и шаблонами объяснений в API — чтобы id класса везде значил одно и то же.
"""

LABELS = {
    0: "clean",
    1: "casino_betting",
    2: "pyramid_investment",
    3: "referral_network",
    4: "urgency_pressure",
    5: "hidden_engagement",
}

LABELS_RU = {
    0: "чисто / нейтральный контент",
    1: "нелегальное казино / ставки",
    2: "гарантированный доход / пирамида",
    3: "реферальная / сетевая схема",
    4: "психологическое давление / срочность",
    5: "скрытое вовлечение (личка, закрытый канал)",
}

NAME_TO_ID = {v: k for k, v in LABELS.items()}
