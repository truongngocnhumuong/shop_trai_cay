@echo off
set USE_CONSUL=true
set SERVICE_ADDRESS=localhost
python manage.py runserver 8006
