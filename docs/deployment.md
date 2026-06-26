# Deployment Notes

These notes describe a production-style deployment for Support Operations
Copilot. The project is designed to run as a Django web process plus Celery
workers backed by PostgreSQL and Redis.

## Required Services

- Django web process running `config.wsgi`
- Celery worker using the same image and environment
- PostgreSQL with pgvector support
- Redis for Celery and Channels
- Persistent media storage for uploaded knowledge documents

## Required Environment

```env
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.example.com
DATABASE_URL=postgres://user:password@host:5432/database
REDIS_URL=redis://host:6379/0
OPENAI_API_KEY=optional-production-key
```

Use managed secrets for production values. Do not commit `.env`.

## Local Production Image

1. Build the image:

   ```powershell
   docker build -f infra/docker/Dockerfile -t support-operations-copilot:release .
   ```

2. Run the quality gate:

   ```powershell
   docker compose exec web python manage.py check
   docker compose exec web python manage.py makemigrations --check --dry-run
   docker compose exec web pytest
   docker compose exec web ruff check .
   ```

## Runtime Commands

Apply database migrations after the new release is available:

```powershell
python manage.py migrate --noinput
```

Collect static files:

```powershell
python manage.py collectstatic --noinput
```

Start the web process:

```powershell
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Start a worker process:

```powershell
celery -A config worker --loglevel=info
```

Confirm the health endpoint:

```text
https://your-domain.example.com/health/
```

Expected response:

```json
{"status": "ok", "service": "support-operations-copilot"}
```

## Suggested Hosting Shape

Any platform that can run a Docker image, PostgreSQL, Redis, and a background
worker should work. Good options include Render, Railway, Fly.io, DigitalOcean,
or a VPS.

Minimum process layout:

- `web`: Gunicorn serving Django.
- `worker`: Celery worker using the same image.
- `postgres`: managed PostgreSQL or pgvector-ready database.
- `redis`: managed Redis instance.
- `media`: persistent storage for uploaded knowledge documents.

## Pre-Deploy Checklist

- `DJANGO_DEBUG=False`.
- `DJANGO_SECRET_KEY` is unique and stored as a secret.
- `DATABASE_URL` points to the production database.
- `REDIS_URL` points to the production Redis instance.
- `DJANGO_ALLOWED_HOSTS` includes only the deployed host.
- `DJANGO_CSRF_TRUSTED_ORIGINS` includes the deployed HTTPS origin.
- `OPENAI_API_KEY` is configured only if model-backed AI features are desired.
- PostgreSQL backups are enabled.
- Uploaded media files are persistent.

## GitHub Actions

The workflow in `.github/workflows/ci.yml` runs Django checks, migration checks,
Ruff, pytest, a Playwright smoke test, the support evaluation smoke suite, Docker
image build, and a Trivy vulnerability scan. The Trivy step is report-only so an
upstream base-image issue does not block portfolio demos.

## Operational Notes

- Keep `DJANGO_DEBUG=False` outside local development.
- Restrict `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to real domains.
- Back up PostgreSQL and uploaded media files.
- Monitor Celery failures because classification, drafting, ingestion, summaries,
  approvals, and evaluations depend on background work.
- Treat OpenAI usage as optional: local heuristic fallbacks keep the app demoable,
  but production-quality drafting and classification should use a configured key.
