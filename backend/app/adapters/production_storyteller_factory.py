from __future__ import annotations

import os
from datetime import timedelta
from typing import Any

from app.adapters.bedrock_storyteller import BedrockStoryteller
from app.adapters.story_resolution_narrator import (
    ProductionCompositeStorytellerNarrator,
)
from app.adapters.system_clock import SystemClock
from app.application.story_resolution import StoryResolutionWorker
from app.workers.story_resolution_worker import LocalStoryResolutionWorkerRunner


def _required_setting(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(name)
    return value


def _required_positive_int(
    name: str,
    *,
    minimum: int = 1,
    maximum: int = 1200,
) -> int:
    raw = _required_setting(name)
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(name) from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(name)
    return value


def _create_bedrock_client(region: str, *, config: Any):
    import boto3

    return boto3.client("bedrock-runtime", region_name=region, config=config)


def create_production_bedrock_storyteller() -> BedrockStoryteller:
    region = _required_setting("CO_STORY_AWS_REGION")
    model_id = _required_setting("CO_STORY_BEDROCK_MODEL_ID")
    guardrail_id = _required_setting("CO_STORY_BEDROCK_GUARDRAIL_ID")
    guardrail_version = _required_setting("CO_STORY_BEDROCK_GUARDRAIL_VERSION")
    max_tokens = _required_positive_int("CO_STORY_BEDROCK_MAX_TOKENS")

    from botocore.config import Config

    config = Config(
        read_timeout=30,
        connect_timeout=5,
        retries={"max_attempts": 0},
    )
    client = _create_bedrock_client(region, config=config)
    return BedrockStoryteller(
        client=client,
        model_id=model_id,
        guardrail_id=guardrail_id,
        guardrail_version=guardrail_version,
        max_tokens=max_tokens,
    )


def create_production_story_resolution_narrator() -> ProductionCompositeStorytellerNarrator:
    return ProductionCompositeStorytellerNarrator(create_production_bedrock_storyteller())


def build_production_worker_runner(
    *,
    database_url: str,
    worker_id: str,
) -> LocalStoryResolutionWorkerRunner:
    from app.adapters.postgres_story_job_queue import PostgresStoryJobQueue
    from app.adapters.postgres_story_resolution_store import PostgresStoryResolutionStore

    clock = SystemClock()
    queue = PostgresStoryJobQueue(
        database_url,
        clock=clock,
        lease_duration=timedelta(seconds=30),
        max_attempts=2,
    )
    store = PostgresStoryResolutionStore(database_url, clock=clock)
    narrator = create_production_story_resolution_narrator()
    worker = StoryResolutionWorker(
        queue,
        store,
        narrator,
        max_attempts=2,
    )
    return LocalStoryResolutionWorkerRunner(queue, worker, worker_id=worker_id)


def build_production_worker(
    database_url: str,
    worker_id: str | None = None,
) -> LocalStoryResolutionWorkerRunner:
    if not database_url:
        raise RuntimeError("DATABASE_URL")
    if os.environ.get("CO_STORY_ENV", "").lower() != "production":
        raise RuntimeError("CO_STORY_ENV")
    if os.environ.get("CO_STORY_RESOLUTION_MODE", "async").strip().lower() != "async":
        raise RuntimeError("CO_STORY_RESOLUTION_MODE")

    return build_production_worker_runner(
        database_url=database_url,
        worker_id=worker_id or "production-story-resolution-worker",
    )
