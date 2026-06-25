"""
Пять спец-агентов по типам мошенничества (6-классовая схема, класс 0=clean
не нуждается в специалисте). Каждый — тонкая конфигурация над BaseSpecialist.
"""

from __future__ import annotations

from .base_specialist import BaseSpecialist


class CasinoAgent(BaseSpecialist):
    violation_class = "casino_betting"
    display_ru = "нелегальное казино / ставки"
    keywords = [
        "казино", "ставк", "ставки", "слот", "рулетк", "1xbet", "mostbet",
        "betwinner", "букмекер", "фриспин", "джекпот", "jackpot", "вывод средств",
        "депозит", "промокод", "коэффициент", "бонус на депозит",
    ]
    visual_markers_of_interest = ["casino_interface", "luxury_lifestyle"]
    expert_focus = (
        "Признаки: реклама онлайн-казино/букмекеров без лицензии РК, обещание "
        "лёгкого выигрыша, промокоды, бонусы на депозит, демонстрация интерфейса слотов."
    )


class PyramidAgent(BaseSpecialist):
    violation_class = "pyramid_investment"
    display_ru = "гарантированный доход / финансовая пирамида"
    keywords = [
        "гарант", "гарантированный доход", "доход", "прибыл", "удво", "x2", "x3",
        "х2", "х3", "пирамид", "инвест", "вклад", "проценты", "пассивный доход",
        "приумнож", "фонд", "трейдинг", "крипто",
    ]
    visual_markers_of_interest = ["fake_income_screenshot", "pyramid_diagram", "trading_terminal", "luxury_lifestyle"]
    expert_focus = (
        "Признаки: обещание гарантированной/нереалистичной доходности, выплаты "
        "за счёт новых участников, скриншоты «дохода», структура с уровнями."
    )


class ReferralAgent(BaseSpecialist):
    violation_class = "referral_network"
    display_ru = "реферальная / сетевая схема"
    keywords = [
        "реферал", "пригласи", "приглашай", "партнёрск", "партнерск", "сетевой",
        "mlm", "бонус за друга", "реф-ссылк", "реферальн", "команда", "структур",
        "приведи друга", "зарабатывай на приглашениях",
    ]
    visual_markers_of_interest = ["pyramid_diagram"]
    expert_focus = (
        "Признаки: заработок преимущественно за привлечение новых людей, "
        "реферальные ссылки, многоуровневые бонусы за приглашённых."
    )


class UrgencyAgent(BaseSpecialist):
    violation_class = "urgency_pressure"
    display_ru = "психологическое давление / срочность"
    keywords = [
        "успей", "срочно", "только сегодня", "последний", "осталось", "лимит",
        "не упусти", "прямо сейчас", "акция заканчивается", "мест осталось",
        "горящее", "успейте", "пока не поздно", "ограниченное предложение",
    ]
    visual_markers_of_interest = []
    expert_focus = (
        "Признаки: искусственный дефицит и срочность, давление «решай сейчас», "
        "обратный отсчёт, страх упустить (FOMO) как манипуляция."
    )


class HiddenEngagementAgent(BaseSpecialist):
    violation_class = "hidden_engagement"
    display_ru = "скрытое вовлечение (личка / закрытый канал)"
    keywords = [
        "пиши в личк", "в директ", "telegram", "t.me", "закрытый канал",
        "ссылка в шапк", "перейди по ссылк", "напиши +", "ставь +", "в комментариях ссылк",
        "подробности в лс", "пиши в телеграм", "вступай в канал", "по ссылке в профиле",
    ]
    visual_markers_of_interest = []
    expert_focus = (
        "Признаки: увод аудитории в личку/закрытый канал/Telegram, чтобы продолжить "
        "схему вне модерации площадки; призывы «напиши +», «ссылка в профиле»."
    )


ALL_SPECIALISTS = [
    CasinoAgent, PyramidAgent, ReferralAgent, UrgencyAgent, HiddenEngagementAgent,
]
