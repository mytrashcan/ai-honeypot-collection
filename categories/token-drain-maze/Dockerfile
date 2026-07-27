FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY categories/token-drain-maze/requirements.txt ./requirements.txt
RUN python -m pip install --requirement requirements.txt --target /deps


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HONEYPOT_LOG_PATH=/data/events.jsonl

COPY --from=builder /deps /usr/local/lib/python3.12/site-packages

RUN groupadd --system --gid 10001 honeypot \
    && useradd --system --uid 10001 --gid honeypot --no-create-home honeypot

WORKDIR /app
COPY honeypot_common ./honeypot_common
COPY categories/token-drain-maze/app.py categories/token-drain-maze/decoy_data.json ./
RUN mkdir /data && chown honeypot:honeypot /data

USER 10001:10001
EXPOSE 8080

CMD ["uvicorn", "app:app", "--host=0.0.0.0", "--port=8080", "--workers=2", "--no-server-header"]
