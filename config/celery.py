"""Celery application configuration."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("support_operations_copilot")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.imports = (
    "workers.classify_ticket",
    "workers.draft_reply",
    "workers.ingest_knowledge",
    "workers.run_eval",
    "workers.summarize_thread",
)
app.autodiscover_tasks()
