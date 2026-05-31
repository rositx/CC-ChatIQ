from celery import Celery
from backend.config import REDIS_URL

# Create the global Celery application instance
celery_app = Celery(
    "cc_chatiq_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Enforce standard synchronous eager execution mode for local tests
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True
