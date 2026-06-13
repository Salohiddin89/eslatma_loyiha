from django.contrib import admin
from .models import WeekDay, Task, Reminder
admin.site.register(WeekDay)
admin.site.register(Task)
admin.site.register(Reminder)
