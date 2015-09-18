web: gunicorn topica:application --log-file=- --timeout=600
worker: celery -A topica worker -l info
flower: celery -A topica.app flower --port=$PORT
