FROM python:3.13-slim-bookworm@sha256:c45a22ea000adfd9cda29364bbe7edd23001ce5cc2ad15857cfbf7766943b9ca

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --gid 10001 co-story \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin co-story

WORKDIR /opt/co-story
COPY backend/requirements-prod.txt backend/requirements-prod.txt
RUN python -m pip install --no-cache-dir --requirement backend/requirements-prod.txt

COPY backend backend
COPY web web
COPY ops/container/healthcheck.py /usr/local/bin/co-story-healthcheck
RUN chmod 0555 /usr/local/bin/co-story-healthcheck \
    && install -d -m 0750 -o 10001 -g 10001 /var/log/co-story

WORKDIR /opt/co-story/backend
USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "/usr/local/bin/co-story-healthcheck", "127.0.0.1", "8000"]

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "8000", "--workers", "1"]
