#!/bin/sh
set -eu

python manage.py migrate --noinput
exec daphne -b 0.0.0.0 -p 8080 etewitter.asgi:application
