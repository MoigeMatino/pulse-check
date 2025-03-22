from celery import Celery
from celery.schedules import crontab
import os

BROKER_URL = os.getenv("CELERY_BROKER_URL")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

celery_app = Celery(
    "worker",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.tasks"], 
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    result_expires=3600,
)

celery_app.conf.beat_schedule = {
    # SSL Check Task (runs daily at midnight)
    "periodic-ssl-check": {
        "task": "app.tasks.ssl_checker.periodic_ssl_check",  
        "schedule": crontab(hour=0, minute=0),  # Run daily at midnight
    },
}

# Configure directory path to celerybeat-schedule file(file used by Celery Beat to store the state of periodic tasks)
celery_app.conf.beat_schedule_filename = "/var/run/celery/celerybeat-schedule"