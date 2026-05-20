"""Celery application instance.

Both API and worker processes import this module so task names resolve on
either side. Run the worker with:

    celery -A apps.worker.celery_app:celery_app worker --loglevel=info
"""

from celery import Celery

from core.config import settings

celery_app = Celery(
    "conviq",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["apps.worker.tasks.pipeline"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    # ML inference can be long-running; don't prefetch extra work
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)
