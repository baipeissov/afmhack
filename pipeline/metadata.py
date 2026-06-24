"""
Метаданные аккаунта -> нормализованные признаки для fusion-модели.

Сейчас принимает dict (передаётся вручную при демо или приходит из
коннектора/жалобы гражданина). В проде сюда подключается реальный вызов
TikTok Research API / Instagram Graph API (account info endpoint) — сам
контракт normalize() не меняется, меняется только то, что заполняет
raw-словарь на входе.

Намеренно НЕ собираем PII: только агрегированные публичные метрики аккаунта
(возраст, темп роста, наличие реф-ссылки в био) — никаких имён, телефонов,
геолокации.
"""

from dataclasses import dataclass


@dataclass
class AccountFeatures:
    account_age_days: float
    follower_growth_rate: float  # доля прироста подписчиков в неделю, напр. 0.5 = +50%/нед
    has_referral_link_in_bio: float  # 0.0 / 1.0
    posting_frequency_per_day: float = 0.0


DEFAULTS = AccountFeatures(
    account_age_days=365.0,
    follower_growth_rate=0.0,
    has_referral_link_in_bio=0.0,
    posting_frequency_per_day=1.0,
)


def normalize(raw: dict | None) -> dict:
    """raw: {account_age_days, follower_growth, referral_link_in_bio, ...}
    -> нормализованные [0,1]-признаки для fusion-модели.

    Нормализация эвристическая (не обучаемая) — намеренно: на 40-80
    видео-объектах в обучающей выборке fusion-модели обучать ещё и шкалы
    нормализации means переобучение. Эвристики легко объяснить аналитику
    на дефенсе: "аккаунт младше 30 дней -> risk выше".
    """
    raw = raw or {}
    age_days = float(raw.get("account_age_days", DEFAULTS.account_age_days))
    growth = float(raw.get("follower_growth", DEFAULTS.follower_growth_rate))
    has_ref = 1.0 if raw.get("referral_link_in_bio") else 0.0

    # моложе 30 дней -> 1.0, старше 365 дней -> ~0.0, линейно между
    age_risk = max(0.0, min(1.0, (365 - age_days) / 335))
    # рост >100%/нед -> считаем максимально подозрительным
    growth_risk = max(0.0, min(1.0, growth / 1.0))

    return {
        "account_age_risk": round(age_risk, 4),
        "follower_growth_risk": round(growth_risk, 4),
        "has_referral_link_in_bio": has_ref,
    }


if __name__ == "__main__":
    example = {"account_age_days": 23, "follower_growth": 12.0, "referral_link_in_bio": True}
    print(normalize(example))
