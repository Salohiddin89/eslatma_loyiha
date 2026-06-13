from django.db import models
from accounts.models import User

WEEKDAYS = [
    ('dushanba', 'Dushanba'),
    ('seshanba', 'Seshanba'),
    ('chorshanba', 'Chorshanba'),
    ('payshanba', 'Payshanba'),
    ('juma', 'Juma'),
    ('shanba', 'Shanba'),
    ('yakshanba', 'Yakshanba'),
]


class WeekDay(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekdays')
    day = models.CharField(max_length=20, choices=WEEKDAYS)
    title = models.CharField(max_length=200, help_text="Kun nomi, misol: Fizika o'rganish kuni")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'day')
        ordering = ['id']

    def __str__(self):
        return f"{self.user} - {self.get_day_display()}: {self.title}"


class Task(models.Model):
    weekday = models.ForeignKey(WeekDay, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=300)
    time = models.TimeField(help_text="Vazifa vaqti")
    notified = models.BooleanField(default=False)
    last_notified_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['time']

    def __str__(self):
        return f"{self.title} - {self.time}"


class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    title = models.CharField(max_length=300)
    remind_at = models.DateTimeField(help_text="Eslatma vaqti")
    notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['remind_at']

    def __str__(self):
        return f"{self.user} - {self.title} @ {self.remind_at}"
