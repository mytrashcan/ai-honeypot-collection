FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HONEYPOT_LOG_PATH=/data/events.jsonl

RUN groupadd --system --gid 10001 honeypot \
    && useradd --system --uid 10001 --gid honeypot --no-create-home honeypot

WORKDIR /app
COPY categories/credential-honey/requirements.txt ./requirements.txt
RUN python -m pip install --requirement requirements.txt

COPY honeypot_common ./honeypot_common
COPY categories/credential-honey/server.py categories/credential-honey/.env categories/credential-honey/config.json ./
RUN mkdir /data && chown honeypot:honeypot /data

USER 10001:10001
EXPOSE 8080

CMD ["uvicorn", "server:app", "--host=0.0.0.0", "--port=8080", "--workers=2", "--no-server-header"]
