FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system --gid 10001 honeypot \
    && useradd --system --uid 10001 --gid honeypot --no-create-home honeypot

WORKDIR /app
COPY categories/ai-fingerprint/analyzer.py categories/ai-fingerprint/rules.yaml ./
RUN mkdir /data && chown honeypot:honeypot /data

USER 10001:10001

# The analyzer is an offline tool. Keep its Compose container available so it
# can inspect any service log with `docker compose exec ai-fingerprint ...`.
CMD ["python", "-c", "import time; time.sleep(2147483647)"]
