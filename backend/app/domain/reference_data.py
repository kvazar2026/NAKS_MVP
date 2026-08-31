"""Closed reference lists (справочники) used by the structural ``error``-level
rules (``app/services/validation.py``) and by ``MockProvider`` (synonym
matching for the classification-relevant fields).

**Known limitation, explicit in spec ("Further Notes"):** these lists are
MVP demo data, not verified against a NAKS expert or a normative source —
"справочники допустимых значений (группы ОПО, способы сварки и т.д.)... не
проверены экспертом НАКС — это явный открытый риск... не блокирующий
реализацию MVP, но обязательный к учёту перед реальным использованием."
Do not present these as authoritative outside the demo.

A value is considered valid by matching its ``label`` exactly (the label is
the canonical value stored on ``NormalizedSurveyData`` and used verbatim as
the generated .docx placeholder text) — ``code`` only exists for stable
identifiers (React/test keys), it never travels over the wire.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReferenceEntry:
    code: str
    label: str
    # Lowercased free-text variants ``MockProvider`` maps onto ``label``.
    synonyms: tuple[str, ...] = field(default_factory=tuple)


OPO_GROUPS: tuple[ReferenceEntry, ...] = (
    ReferenceEntry("1", "Группа 1 — сосуды и аппараты, работающие под давлением"),
    ReferenceEntry("2", "Группа 2 — технологические трубопроводы"),
    ReferenceEntry("3", "Группа 3 — объекты котлонадзора"),
    ReferenceEntry("4", "Группа 4 — подъёмные сооружения"),
    ReferenceEntry("5", "Группа 5 — объекты горнодобывающей и металлургической промышленности"),
)

EQUIPMENT_TYPES: tuple[ReferenceEntry, ...] = (
    ReferenceEntry(
        "power_source",
        "Источник сварочного тока",
        ("источник питания", "источник тока", "сварочный источник", "источник сварочного тока"),
    ),
    ReferenceEntry(
        "semi_automatic",
        "Полуавтомат сварочный",
        ("полуавтомат", "п/а", "полуавтомат сварочный"),
    ),
    ReferenceEntry(
        "tig_unit",
        "Аппарат аргонодуговой сварки (TIG)",
        ("tig", "аргонодуговой аппарат", "установка рад", "аппарат рад"),
    ),
    ReferenceEntry(
        "automatic_unit",
        "Автомат сварочный",
        ("автомат", "сварочный автомат", "автомат сварочный"),
    ),
    ReferenceEntry(
        "contact_welding_unit",
        "Установка контактной сварки",
        ("контактная сварка", "точечная сварка", "установка контактной сварки"),
    ),
)

WELDING_METHODS: tuple[ReferenceEntry, ...] = (
    ReferenceEntry("RD", "РД — ручная дуговая сварка покрытым электродом", ("рд", "ручная дуговая")),
    ReferenceEntry("RAD", "РАД — ручная аргонодуговая сварка", ("рад", "tig", "аргонодуговая")),
    ReferenceEntry(
        "MP",
        "МП — механизированная сварка плавящимся электродом в среде защитных газов (МИГ/МАГ)",
        ("мп", "миг", "маг", "миг/маг", "мп (миг/маг)", "мпг", "мпс", "мпи"),
    ),
    ReferenceEntry("ADS", "АДС — автоматическая дуговая сварка под флюсом", ("адс", "автоматическая под флюсом")),
    ReferenceEntry("ESHS", "ЭШС — электрошлаковая сварка", ("эшс",)),
    ReferenceEntry("KT", "КТ — контактная сварка", ("кт", "контактная")),
)

PURPOSES: tuple[ReferenceEntry, ...] = (
    ReferenceEntry(
        "pipelines",
        "Сварка технологических трубопроводов",
        ("трубопровод", "сварка трубопроводов", "трубопроводы"),
    ),
    ReferenceEntry(
        "pressure_vessels",
        "Сварка сосудов, работающих под давлением",
        ("сосуды под давлением", "сосуд", "сосуды"),
    ),
    ReferenceEntry(
        "metal_structures",
        "Сварка металлоконструкций",
        ("металлоконструкции", "мк"),
    ),
    ReferenceEntry("repair", "Ремонт и восстановление оборудования", ("ремонт", "восстановление")),
    ReferenceEntry("installation", "Монтаж оборудования", ("монтаж",)),
)


def labels(entries: tuple[ReferenceEntry, ...]) -> frozenset[str]:
    """Canonical labels of ``entries`` — the set a value must belong to."""

    return frozenset(entry.label for entry in entries)
