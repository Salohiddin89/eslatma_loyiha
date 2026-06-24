"""
Bildirishnoma scheduler — Django server o'zi xabar yuboradi.
Bot alohida run bo'lishi shart emas. requests orqali ishlaydi.
"""
import logging
from datetime import timedelta
from html import escape

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone

from .telegram_sender import send_telegram_message

logger = logging.getLogger(__name__)

TZ = pytz.timezone('Asia/Tashkent')
WEEKDAY_ORDER = ['dushanba', 'seshanba', 'chorshanba', 'payshanba', 'juma', 'shanba', 'yakshanba']


def get_today_slug():
    return WEEKDAY_ORDER[timezone.now().astimezone(TZ).weekday()]


# ─────────────────────────────────────────────
#  Ertalabki xabar (har kuni 08:00 da)
# ─────────────────────────────────────────────
def send_morning_messages():
    """Har kuni ertalab bugungi kun tartibini yuboradi."""
    from accounts.models import User
    from planner.models import WeekDay

    today = get_today_slug()
    users = User.objects.filter(telegram_id__isnull=False).exclude(telegram_id=0)

    for user in users:
        try:
            wd = WeekDay.objects.filter(user=user, day=today).first()
            if wd:
                tasks = list(wd.tasks.all())
                if tasks:
                    task_lines = '\n'.join([
                        f"{i}. 🕒 <b>{str(t.time)[:5]}</b> — {escape(t.title)}"
                        for i, t in enumerate(tasks, 1)
                    ])
                    text = (
                        f"🌅 <b>Bugungi kun tartibi</b>\n\n"
                        f"👋 Salom, <b>{escape(user.first_name)}</b>!\n"
                        f"📅 Kun: <b>{wd.get_day_display()}</b>\n"
                        f"🎯 Reja: <b>{escape(wd.title)}</b>\n"
                        f"📌 Vazifalar: <b>{len(tasks)} ta</b>\n\n"
                        f"📝 <b>Vazifalar:</b>\n{task_lines}"
                    )
                else:
                    text = (
                        f"🌅 <b>Bugungi kun tartibi</b>\n\n"
                        f"👋 Salom, <b>{escape(user.first_name)}</b>!\n"
                        f"📅 Kun: <b>{wd.get_day_display()}</b>\n"
                        f"🎯 Reja: <b>{escape(wd.title)}</b>\n\n"
                        "✅ Bugun uchun vazifa qo'shilmagan."
                    )
            else:
                day_name = today.capitalize()
                text = (
                    f"🌅 <b>Bugungi kun tartibi</b>\n\n"
                    f"👋 Salom, <b>{escape(user.first_name)}</b>!\n"
                    f"📅 Kun: <b>{day_name}</b>\n"
                    "⚠️ Bugun uchun kun tartibi qo'shilmagan."
                )

            if send_telegram_message(user.telegram_id, text):
                logger.info("Ertalabki xabar yuborildi → %s", user.username)
            else:
                logger.warning("Ertalabki xabar yuborilmadi → %s", user.username)

        except Exception as exc:
            logger.error("Ertalabki xabar xatosi (%s): %s", user.username, exc)


# ─────────────────────────────────────────────
#  Vazifa vaqti xabari (har 1 daqiqada)
# ─────────────────────────────────────────────
def check_task_notifications():
    """Vaqti kelgan vazifalar haqida xabar yuboradi."""
    from planner.models import Task

    now_local = timezone.now().astimezone(TZ)
    # HH:MM formatida solishtirish uchun string emas, time objektini ishlatamiz
    current_time = now_local.time().replace(second=0, microsecond=0)
    today_date = now_local.date()
    today = get_today_slug()

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

    for task in tasks:
        try:
            user = task.weekday.user
            task_list = list(task.weekday.tasks.order_by('time'))
            try:
                task_number = task_list.index(task) + 1
            except ValueError:
                task_number = 1
            task_count = len(task_list)

            text = (
                f"⏰ <b>Vazifa vaqti keldi</b>\n\n"
                f"👋 Salom, <b>{escape(user.first_name)}</b>!\n"
                f"📅 Kun: <b>{task.weekday.get_day_display()}</b>\n"
                f"🎯 Reja: <b>{escape(task.weekday.title)}</b>\n"
                f"📌 Vazifa: <b>{task_number}/{task_count}</b>\n\n"
                f"{task_number}. ✅ <b>{escape(task.title)}</b>\n"
                f"🕒 Vaqt: <b>{str(task.time)[:5]}</b>"
            )

            if send_telegram_message(user.telegram_id, text):
                Task.objects.filter(id=task.id).update(
                    notified=True, last_notified_date=today_date
                )
                logger.info("Vazifa xabari yuborildi: %s → %s", task.title, user.username)
            else:
                logger.warning("Vazifa xabari yuborilmadi: %s → %s", task.id, user.username)

        except Exception as exc:
            logger.error("Vazifa xabari xatosi (id=%s): %s", task.id, exc)


# ─────────────────────────────────────────────
#  Eslatma xabari (har 1 daqiqada)
# ─────────────────────────────────────────────
def check_reminders():
    """Vaqti kelgan eslatmalar haqida xabar yuboradi."""
    from planner.models import Reminder

    now = timezone.now()
    window_end = now + timedelta(minutes=1)

    reminders = (
        Reminder.objects.filter(
            notified=False,
            remind_at__lte=window_end,
            user__telegram_id__isnull=False,
        )
        .exclude(user__telegram_id=0)
        .select_related('user')
    )

    for reminder in reminders:
        try:
            user = reminder.user
            dt_local = reminder.remind_at.astimezone(TZ)

            text = (
                f"🔔 <b>Eslatma vaqti keldi</b>\n\n"
                f"👋 Salom, <b>{escape(user.first_name)}</b>!\n"
                f"📌 Eslatma: <b>{escape(reminder.title)}</b>\n"
                f"📅 Sana: <b>{dt_local.strftime('%d-%m-%Y')}</b>\n"
                f"🕒 Vaqt: <b>{dt_local.strftime('%H:%M')}</b>\n\n"
                "✅ Iltimos, ushbu ishni vaqtida bajaring."
            )

            if send_telegram_message(user.telegram_id, text):
                Reminder.objects.filter(id=reminder.id).update(notified=True)
                logger.info("Eslatma yuborildi: %s → %s", reminder.title, user.username)
            else:
                logger.warning("Eslatma yuborilmadi: %s → %s", reminder.id, user.username)

        except Exception as exc:
            logger.error("Eslatma xatosi (id=%s): %s", reminder.id, exc)


# ─────────────────────────────────────────────
#  Schedulerni ishga tushirish
# ─────────────────────────────────────────────
def start_scheduler():
    """
    BackgroundScheduler — Django serveri bilan birga ishlaydi.
    Bot alohida run bo'lishi shart emas.
    """
    scheduler = BackgroundScheduler(timezone=TZ)

    # Har kuni 08:00 da ertalabki xabar
    scheduler.add_job(
        send_morning_messages,
        'cron', hour=8, minute=0,
        id='morning_messages',
        replace_existing=True,
    )

    # Har 1 daqiqada vazifa tekshiruvi
    scheduler.add_job(
        check_task_notifications,
        'interval', minutes=1,
        id='task_notifications',
        replace_existing=True,
    )

    # Har 1 daqiqada eslatma tekshiruvi
    scheduler.add_job(
        check_reminders,
        'interval', minutes=1,
        id='reminders_check',
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✅ Bildirishnoma scheduler ishga tushdi (Asia/Tashkent)")
    return scheduler
