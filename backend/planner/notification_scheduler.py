import logging
from datetime import timedelta
from html import escape

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asgiref.sync import sync_to_async
from django.utils import timezone

logger = logging.getLogger(__name__)

TZ = pytz.timezone('Asia/Tashkent')
WEEKDAY_ORDER = ['dushanba', 'seshanba', 'chorshanba', 'payshanba', 'juma', 'shanba', 'yakshanba']


def get_today_slug():
    return WEEKDAY_ORDER[timezone.now().astimezone(TZ).weekday()]


@sync_to_async
def _get_morning_messages(today):
    from accounts.models import User
    from planner.models import WeekDay

    messages = []
    users = User.objects.filter(telegram_id__isnull=False).exclude(telegram_id=0)
    for user in users:
        wd = WeekDay.objects.filter(user=user, day=today).first()
        if wd:
            tasks = list(wd.tasks.all())
            if tasks:
                task_lines = '\n'.join(
                    [
                        f"{idx}. 🕒 <b>{str(task.time)[:5]}</b> - {escape(task.title)}"
                        for idx, task in enumerate(tasks, start=1)
                    ]
                )
                text = (
                    f"🌅 <b>Bugungi kun tartibi</b>\n\n"
                    f"👋 Salom, <b>{escape(user.first_name)}</b>!\n"
                    f"📅 Kun: <b>{wd.get_day_display()}</b>\n"
                    f"🎯 Reja: <b>{escape(wd.title)}</b>\n"
                    f"📌 Vazifalar soni: <b>{len(tasks)} ta</b>\n\n"
                    f"📝 <b>Vazifalar:</b>\n{task_lines}"
                )
            else:
                text = (
                    f"🌅 <b>Bugungi kun tartibi</b>\n\n"
                    f"👋 Salom, <b>{escape(user.first_name)}</b>!\n"
                    f"📅 Kun: <b>{wd.get_day_display()}</b>\n"
                    f"🎯 Reja: <b>{escape(wd.title)}</b>\n"
                    f"📌 Vazifalar soni: <b>0 ta</b>\n\n"
                    "✅ Bugun uchun vazifa qo'shilmagan."
                )
        else:
            day_name = WEEKDAY_ORDER[timezone.now().astimezone(TZ).weekday()].capitalize()
            text = (
                f"🌅 <b>Bugungi kun tartibi</b>\n\n"
                f"👋 Salom, <b>{escape(user.first_name)}</b>!\n"
                f"📅 Kun: <b>{day_name}</b>\n"
                "⚠️ Bugun uchun kun tartibi qo'shilmagan."
            )
        messages.append({'telegram_id': user.telegram_id, 'username': user.username, 'text': text})
    return messages


@sync_to_async
def _get_due_tasks(today, current_time, today_date):
    from planner.models import Task

    tasks = (
        Task.objects.filter(
            weekday__day=today,
            time__lte=current_time,
            weekday__user__telegram_id__isnull=False,
        )
        .exclude(weekday__user__telegram_id=0)
        .exclude(last_notified_date=today_date)
        .select_related('weekday', 'weekday__user')
    )
    return [
        {
            'id': task.id,
            'telegram_id': task.weekday.user.telegram_id,
            'username': task.weekday.user.username,
            'first_name': task.weekday.user.first_name,
            'day': task.weekday.get_day_display(),
            'day_title': task.weekday.title,
            'title': task.title,
            'time': str(task.time)[:5],
            'task_number': list(task.weekday.tasks.all()).index(task) + 1,
            'task_count': task.weekday.tasks.count(),
        }
        for task in tasks
    ]


@sync_to_async
def _mark_task_sent(task_id, today_date):
    from planner.models import Task

    Task.objects.filter(id=task_id).update(notified=True, last_notified_date=today_date)


@sync_to_async
def _get_due_reminders(now, window_end):
    from planner.models import Reminder

    reminders = (
        Reminder.objects.filter(
            notified=False,
            remind_at__lte=window_end,
            user__telegram_id__isnull=False,
        )
        .exclude(user__telegram_id=0)
        .select_related('user')
    )
    return [
        {
            'id': reminder.id,
            'telegram_id': reminder.user.telegram_id,
            'username': reminder.user.username,
            'first_name': reminder.user.first_name,
            'title': reminder.title,
            'remind_at': reminder.remind_at,
        }
        for reminder in reminders
    ]


@sync_to_async
def _mark_reminder_sent(reminder_id):
    from planner.models import Reminder

    Reminder.objects.filter(id=reminder_id).update(notified=True)


async def send_morning_messages(bot):
    today = get_today_slug()
    for message in await _get_morning_messages(today):
        try:
            await bot.send_message(message['telegram_id'], message['text'], parse_mode='HTML')
            logger.info("Morning message sent to %s (%s)", message['username'], message['telegram_id'])
        except Exception as exc:
            logger.warning("Could not send morning message to %s: %s", message['username'], exc)


async def check_task_notifications(bot):
    now_local = timezone.now().astimezone(TZ)
    current_time = now_local.strftime('%H:%M')
    today_date = now_local.date()
    today = get_today_slug()

    for task in await _get_due_tasks(today, current_time, today_date):
        try:
            text = (
                f"⏰ <b>Vazifa vaqti keldi</b>\n\n"
                f"👋 Salom, <b>{escape(task['first_name'])}</b>!\n"
                f"📅 Kun: <b>{task['day']}</b>\n"
                f"🎯 Reja: <b>{escape(task['day_title'])}</b>\n"
                f"📌 Vazifa: <b>{task['task_number']}/{task['task_count']}</b>\n\n"
                f"{task['task_number']}. ✅ <b>{escape(task['title'])}</b>\n"
                f"🕒 Vaqt: <b>{task['time']}</b>"
            )
            await bot.send_message(task['telegram_id'], text, parse_mode='HTML')
            await _mark_task_sent(task['id'], today_date)
            logger.info("Task notification sent: %s -> %s", task['title'], task['username'])
        except Exception as exc:
            logger.warning("Could not send task notification %s: %s", task['id'], exc)


async def check_reminders(bot):
    now = timezone.now()
    window_end = now + timedelta(minutes=1)

    for reminder in await _get_due_reminders(now, window_end):
        try:
            dt_local = reminder['remind_at'].astimezone(TZ)
            text = (
                f"🔔 <b>Eslatma vaqti keldi</b>\n\n"
                f"👋 Salom, <b>{escape(reminder['first_name'])}</b>!\n"
                f"📌 Eslatma: <b>{escape(reminder['title'])}</b>\n"
                f"📅 Sana: <b>{dt_local.strftime('%d-%m-%Y')}</b>\n"
                f"🕒 Vaqt: <b>{dt_local.strftime('%H:%M')}</b>\n\n"
                "✅ Iltimos, ushbu ishni vaqtida bajaring."
            )
            await bot.send_message(reminder['telegram_id'], text, parse_mode='HTML')
            await _mark_reminder_sent(reminder['id'])
            logger.info("Reminder sent: %s -> %s", reminder['title'], reminder['username'])
        except Exception as exc:
            logger.warning("Could not send reminder %s: %s", reminder['id'], exc)


def start_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(send_morning_messages, 'cron', hour=8, minute=0, args=[bot], id='morning_messages')
    scheduler.add_job(check_task_notifications, 'interval', minutes=1, args=[bot], id='task_notifications')
    scheduler.add_job(check_reminders, 'interval', minutes=1, args=[bot], id='reminders_check')
    scheduler.start()
    logger.info("Notification scheduler started (Asia/Tashkent timezone)")
    return scheduler
