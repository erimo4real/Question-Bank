#!/usr/bin/env bash
set -o errexit

export DJANGO_ENVIRONMENT=production

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput

# Create super admin + seed data (idempotent)
python manage.py seed || true
python manage.py seed_class_levels || true
python manage.py seed_question_types || true
