import os
import sys
from django.apps import AppConfig


class PlannerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planner'

    def ready(self):
        # migrate, test, shell, collectstatic va boshqa manage.py buyruqlarda scheduler ishga tushmaydi
        skip_commands = (
            'migrate', 'makemigrations', 'test', 'shell',
            'collectstatic', 'createsuperuser', 'run_notifications',
            'dbshell', 'showmigrations', 'sqlmigrate',
        )
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        # Faqat local runserver da scheduler ishga tushadi
        # PythonAnywhere (uWSGI) va boshqa hosting'larda
        # background thread ishlamaydi — scheduled task ishlatiladi
        is_runserver = 'runserver' in sys.argv
        run_main = os.environ.get('RUN_MAIN', '')

        if is_runserver and run_main == 'true':
            # Local development uchun
            try:
                from planner.notification_scheduler import start_scheduler
                start_scheduler()
            except Exception as exc:
                import logging
                logging.getLogger(__name__).error(
                    "Scheduler ishga tushmadi: %s", exc, exc_info=True
                )
