"""Celery app configuration."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "cortexos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.agent_tasks",
        "app.tasks.memory_tasks",
        "app.tasks.research_tasks",
    ],
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
    result_expires=86400,
    timezone="Australia/Perth",
    enable_utc=True,
    task_max_retries=3,
    task_default_retry_delay=60,
    task_annotations={
        "app.tasks.agent_tasks.run_agent_task": {"rate_limit": "60/m"},
        "app.tasks.agent_tasks.run_workflow_task": {"rate_limit": "30/m"},
    },
    beat_schedule={
        "cleanup-stale-tasks": {
            "task": "app.tasks.agent_tasks.cleanup_stale_tasks",
            "schedule": 300.0,
        },
        "ingest-work-log": {
            "task": "app.tasks.memory_tasks.ingest_work_log",
            "schedule": 900.0,
        },
        "sync-agent-files": {
            "task": "app.tasks.memory_tasks.sync_agent_files",
            "schedule": 14400.0,
        },
        "snapshot-empire-health": {
            "task": "app.tasks.memory_tasks.snapshot_empire_health",
            "schedule": 21600.0,
        },
        "decay-old-memories": {
            "task": "app.tasks.memory_tasks.decay_old_memories",
            "schedule": 86400.0,
        },
        # Research loop — daily per venture (AWST times, stored as UTC)
        "research-cudan-studio": {
            "task": "app.tasks.research_tasks.research_cudan_studio",
            "schedule": crontab(hour=0, minute=0),   # 8am AWST
        },
        "research-bloom-bub": {
            "task": "app.tasks.research_tasks.research_bloom_bub",
            "schedule": crontab(hour=0, minute=30),  # 8:30am AWST
        },
        "research-gtt-perth": {
            "task": "app.tasks.research_tasks.research_gtt_perth",
            "schedule": crontab(hour=1, minute=0),   # 9am AWST
        },
        # Phase 2 — approval polling + outcome reminders
        "check-action-approvals": {
            "task": "app.tasks.research_tasks.check_action_approvals",
            "schedule": 1800.0,  # every 30 min
        },
        "send-outcome-reminders": {
            "task": "app.tasks.research_tasks.send_outcome_reminders",
            "schedule": 21600.0,  # every 6 hours
        },
    },
)
