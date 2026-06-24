"""
Telegram xabar yuboruvchi — aiogram kerak emas, requests orqali ishlaydi.
Django server ishlaganda avtomatik xabar yuboradi.
Retry mexanizmi bilan — tarmoq muammolarida qayta urinadi.
"""
import logging
import time
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_RETRIES = 3
RETRY_DELAY = 2  # soniya


def send_telegram_message(chat_id: int, text: str) -> bool:
    """
    Telegramga xabar yuboradi.
    True = muvaffaqiyatli, False = xato.
    Tarmoq muammolarida MAX_RETRIES marta qayta urinadi.
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN sozlanmagan!")
        return False

    if not chat_id:
        logger.warning("chat_id bo'sh yoki noto'g'ri: %s", chat_id)
        return False

    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                return True
            elif resp.status_code == 403:
                # Foydalanuvchi botni bloklagan
                logger.warning(
                    "Foydalanuvchi botni bloklagan (chat_id=%s): %s",
                    chat_id, resp.text[:200]
                )
                return False
            elif resp.status_code == 400:
                # Noto'g'ri so'rov (chat_id xato yoki xabar formati noto'g'ri)
                logger.warning(
                    "Telegram API: Noto'g'ri so'rov (chat_id=%s): %s",
                    chat_id, resp.text[:300]
                )
                return False
            else:
                logger.warning(
                    "Telegram API xato (urinish %d/%d): status=%s — %s",
                    attempt, MAX_RETRIES, resp.status_code, resp.text[:200]
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)

        except requests.Timeout:
            logger.warning(
                "Telegram so'rov timeout (urinish %d/%d, chat_id=%s)",
                attempt, MAX_RETRIES, chat_id
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

        except requests.ConnectionError as exc:
            logger.warning(
                "Telegram ulanish xatosi (urinish %d/%d, chat_id=%s): %s",
                attempt, MAX_RETRIES, chat_id, exc
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

        except requests.RequestException as exc:
            logger.warning(
                "Telegram so'rov xatosi (urinish %d/%d, chat_id=%s): %s",
                attempt, MAX_RETRIES, chat_id, exc
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    logger.error(
        "Telegram xabar %d urinishdan keyin ham yuborilmadi (chat_id=%s)",
        MAX_RETRIES, chat_id
    )
    return False
