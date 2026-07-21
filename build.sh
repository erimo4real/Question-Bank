#!/usr/bin/env bash
set -o errexit

export DJANGO_ENVIRONMENT=production

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput
