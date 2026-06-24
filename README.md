# Kun Tartibi — Deployment Qo'llanmasi

## 🔧 Muammo va Yechim

### Nima uchun hosting'da bot xabarlari kelmadi?

Eski kod `apps.py` `ready()` metodi orqali schedulerni ishga tushirishga harakat qilardi.
Hosting (gunicorn, Anywhere.run) bilan bu ishlamaydi, chunki:

1. **Gunicorn multi-worker** — har bir worker `ready()` ni chaqiradi → scheduler ko'p marta ishga tushadi → konflikt
2. **Procfile yo'q** — hosting qanday ishga tushirishni bilmaydi
3. **Worker jarayon yo'q** — bildirishnoma workeri alohida run bo'lishi kerak

### Tuzatish nimalardan iborat?

| Fayl | O'zgartirish |
|------|-------------|
| `apps.py` | Gunicorn/runserver farqlanishi mustahkamlandi |
| `run_notifications.py` | Aiogram dependency olib tashlandi, to'g'ridan-to'g'ri requests orqali |
| `notification_scheduler.py` | `time__lte` solishtirish tuzatildi |
| `telegram_sender.py` | 3 marta retry mexanizmi qo'shildi |
| `Procfile` | **Yangi** — hosting uchun zarur |
| `requirements.txt` | `gunicorn` qo'shildi |

---

## Anywhere.run'da Deploy

### 1. Environment Variables (Muhit o'zgaruvchilari)

Hosting panelida quyidagi env variable'larni o'rnating:

```
BOT_TOKEN=<sizning_bot_tokeningiz>
SECRET_KEY=<tasodifiy_uzun_kalit>
DEBUG=False
```

### 2. Build Command

```bash
pip install -r requirements.txt && cd backend && python manage.py migrate && python manage.py collectstatic --noinput
```

### 3. Start Command (Web)

```bash
cd backend && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

### 4. Worker Command (Bildirishnomalar uchun)

Agar hosting worker jarayon qo'llab-quvvatlasa (Render, Railway, Heroku):
```bash
cd backend && python manage.py run_notifications
```

---

## Local Test

```bash
# Bir martalik tekshiruv (bot xabar yuboradimi?)
.venv/Scripts/python backend/manage.py run_notifications --once

# Doimiy worker sifatida ishga tushirish
.venv/Scripts/python backend/manage.py run_notifications
```

---

## Muhim Eslatmalar

- **`gunicorn --workers 1`** — Scheduler bir marta ishga tushishi uchun albatta 1 worker ishlatilsin
- **`BOT_TOKEN`** env variable **albatta** hosting'da o'rnatilishi kerak
- Bot foydalanuvchi chat'ini bloklagan bo'lsa, 403 xatosi logga yoziladi (normal holat)
