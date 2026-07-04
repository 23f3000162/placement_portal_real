# celery worker file
from app import app, celery  # noqa: F401
import tasks  # noqa: F401
