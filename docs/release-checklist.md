# Release Checklist

Use this checklist before publishing a demo, recording a walkthrough, or deploying
the app.

## Code Quality

- Run `docker compose exec web python manage.py check`.
- Run `docker compose exec web python manage.py makemigrations --check --dry-run`.
- Run `docker compose exec web ruff check .`.
- Run `docker compose exec web pytest`.
- Run `docker compose exec web python manage.py collectstatic --dry-run --noinput -v 0`.
- Run `docker compose exec worker celery -A config inspect ping`.

## Demo Data

- Run `docker compose exec web python manage.py seed_ecommerce_demo`.
- Confirm `demo.agent / DemoPass123!` can open the inbox.
- Confirm `demo.lead / DemoPass123!` can open approvals.
- Confirm at least one pending approval exists for the demo story.
- Confirm `/evaluations/` can run the support-case evaluation.

## Product Walkthrough

- Dashboard shows queue metrics and recent tickets.
- Inbox filters work.
- Ticket classification updates intent, priority, SLA risk, sentiment, and reason.
- Ticket summary and reply drafting work with local fallback or OpenAI.
- Sensitive drafts create approval requests.
- Support lead can approve or reject.
- Feedback controls render on AI suggestions.
- Knowledge documents and macros render cleanly.

## Security

- `.env` is ignored and not staged.
- No API keys or database dumps are committed.
- `DJANGO_DEBUG=False` is set in production.
- `DJANGO_ALLOWED_HOSTS` is restricted in production.
- `DJANGO_CSRF_TRUSTED_ORIGINS` is set for the deployed domain.
- Production secrets are managed by the hosting platform.

## Deployment

- Docker image builds successfully.
- Database migrations are applied.
- Static files are collected.
- Web process starts with Gunicorn.
- Celery worker starts with the same release image.
- `/health/` returns the expected JSON response.
- PostgreSQL backups and media persistence are configured.

## Portfolio Polish

- README screenshots are current.
- Demo script matches the seeded data.
- GitHub repo description is set.
- Repo visibility is intentional.
- License is present.
- CI status is checked after push.
