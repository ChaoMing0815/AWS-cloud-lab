FROM python:3.13-slim-bookworm@sha256:c45a22ea000adfd9cda29364bbe7edd23001ce5cc2ad15857cfbf7766943b9ca AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /opt/co-story
COPY backend/requirements-prod.txt backend/requirements-prod.txt
RUN python -m pip install --no-cache-dir --requirement backend/requirements-prod.txt \
    && python -m pip uninstall --yes pip setuptools

FROM debian:bookworm-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates netbase tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 co-story \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin co-story

WORKDIR /opt/co-story
COPY --from=builder /usr/local /usr/local
COPY backend backend
COPY web web
COPY ops/container/healthcheck.py /usr/local/bin/co-story-healthcheck
COPY ops/release/deploy_container.sh /usr/local/share/co-story/deploy_container.sh
COPY ops/systemd/co-story-container.service /usr/local/share/co-story/co-story-container.service
RUN chmod 0555 /usr/local/bin/co-story-healthcheck \
    && chmod 0555 /usr/local/share/co-story/deploy_container.sh \
    && chmod 0444 /usr/local/share/co-story/co-story-container.service \
    && install -d -m 0750 -o 10001 -g 10001 /var/log/co-story \
    && install -d -m 0755 -o root -g root /etc/pki/rds

WORKDIR /opt/co-story/backend
USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "/usr/local/bin/co-story-healthcheck"]

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "8000", "--workers", "1"]
