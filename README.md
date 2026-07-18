# Question Bank Management System

A Django-based question bank management system for schools — create, organize, and manage questions, then generate printable exam papers (PDF, Word, Print).

## Features

- **Multi-school** support with role-based access (Super Admin, Admin, Teacher)
- **Question bank** with MCQ, True/False, Fill-in-blank, Essay, Matching, Ordering, Image-based types
- **Exam paper builder** with drag-and-drop, auto-fill by difficulty, bulk add
- **Export** to PDF (ReportLab), Word (python-docx), and browser print
- **Import/Export** questions via CSV
- **Dashboard** with Chart.js analytics
- **Full-text search** with PostgreSQL `SearchVector`
- **Responsive UI** with Tailwind CSS, HTMX, Alpine.js

## Tech Stack

- Python 3.x + Django 6.0
- PostgreSQL 18
- Django REST Framework (JSON API, browsable API disabled)
- Tailwind CSS (CDN) + HTMX + Alpine.js
- ReportLab + python-docx for exports
- Celery + Redis (configured, no active tasks yet)

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 18
- pip

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd "Question Bank"

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your DB credentials

# Create database
psql -U postgres -c "CREATE DATABASE question_bank;"

# Run migrations
python manage.py migrate

# Seed data (creates super admin + school data)
python manage.py seed

# Run server
python manage.py runserver
```

### Default Users

| Role | Email | Password |
|------|-------|----------|
| Super Admin | superadmin@example.com | superadmin123 |
| School Admin | admin@example.com | admin123 |

### Access the app

- **Web UI**: http://127.0.0.1:8000/
- **API Docs**: http://127.0.0.1:8000/api/docs/
- **Django Admin**: http://127.0.0.1:8000/admin/

## Project Structure

```
Question Bank/
├── apps/
│   ├── accounts/     # User auth, roles, profile
│   ├── dashboard/    # Dashboard with charts
│   ├── papers/       # Exam paper builder + export
│   ├── questions/    # Question CRUD + import/export
│   ├── schools/      # Multi-school management
│   └── subjects/     # Subjects & topics
├── config/
│   └── settings/     # base.py, development.py, production.py
├── templates/        # Django templates (Tailwind + HTMX)
├── static/           # Static files
├── media/            # Uploaded files
└── manage.py
```

## Environment Variables

See `.env.example` for all required variables.

## Deployment

Set `DJANGO_SETTINGS_MODULE=config.settings.production` and configure:
- `SECRET_KEY` — strong random value
- `DB_*` — PostgreSQL credentials
- `ALLOWED_HOSTS` — comma-separated production domains
- `SECURE_SSL_REDIRECT=True` — behind a reverse proxy
- `EMAIL_HOST/USER/PASSWORD` — SMTP for password reset emails

## License

Private — for internal school use.
