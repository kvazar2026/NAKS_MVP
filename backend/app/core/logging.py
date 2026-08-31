"""Structured, PII-free technical logging (spec, User Story 28; ADR 0002):
"обезличенные технические логи (время обработки, направление, код
результата, ошибка) без реквизитов и персональных данных".

``log_outcome``'s parameter list is deliberately narrow (endpoint, direction,
result, duration, error code) — the same "make the safe shape the only
callable shape" approach as ``LLMNormalizationInput`` (see app/schemas/llm.py):
there is no ``**fields``/``dict`` escape hatch a caller could use to slip
survey content (INN, address, contact details, equipment data) into a log
line.
"""

import logging

logger = logging.getLogger("naks")


def configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(message)s")


def log_outcome(
    *,
    endpoint: str,
    direction: str,
    result: str,
    duration_ms: float,
    error_code: str | None = None,
) -> None:
    logger.info(
        "endpoint=%s direction=%s result=%s duration_ms=%.1f error_code=%s",
        endpoint,
        direction,
        result,
        duration_ms,
        error_code or "-",
    )
