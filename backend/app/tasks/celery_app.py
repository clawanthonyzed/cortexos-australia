"""Celery app configuration."""
from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "cortexos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.agent_tasks"],
)

celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    result_expires=86400,  # 24 hours
    timezone="Australia/Perth",
    enable_utc=True,
    # Retry configuration
    task_max_retries=3,
    task_default_retry_delay=60,
    # Rate limiting per task type
    task_annotations={
        "app.tasks.agent_tasks.run_agent_task": {"rate_limit": "60/m"},
        "app.tasks.agent_tasks.run_workflow_task": {"rate_limit": "30/m"},
    },
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-stale-tasks": {
            "task": "app.tasks.agent_tasks.cleanup_stale_tasks",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)
