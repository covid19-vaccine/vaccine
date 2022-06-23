from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esr21.settings')

app = Celery('esr21')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')


# Configure an over age calculation task to run Mon-Fri at 6a.m
app.conf.beat_schedule = {
    "schedule-esr21-reports-updates": {
        "task": "esr21_reports.tasks.pull_reports_data",
        "schedule": crontab(minute="*/5", day_of_week='*')
    },
}
