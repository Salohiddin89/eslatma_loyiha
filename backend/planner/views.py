import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import WeekDay, Task, Reminder, WEEKDAYS

WEEKDAY_ORDER = ['dushanba', 'seshanba', 'chorshanba', 'payshanba', 'juma', 'shanba', 'yakshanba']


@login_required
def home(request):
    import pytz
    tz = pytz.timezone('Asia/Tashkent')
    now_local = timezone.now().astimezone(tz)
    # Python weekday: 0=Monday ... 6=Sunday
    dow = now_local.weekday()
    today_slug = WEEKDAY_ORDER[dow]

    weekdays = WeekDay.objects.filter(user=request.user)
    added_days = {wd.day: wd for wd in weekdays}
    today_weekday = added_days.get(today_slug)
    reminders = Reminder.objects.filter(user=request.user, remind_at__gte=timezone.now()).order_by('remind_at')[:5]
    return render(request, 'home/index.html', {
        'weekdays': weekdays,
        'added_days': added_days,
        'all_days': WEEKDAYS,
        'weekday_order': WEEKDAY_ORDER,
        'reminders': reminders,
        'today_slug': today_slug,
        'today_weekday_title': today_weekday.title if today_weekday else '',
    })


@login_required
def day_detail(request, day_slug):
    weekday = get_object_or_404(WeekDay, user=request.user, day=day_slug)
    tasks = weekday.tasks.all()
    return render(request, 'home/day_detail.html', {
        'weekday': weekday,
        'tasks': tasks,
    })


@login_required
@require_POST
def add_day(request):
    data = json.loads(request.body)
    day = data.get('day')
    title = data.get('title', '').strip()
    if not day or not title:
        return JsonResponse({'error': 'Kun va nom kiritilishi shart'}, status=400)
    day_choices = [d[0] for d in WEEKDAYS]
    if day not in day_choices:
        return JsonResponse({'error': "Noto'g'ri kun"}, status=400)
    if WeekDay.objects.filter(user=request.user, day=day).exists():
        return JsonResponse({'error': 'Bu kun allaqachon qo\'shilgan'}, status=400)
    wd = WeekDay.objects.create(user=request.user, day=day, title=title)
    return JsonResponse({'id': wd.id, 'day': wd.day, 'display': wd.get_day_display(), 'title': wd.title})


@login_required
@require_POST
def update_day(request, day_slug):
    data = json.loads(request.body)
    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Kun nomi kiritilishi shart'}, status=400)
    weekday = get_object_or_404(WeekDay, user=request.user, day=day_slug)
    weekday.title = title
    weekday.save(update_fields=['title'])
    return JsonResponse({
        'id': weekday.id,
        'day': weekday.day,
        'display': weekday.get_day_display(),
        'title': weekday.title,
    })


@login_required
@require_POST
def add_task(request, day_slug):
    data = json.loads(request.body)
    title = data.get('title', '').strip()
    time_str = data.get('time', '').strip()
    if not title or not time_str:
        return JsonResponse({'error': 'Vazifa nomi va vaqt kiritilishi shart'}, status=400)
    # Check duplicate time
    weekday = get_object_or_404(WeekDay, user=request.user, day=day_slug)
    if weekday.tasks.filter(time=time_str).exists():
        return JsonResponse({'error': 'Bu vaqtda allaqachon vazifa bor'}, status=400)
    task = Task.objects.create(weekday=weekday, title=title, time=time_str)
    return JsonResponse({'id': task.id, 'title': task.title, 'time': str(task.time)[:5]})


@login_required
@require_POST
def update_task(request, task_id):
    data = json.loads(request.body)
    title = data.get('title', '').strip()
    time_str = data.get('time', '').strip()
    if not title or not time_str:
        return JsonResponse({'error': 'Vazifa nomi va vaqt kiritilishi shart'}, status=400)

    task = get_object_or_404(Task, id=task_id, weekday__user=request.user)
    if task.weekday.tasks.exclude(id=task.id).filter(time=time_str).exists():
        return JsonResponse({'error': 'Bu vaqtda allaqachon vazifa bor'}, status=400)

    task.title = title
    task.time = time_str
    task.notified = False
    task.last_notified_date = None
    task.save(update_fields=['title', 'time', 'notified', 'last_notified_date'])
    return JsonResponse({'id': task.id, 'title': task.title, 'time': str(task.time)[:5]})


@login_required
@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, weekday__user=request.user)
    task.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def delete_day(request, day_slug):
    weekday = get_object_or_404(WeekDay, user=request.user, day=day_slug)
    weekday.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def add_reminder(request):
    data = json.loads(request.body)
    title = data.get('title', '').strip()
    remind_at = data.get('remind_at', '').strip()
    if not title or not remind_at:
        return JsonResponse({'error': 'Eslatma nomi va vaqt kiritilishi shart'}, status=400)
    dt = parse_datetime(remind_at)
    if not dt:
        return JsonResponse({'error': "Vaqt formati noto'g'ri"}, status=400)
    # Make timezone aware
    if timezone.is_naive(dt):
        import pytz
        tz = pytz.timezone('Asia/Tashkent')
        dt = tz.localize(dt)
    if dt <= timezone.now():
        return JsonResponse({'error': "Vaqt o'tib ketgan, kelajakdagi vaqt kiriting"}, status=400)
    r = Reminder.objects.create(user=request.user, title=title, remind_at=dt)
    local_remind_at = timezone.localtime(r.remind_at)
    return JsonResponse({
        'id': r.id,
        'title': r.title,
        'remind_at': local_remind_at.strftime('%d-%m-%Y %H:%M'),
        'remind_at_input': local_remind_at.strftime('%Y-%m-%dT%H:%M'),
    })


@login_required
@require_POST
def update_reminder(request, reminder_id):
    data = json.loads(request.body)
    title = data.get('title', '').strip()
    remind_at = data.get('remind_at', '').strip()
    if not title or not remind_at:
        return JsonResponse({'error': 'Eslatma nomi va vaqt kiritilishi shart'}, status=400)

    dt = parse_datetime(remind_at)
    if not dt:
        return JsonResponse({'error': "Vaqt formati noto'g'ri"}, status=400)
    if timezone.is_naive(dt):
        import pytz
        tz = pytz.timezone('Asia/Tashkent')
        dt = tz.localize(dt)
    if dt <= timezone.now():
        return JsonResponse({'error': "Vaqt o'tib ketgan, kelajakdagi vaqt kiriting"}, status=400)

    reminder = get_object_or_404(Reminder, id=reminder_id, user=request.user)
    reminder.title = title
    reminder.remind_at = dt
    reminder.notified = False
    reminder.save(update_fields=['title', 'remind_at', 'notified'])
    local_remind_at = timezone.localtime(reminder.remind_at)
    return JsonResponse({
        'id': reminder.id,
        'title': reminder.title,
        'remind_at': local_remind_at.strftime('%d-%m-%Y %H:%M'),
        'remind_at_input': local_remind_at.strftime('%Y-%m-%dT%H:%M'),
    })


@login_required
@require_POST
def delete_reminder(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id, user=request.user)
    reminder.delete()
    return JsonResponse({'ok': True})
