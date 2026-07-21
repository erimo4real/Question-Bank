#!/usr/bin/env bash
set -o errexit

export DJANGO_ENVIRONMENT=production

# Run migrations
python manage.py migrate --noinput

# Seed data (idempotent — safe to run every time)
python manage.py seed || true
python manage.py seed_class_levels || true
python manage.py seed_question_types || true

# Force-reset all passwords (ensures login works after any DB issue)
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
passwords = {
    'superadmin@example.com': 'superadmin123',
    'admin@greenfieldacademy.com': 'admin123',
    'teacher@greenfieldacademy.com': 'teacher123',
    'admin@abccollage.com': 'admin123',
    'teacher@abccollage.com': 'teacher123',
}
for email, pw in passwords.items():
    try:
        u = User.objects.get(email=email)
        u.set_password(pw)
        u.save()
        print(f'  Reset password for {email}')
    except User.DoesNotExist:
        print(f'  SKIP {email} (not found)')
"

# Start gunicorn
exec gunicorn config.wsgi:application
