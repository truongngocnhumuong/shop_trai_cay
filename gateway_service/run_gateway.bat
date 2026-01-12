@echo off
set USE_CONSUL=true
set CONSUL_HOST=localhost
set CONSUL_PORT=8500
set SERVICE_ADDRESS=localhost
python manage.py runserver 8005
