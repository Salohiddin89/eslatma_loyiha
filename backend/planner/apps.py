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

        # Gunicorn preforked model: faqat worker jarayonida (RUN_MAIN yo'q bo'lsa)
        # runserver: RUN_MAIN=true bo'lgandagina ishga tushirish (reloader ni o'tkazib yuborish)
        run_main = os.environ.get('RUN_MAIN')
        server_software = os.environ.get('SERVER_SOFTWARE', '')

        # runserver bilan ishlayotganda — Django reloader'dagi ikki marta ishga tushishni oldini olish
        if 'runserver' in sys.argv and run_main != 'true':
            return

        # gunicorn, uvicorn, waitress va boshqa WSGI/ASGI server
        # Bu holda RUN_MAIN yo'q, lekin scheduler ishlashi kerak
        try:
            from planner.notification_scheduler import start_scheduler
            start_scheduler()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error(
                "Scheduler ishga tushmadi: %s", exc, exc_info=True
            )
