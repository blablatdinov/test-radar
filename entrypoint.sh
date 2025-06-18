python3.12 src/manage.py migrate
python3.12 src/manage.py collectstatic --no-input
cd src && gunicorn server.wsgi:application -w $(nproc) -b 0.0.0.0:8000
