import asyncio
import logging

from aiogram import Bot
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from planner.notification_scheduler import check_reminders, check_task_notifications, start_scheduler


class Command(BaseCommand):
    help = "Runs Telegram notification scheduler without starting bot polling."

    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Checks due task/reminder notifications once and exits.',
        )

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN is empty. Set BOT_TOKEN environment variable.")

        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
        if options['once']:
            asyncio.run(self._run_once(token))
        else:
            asyncio.run(self._run(token))

    async def _run_once(self, token):
        bot = Bot(token=token)
        try:
            await check_task_notifications(bot)
            await check_reminders(bot)
            self.stdout.write(self.style.SUCCESS("Notification check finished."))
        finally:
            await bot.session.close()

    async def _run(self, token):
        bot = Bot(token=token)
        scheduler = start_scheduler(bot)
        self.stdout.write(self.style.SUCCESS("Notification worker started. Press Ctrl+C to stop."))
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            self.stdout.write("Stopping notification worker...")
        finally:
            scheduler.shutdown()
            await bot.session.close()
