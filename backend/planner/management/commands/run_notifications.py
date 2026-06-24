"""
Bildirishnoma workeri — bot kerak emas, requests orqali ishlaydi.
Hosting'da alohida process sifatida ishga tushiriladi:
    python manage.py run_notifications

Procfile'da:
    worker: python backend/manage.py run_notifications
"""
import logging
import time
import signal
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Bildirishnoma schedulerni ishga tushiradi (bot kerak emas, requests orqali)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Bir marta tekshirib chiqadi va to\'xtaydi.',
        )

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not token:
            raise CommandError(
                "TELEGRAM_BOT_TOKEN bo'sh. BOT_TOKEN environment variable ni o'rnating."
            )

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            stream=sys.stdout,
        )

        if options['once']:
            self._run_once()
        else:
            self._run_loop()

    def _run_once(self):
        """Bir marta tekshirib chiqadi."""
        from planner.notification_scheduler import check_task_notifications, check_reminders
        self.stdout.write("Bir martalik tekshiruv boshlandi...")
        check_task_notifications()
        check_reminders()
        self.stdout.write(self.style.SUCCESS("Tekshiruv tugadi."))

    def _run_loop(self):
        """Scheduler'ni ishga tushiradi va doimiy ishlaydi."""
        from planner.notification_scheduler import start_scheduler

        self.stdout.write(self.style.SUCCESS(
            "✅ Bildirishnoma workeri ishga tushdi (bot kerak emas)."
        ))
        self.stdout.write("To'xtatish uchun Ctrl+C bosing.")

        scheduler = start_scheduler()

        # Graceful shutdown
        def _shutdown(signum, frame):
            self.stdout.write("\nScheduler to'xtatilmoqda...")
            scheduler.shutdown(wait=False)
            sys.exit(0)

        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGINT, _shutdown)

        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self.stdout.write("\nScheduler to'xtatildi.")
            scheduler.shutdown(wait=False)
