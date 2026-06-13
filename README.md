# 📅 Kun Tartibi

Haftalik kun tartibi va eslatmalar platformasi.  
**Django sayt** + **Aiogram 3.x Telegram bot** + **SQLite**

---

## 📁 Fayl tuzilmasi

```
project/
├── backend/           ← Django loyiha
│   ├── accounts/      ← Foydalanuvchi modeli, login/register
│   ├── planner/       ← Hafta kunlari, vazifalar, eslatmalar
│   ├── static/        ← CSS, JS
│   ├── templates/     ← HTML shablonlar
│   └── core/          ← settings, urls
├── bot/
│   ├── main.py        ← Bot asosiy fayl
│   └── scheduler.py   ← Vaqtli xabarlar (APScheduler)
└── requirements.txt
```

---

## ⚙️ O'rnatish

```bash
pip install -r requirements.txt
```

---

## 🔑 Bot token sozlash

`backend/core/settings.py` faylida:
```python
TELEGRAM_BOT_TOKEN = 'your-real-token-here'
```
Yoki environment variable:
```bash
export BOT_TOKEN="your-token"
```

---

## 🚀 Ishga tushirish

**1. Migratsiya (birinchi marta):**
```bash
cd backend
python manage.py migrate
python manage.py createsuperuser  # ixtiyoriy
```

**2. Saytni ishga tushirish:**
```bash
cd backend
python manage.py runserver
```
Sayt: http://localhost:8000

**3. Telegram xabar workerini ishga tushirish (alohida terminal):**
```bash
cd backend
python manage.py run_notifications
```
Bu worker bot polling qilmaydi. Saytdagi vazifa va eslatmalarni tekshiradi va Telegram orqali xabar yuboradi.

**4. Bot komandalarini ishga tushirish (ixtiyoriy, alohida terminal):**
```bash
cd bot
python main.py
```

---

## 💬 Bot xabarlari

| Holat | Xabar |
|-------|-------|
| Ertalab 08:00 | `Salom Ali! Bugun Dushanba — Fizika o'rganish kuni. Vazifalar: ...` |
| Vazifa vaqti (masalan 08:15) | `⏰ Salom Ali! Vazifangiz: Kitob sotib olish` |
| Eslatma vaqti | `🔔 Salom Ali! Eslatma: Doktorga borish` |

---

## 📱 Telegram ID olish

Botga `/id` buyrug'ini yuboring yoki `@userinfobot` botidan oling.

---

## 🕐 Vaqt zonasi

Barcha vaqtlar **Asia/Tashkent** (+5 UTC) zonasida ishlaydi.
