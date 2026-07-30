FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY categories/mcp-server-trap/requirements.txt ./requirements.txt
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --requirement requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HONEYPOT_LOG_PATH=/data/events.jsonl

RUN groupadd --system --gid 10001 honeypot \
    && useradd --system --uid 10001 --gid honeypot --no-create-home honeypot

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY honeypot_common ./honeypot_common
COPY categories/mcp-server-trap/app.py categories/mcp-server-trap/decoy_data.json ./
RUN mkdir /data && chown honeypot:honeypot /data

USER 10001:10001
EXPOSE 8086

CMD ["uvicorn", "app:app", "--host=0.0.0.0", "--port=8086", "--workers=2", "--no-server-header"]
