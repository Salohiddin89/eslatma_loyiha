import os
import sys
from django.apps import AppConfig


class PlannerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planner'

    def ready(self):
        # Bu buyruqlarda scheduler ishga tushmaydi
        skip_commands = (
            'migrate', 'makemigrations', 'test', 'shell',
            'collectstatic', 'createsuperuser', 'run_notifications',
            'dbshell', 'showmigrations', 'sqlmigrate',
        )
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        # Local runserver da faqat asosiy jarayon (reloader'dan o'tkazib yuborish)
        if 'runserver' in sys.argv:
            if os.environ.get('RUN_MAIN') != 'true':
                return

        # uWSGI / gunicorn / boshqa WSGI server yoki local runserver
        # Har ikki holda ham schedulerni ishga tushiramiz
        try:
            from planner.notification_scheduler import start_scheduler
            import logging
            logging.getLogger(__name__).info(
                "Scheduler ishga tushmoqda... (pid=%s)", os.getpid()
            )
            start_scheduler()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error(
                "Scheduler ishga tushmadi: %s", exc, exc_info=True
            )
