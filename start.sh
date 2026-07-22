#!/usr/bin/env bash
set -o errexit

export DJANGO_ENVIRONMENT=production

# Run migrations
python manage.py migrate --noinput

# Seed data (idempotent — safe to run every time)
python manage.py seed || true
python manage.py seed_class_levels || true
python manage.py seed_question_types || true

# Force-reset all passwords + verify DB
python manage.py reset_passwords || true

# Start gunicorn
exec gunicorn config.wsgi:application
