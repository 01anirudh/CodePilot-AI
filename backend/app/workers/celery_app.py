from celery import Celery
from app.config import settings

celery_app = Celery(
    "codepilot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.analyze_repository": {"queue": "analysis"},
        "app.workers.tasks.run_workflow": {"queue": "workflows"},
        "app.workers.tasks.generate_embeddings": {"queue": "embeddings"},
    },
)
