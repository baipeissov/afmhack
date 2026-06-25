"""
Layer 3 — синтетическая аугментация (data/synthetic_seed.csv).

Генерируем RU/KZ-варианты скам-фраз через слот-шаблоны (template-based),
а не через внешний LLM API: это сознательный выбор — детерминированно,
полностью офлайн, легко объяснить на защите ("вот шаблон, вот слоты,
вот почему модель видит такие фразы"), нет риска утечки/зависимости от
сторонних сервисов.

Решает проблему дыры в данных: классы casino_betting / referral_network /
urgency_pressure почти не встречаются во внешних Layer-1 датасетах (они
все про job-scam/phishing/generic-spam), а pyramid_investment и
hidden_engagement из Layer 1 почти полностью на английском, хотя продукт
должен явно работать с RU/KZ.

Каждый шаблон — строка с {slot} placeholders, наполняется декартовым
произведением вариантов слотов, затем случайно подвыбирается до cap
строк на класс/язык, чтобы не взрывать размер датасета.
"""

import csv
import itertools
import random
from pathlib import Path

random.seed(42)

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic_seed.csv"
CAP_PER_CLASS_LANG = 120  # после декартова произведения сэмплим не больше этого числа

# ---------------------------------------------------------------------------
# Общие слоты
# ---------------------------------------------------------------------------
CASINOS = ["1xBet", "Mostbet", "Vulkan Casino", "Azino777", "Pin-Up", "Лев Казино", "BetKZ"]
SPORTS_RU = ["футбол", "хоккей", "теннис", "баскетбол", "киберспорт"]
SPORTS_KZ = ["футбол", "хоккей", "теннис", "баскетбол", "электронды спорт"]
AMOUNTS = [30000, 50000, 100000, 200000, 500000]
PCTS = [100, 150, 200, 300, 500]
MINUTES = [5, 10, 15, 30]
PROMOS = ["VIP100", "BONUS200", "WIN500", "START300"]

MULTS = [2, 3, 5, 10]
PERIODS_RU = ["неделю", "месяц", "день"]
PERIODS_KZ = ["апта", "ай", "күн"]
FUNDS = ["TengeGrowth", "AlphaInvest", "QazFinance Club", "CryptoStar Fund", "ProfitChain"]
DAYS = [7, 10, 14, 30]

N_PEOPLE = [3, 5, 10, 20]

HOURS = [1, 2, 3, 6]
N_SLOTS = [1, 2, 3, 5]

WORDS = ["хочу", "старт", "да", "инфо", "+"]
WORDS_KZ = ["қалаймын", "старт", "иә", "ақпарат"]
CHANNELS = ["VIP Club", "Private Signals", "Closed Group", "Жабық топ"]
TOPICS_RU = ["заработок", "инвестиции", "казино-бонусы", "крипту"]
TOPICS_KZ = ["табыс", "инвестиция", "казино бонустары", "криптовалюта"]

# ---- слоты для clean (0) — нейтральный бытовой контент без скам-сигнала.
# Было 0 KZ-шаблонов для этого класса (только 10 строк из внешних
# источников на весь датасет) — модель путала нейтральный казахский текст
# с мошенничеством из-за нехватки негативных примеров на языке.
CITIES_RU = ["Алматы", "Астане", "Шымкенте", "Караганде", "Атырау"]
CITIES_KZ = ["Алматыда", "Астанада", "Шымкентте", "Қарағандыда", "Атырауда"]
DISHES_RU = ["плов", "манты", "баурсаки", "лагман", "бешбармак"]
DISHES_KZ = ["палау", "манты", "бауырсақ", "лагман", "бешбармак"]
SCHOOL_SUBJECTS_RU = ["математике", "физике", "истории", "английскому"]
SCHOOL_SUBJECTS_KZ = ["математикадан", "физикадан", "тарихтан", "ағылшын тілінен"]
WEATHER_RU = ["солнечно", "дождливо", "прохладно", "жарко"]
WEATHER_KZ = ["күн ашық", "жаңбырлы", "салқын", "ыстық"]
SPORT_TEAMS_RU = ["Кайрат", "Астана", "Тобол", "Ордабасы"]
SPORT_TEAMS_KZ = ["Қайрат", "Астана", "Тобыл", "Ордабасы"]

# ---------------------------------------------------------------------------
# (label, lang) -> [(template, {slot_name: [options]})]
# ---------------------------------------------------------------------------
TEMPLATE_SPECS = [
    # ---- 0 clean (нейтральный бытовой контент, БЕЗ скам-сигнала) ----
    (0, "ru", "Сегодня в {city} {weather}, не забудьте взять с собой зонт или кепку.",
     {"city": CITIES_RU, "weather": WEATHER_RU}),
    (0, "ru", "Приготовила на ужин {dish}, получилось очень вкусно, делюсь рецептом в комментариях.",
     {"dish": DISHES_RU}),
    (0, "ru", "Дочка получила пятёрку по {subject}, очень горжусь её успехами в школе.",
     {"subject": SCHOOL_SUBJECTS_RU}),
    (0, "ru", "{team} выиграл вчерашний матч, отличная игра была у защиты.",
     {"team": SPORT_TEAMS_RU}),
    (0, "ru", "Сходили сегодня в парк в {city}, погода была {weather}, дети были очень рады.",
     {"city": CITIES_RU, "weather": WEATHER_RU}),
    (0, "ru", "Подскажите хороший рецепт {dish}, хочу приготовить на выходных для всей семьи.",
     {"dish": DISHES_RU}),
    (0, "ru", "Завтра контрольная по {subject}, весь вечер сидим готовимся с сыном.",
     {"subject": SCHOOL_SUBJECTS_RU}),
    (0, "ru", "Поздравляю всех с праздником, желаю крепкого здоровья и мирного неба над головой.",
     {}),
    (0, "ru", "В {city} открыли новый парк, очень красиво оформили набережную.",
     {"city": CITIES_RU}),
    (0, "kz", "Бүгін {city} {weather}, қолшатырды бірге алып шыққан жөн.",
     {"city": CITIES_KZ, "weather": WEATHER_KZ}),
    (0, "kz", "Кешкі асқа {dish} жасадым, өте дәмді болды, рецептісін комментарийде бөлісемін.",
     {"dish": DISHES_KZ}),
    (0, "kz", "Қызым {subject} пәнінен бес алды, мектептегі жетістігіне қуанып отырмын.",
     {"subject": SCHOOL_SUBJECTS_KZ}),
    (0, "kz", "{team} кешегі ойынды жеңіп алды, қорғаныс өте жақсы ойнады.",
     {"team": SPORT_TEAMS_KZ}),
    (0, "kz", "{city} саябаққа бардық, ауа райы {weather} болды, балалар өте қуанды.",
     {"city": CITIES_KZ, "weather": WEATHER_KZ}),
    (0, "kz", "{dish}-тың жақсы рецептін айтыңызшы, демалыс күні бүкіл отбасына дайындағым келеді.",
     {"dish": DISHES_KZ}),
    (0, "kz", "Ертең {subject} пәнінен бақылау жұмысы, ұлыммен бүкіл кеш дайындалып отырмыз.",
     {"subject": SCHOOL_SUBJECTS_KZ}),
    (0, "kz", "Барша халықты мерекемен құттықтаймын, баршаңызға денсаулық пен бейбітшілік тілеймін.",
     {}),
    (0, "kz", "{city} жаңа саябақ ашылды, жағалауды өте әдемі етіп жасапты.",
     {"city": CITIES_KZ}),
    # ---- 1 casino_betting ----
    (1, "ru", "Заходи в {casino}, бонус {pct}% на первый депозит!",
     {"casino": CASINOS, "pct": PCTS}),
    (1, "ru", "Ставь на {sport} прямо сейчас и выигрывай {amount} тенге за вечер.",
     {"sport": SPORTS_RU, "amount": AMOUNTS}),
    (1, "ru", "{casino}: рулетка и слоты 24/7, вывод средств за {minutes} минут без верификации.",
     {"casino": CASINOS, "minutes": MINUTES}),
    (1, "ru", "Беттинг на {sport} с лучшими коэффициентами в стране, регистрируйся по ссылке в профиле.",
     {"sport": SPORTS_RU}),
    (1, "ru", "Промокод {promo} даёт бонус {pct}% на ставки в {casino}.",
     {"promo": PROMOS, "pct": PCTS, "casino": CASINOS}),
    (1, "kz", "{casino} казиносына кір, бірінші депозитке {pct}% бонус!",
     {"casino": CASINOS, "pct": PCTS}),
    (1, "kz", "{sport} ойынына бәс тігіп, бір кешке {amount} теңге ұтып ал.",
     {"sport": SPORTS_KZ, "amount": AMOUNTS}),
    (1, "kz", "{casino}: рулетка 24/7 жұмыс істейді, ақшаны {minutes} минутта верификациясыз ала аласың.",
     {"casino": CASINOS, "minutes": MINUTES}),

    # ---- 2 pyramid_investment ----
    (2, "ru", "Гарантирую доход x{mult} за {period} без риска, инвестируй в {fund} прямо сейчас.",
     {"mult": MULTS, "period": PERIODS_RU, "fund": FUNDS}),
    (2, "ru", "Вложи {amount} тенге и получи {amount2} через {period} — гарантированно.",
     {"amount": AMOUNTS, "amount2": AMOUNTS, "period": PERIODS_RU}),
    (2, "ru", "{fund} приносит стабильный доход {pct}% в {period}, без усилий с твоей стороны.",
     {"fund": FUNDS, "pct": PCTS, "period": PERIODS_RU}),
    (2, "ru", "Удвой свой капитал за {days} дней — проверенная схема {fund}.",
     {"days": DAYS, "fund": FUNDS}),
    (2, "ru", "Криптофонд {fund} с доходностью {pct}% годовых, тысячи подтверждений в отзывах.",
     {"fund": FUNDS, "pct": PCTS}),
    (2, "kz", "Бір {period}де х{mult} кіріс кепілдендіреміз, {fund}-ке қазір инвестиция сал.",
     {"period": PERIODS_KZ, "mult": MULTS, "fund": FUNDS}),
    (2, "kz", "{amount} теңге салып, бір {period}де {amount2} ал, кепілдік беріледі.",
     {"amount": AMOUNTS, "period": PERIODS_KZ, "amount2": AMOUNTS}),
    (2, "kz", "{fund} күніне {pct}% тұрақты кіріс әкеледі, тәуекелсіз.",
     {"fund": FUNDS, "pct": PCTS}),

    # ---- 3 referral_network ----
    (3, "ru", "Приведи друга и получи {amount} тенге на свой счёт.",
     {"amount": AMOUNTS}),
    (3, "ru", "Построй команду из {n} человек и зарабатывай на каждом приглашённом.",
     {"n": N_PEOPLE}),
    (3, "ru", "Регистрируйся по моей реферальной ссылке в профиле и получи бонус {amount} тенге.",
     {"amount": AMOUNTS}),
    (3, "ru", "Многоуровневая система: получай {pct}% с каждого депозита людей из твоей сети.",
     {"pct": PCTS}),
    (3, "ru", "Стань частью команды {fund}, твой доход растёт с каждым новым участником.",
     {"fund": FUNDS}),
    (3, "kz", "Досыңды әкел, шотыңа {amount} теңге аласың.",
     {"amount": AMOUNTS}),
    (3, "kz", "{n} адамнан команда құрып, әр шақырылған адамнан табыс тап.",
     {"n": N_PEOPLE}),
    (3, "kz", "Менің профильдегі сілтемем арқылы тіркеліп, {amount} теңге бонус ал.",
     {"amount": AMOUNTS}),
    (3, "ru", "{pct}% с каждого депозита твоих рефералов будет приходить тебе пожизненно.",
     {"pct": PCTS}),
    (3, "ru", "Подключи {n} друзей к {fund} и получи {amount} тенге бонусом на счёт.",
     {"n": N_PEOPLE, "fund": FUNDS, "amount": AMOUNTS}),
    (3, "ru", "Развивай свою сеть в {fund}, чем больше структура — тем выше твой ранг и доход.",
     {"fund": FUNDS}),
    (3, "kz", "Рефералдарыңның әр депозитінен {pct}% өмір бойы саған түседі.",
     {"pct": PCTS}),
    (3, "kz", "{n} досыңды {fund}-ке қосып, шотыңа {amount} теңге бонус ал.",
     {"n": N_PEOPLE, "fund": FUNDS, "amount": AMOUNTS}),
    (3, "kz", "{fund}-де желіңді дамыт, құрылым үлкейген сайын табысың артады.",
     {"fund": FUNDS}),

    # ---- 4 urgency_pressure ----
    (4, "ru", "Только сегодня! Акция действует {hours} часа, не упусти шанс.",
     {"hours": HOURS}),
    (4, "ru", "Осталось всего {n} мест, успей записаться прямо сейчас.",
     {"n": N_SLOTS}),
    (4, "ru", "Цена вырастет уже через {hours} часов, успей купить по старой цене.",
     {"hours": HOURS}),
    (4, "ru", "Это последний шанс присоединиться к {fund}, потом мест больше не будет.",
     {"fund": FUNDS}),
    (4, "ru", "Решай быстро — предложение сгорает через {minutes} минут.",
     {"minutes": MINUTES}),
    (4, "kz", "Тек бүгін! Акция {hours} сағат қана жарамды, мүмкіндікті жіберме.",
     {"hours": HOURS}),
    (4, "kz", "Орын {n} ғана қалды, қазір тіркел.",
     {"n": N_SLOTS}),
    (4, "kz", "Бағасы {hours} сағаттан кейін көтеріледі, ескі бағамен үлгер.",
     {"hours": HOURS}),
    (4, "ru", "Если не примешь решение сегодня, потеряешь возможность зайти в {fund} навсегда.",
     {"fund": FUNDS}),
    (4, "ru", "Спеши, количество мест в {fund} ограничено — осталось {n}, заканчивается на глазах.",
     {"fund": FUNDS, "n": N_SLOTS}),
    (4, "ru", "Не теряй время, другие уже зарабатывают в {fund}, а ты ещё думаешь.",
     {"fund": FUNDS}),
    (4, "kz", "Бүгін шешім қабылдамасаң, {fund}-ге кіру мүмкіндігін мүлде жоғалтасың.",
     {"fund": FUNDS}),
    (4, "kz", "{fund}-де орын шектеулі — {n} ғана қалды, көз алдында таусылып барады.",
     {"fund": FUNDS, "n": N_SLOTS}),
    (4, "kz", "Уақытыңды жоғалтпа, басқалар {fund}-те қазірден ақша табады, сен әлі ойланасың.",
     {"fund": FUNDS}),

    # ---- 5 hidden_engagement ----
    (5, "ru", 'Напиши "{word}" в комментариях, пришлю детали в директ.',
     {"word": WORDS}),
    (5, "ru", "Пиши мне в личные сообщения по поводу {topic}, расскажу всё лично.",
     {"topic": TOPICS_RU}),
    (5, "ru", 'Подключайся к закрытому каналу "{channel}", там все подробности про {topic}.',
     {"channel": CHANNELS, "topic": TOPICS_RU}),
    (5, "ru", "Заполни анкету по ссылке в профиле, дальше расскажу всё в директе про {topic}.",
     {"topic": TOPICS_RU}),
    (5, "ru", 'Напиши слово "{word}" и получи доступ к закрытому контенту про {topic}.',
     {"word": WORDS, "topic": TOPICS_RU}),
    (5, "ru", 'Не пишу подробности про {topic} здесь, переходи в закрытый Telegram-канал "{channel}".',
     {"topic": TOPICS_RU, "channel": CHANNELS}),
    (5, "ru", 'Кто хочет узнать про {topic} — ставь лайк и пиши "{word}" мне в директ.',
     {"topic": TOPICS_RU, "word": WORDS}),
    (5, "ru", 'Подробности про {topic} только для своих, добавляйся в закрытую группу "{channel}".',
     {"topic": TOPICS_RU, "channel": CHANNELS}),
    (5, "ru", 'Жду сообщений в директ со словом "{word}", расскажу как начать с {topic}.',
     {"word": WORDS, "topic": TOPICS_RU}),
    (5, "ru", "Это не пишу в открытую — стучись в директ, обсудим {topic} лично.",
     {"topic": TOPICS_RU}),
    (5, "kz", 'Комментарийге "{word}" деп жаз, директке толық ақпарат жіберемін.',
     {"word": WORDS_KZ}),
    (5, "kz", "{topic} жайлы жеке хабарламаға жаз, бәрін жеке айтып беремін.",
     {"topic": TOPICS_KZ}),
    (5, "kz", '"{channel}" жабық каналға қосыл, {topic} жайлы барлық ақпарат сонда.',
     {"channel": CHANNELS, "topic": TOPICS_KZ}),
    (5, "kz", 'Профильдегі сілтеме арқылы анкета толтыр, қалғанын {topic} туралы директте айтамын.',
     {"topic": TOPICS_KZ}),
    (5, "kz", '"{word}" деп жаз, {topic} туралы жабық контентке қол жеткіз.',
     {"word": WORDS_KZ, "topic": TOPICS_KZ}),
    (5, "kz", '{topic} туралы білгің келсе, "{word}" деп жазып директке жаз.',
     {"topic": TOPICS_KZ, "word": WORDS_KZ}),
    (5, "kz", 'Бұл жерде ашық жазбаймын — директке жаз, {topic} туралы жеке сөйлесеміз.',
     {"topic": TOPICS_KZ}),
]


def expand(template, slots):
    if not slots:
        return [template]
    keys = list(slots.keys())
    combos = list(itertools.product(*[slots[k] for k in keys]))
    random.shuffle(combos)
    combos = combos[:CAP_PER_CLASS_LANG]
    out = []
    for combo in combos:
        out.append(template.format(**dict(zip(keys, combo))))
    return out


def main():
    rows = []
    for label, lang, template, slots in TEMPLATE_SPECS:
        for text in expand(template, slots):
            rows.append((text, label, lang))

    # cap per (label, lang) across all templates of that class, to keep
    # class sizes comparable to each other
    by_key = {}
    for r in rows:
        by_key.setdefault((r[1], r[2]), []).append(r)
    final = []
    for key, items in by_key.items():
        random.shuffle(items)
        final.extend(items[:150])

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "label", "lang"])
        w.writerows(final)

    print(f"wrote {len(final)} synthetic rows -> {OUT_PATH}")
    from collections import Counter

    print(Counter((r[1], r[2]) for r in final))


if __name__ == "__main__":
    main()
