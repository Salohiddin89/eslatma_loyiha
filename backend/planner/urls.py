from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('home/add-day/', views.add_day, name='add_day'),
    path('home/day/<str:day_slug>/', views.day_detail, name='day_detail'),
    path('home/day/<str:day_slug>/update/', views.update_day, name='update_day'),
    path('home/day/<str:day_slug>/add-task/', views.add_task, name='add_task'),
    path('home/day/<str:day_slug>/delete/', views.delete_day, name='delete_day'),
    path('home/task/<int:task_id>/update/', views.update_task, name='update_task'),
    path('home/task/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('home/reminder/add/', views.add_reminder, name='add_reminder'),
    path('home/reminder/<int:reminder_id>/update/', views.update_reminder, name='update_reminder'),
    path('home/reminder/<int:reminder_id>/delete/', views.delete_reminder, name='delete_reminder'),
]
