import logging

from celery import Celery
from celery.signals import worker_ready

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "scalermind",
    broker=settings.redis_url,
    backend=f"{settings.redis_url.rsplit('/', 1)[0]}/1",
)
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_track_started=True,
    result_expires=86_400,
    worker_send_task_events=True,
)


@worker_ready.connect
def log_worker_ready(sender=None, **kwargs) -> None:
    worker_name = getattr(sender, "hostname", "unknown")
    logger.info("ScalerMind worker ready; heartbeat enabled", extra={"worker": worker_name})
