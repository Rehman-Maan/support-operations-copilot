$ErrorActionPreference = "Stop"

docker compose exec -T web python manage.py check
docker compose exec -T web python manage.py makemigrations --check --dry-run
docker compose exec -T web ruff check .
docker compose exec -T web pytest
docker compose exec -T web python manage.py collectstatic --dry-run --noinput -v 0
docker compose exec -T worker celery -A config inspect ping
