web: cd backend && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
worker: cd backend && python manage.py run_notifications
