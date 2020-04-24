echo "Waiting for 5 seconds.."
    sleep 5

echo "Migrating Database"
    python manage.py migrate

if [ "$BACKGROUND_ENV" = "web" ]; then
    echo "Starting web.."
    echo "Collect static files"
    python manage.py collectstatic --no-input

    echo "Starting Nginx"
    nginx

    echo "Starting Gunicorn"
    gunicorn interest_miner_api.wsgi:application -b 0.0.0.0:8000 --log-level info --timeout 600

elif [ "$BACKGROUND_ENV" = "worker" ]; then
    echo "Starting Worker.."
    celery --pidfile=/opt/celeryd.pid worker --app=interest_miner_api -l info

else
    echo "Unknown environment"
fi