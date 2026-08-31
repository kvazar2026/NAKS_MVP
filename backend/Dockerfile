# Runtime image for the FastAPI backend (ticket 07 — Docker Compose).
#
# Only what ticket 01+ actually ships is baked in here: runtime deps from
# requirements.txt, the `app/` package, and the config-driven registries
# (`config/`, `templates/`). Dev-only files (tests, requirements-dev.txt,
# pyproject.toml) and anything unrelated to this app (see .dockerignore) are
# intentionally excluded from the image.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Installed separately from the rest of the source so this layer is cached
# across rebuilds that only touch application code.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Uses the stdlib instead of curl/wget so the image needs no extra package.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
