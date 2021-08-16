release: python manage.py migrateweb: gunicorn config.asgi:application -k uvicorn.workers.UvicornWorkerworker: REMAP_SIGTERM=SIGQUIT celery worker --app=config.celery_app --loglevel=info
beat: REMAP_SIGTERM=SIGQUIT celery beat --app=config.celery_app --loglevel=info
