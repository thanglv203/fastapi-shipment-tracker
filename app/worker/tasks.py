from celery import Celery
from app.config import db_settings



app = Celery(
    "api_tasks",
    broker=db_settings.REDIS_URL(9),
)


@app.task
def send_main():
    pass