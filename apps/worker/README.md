# Worker application boundary

Phase 1 runs Celery as a separate Compose service while sharing the API image and Python package. The Celery app bootstrap currently lives in `apps/api/app/worker/celery_app.py`; task modules will be added here as worker responsibilities grow.
