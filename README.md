# Support Operations Copilot

Support Operations Copilot is a Django helpdesk assistant that triages tickets, drafts grounded replies, summarizes conversations, and routes sensitive actions through human approval.

## Problem

Support teams need faster responses without letting AI make unsafe customer-impacting decisions. This project builds a workflow-first copilot that assists agents while keeping humans responsible for final replies and sensitive actions.

## Key Features

- Django backend with DRF, Channels, Celery, PostgreSQL, Redis, and Docker Compose.
- Health check endpoint at `/health/`.
- Split settings for local and production environments.
- Built-in Django login/logout with a protected team dashboard.
- Team and membership models with support roles.
- Ticket inbox with team-scoped queue filters, ticket detail pages, assignment, status
  updates, and message timelines.
- Knowledge base uploads, macros, Celery ingestion, chunking, local embeddings, and
  pgvector-backed team-scoped retrieval.
- Ticket classification with PII redaction, structured AI output parsing, local
  fallback heuristics, SLA risk detection, escalation flags, and audit events.
- Retrieval-grounded reply drafting with source snapshots, approval warnings,
  accept/edit/reject flow, and audit events.
- Human approval workflow for sensitive actions, with support lead queue,
  approve/reject decisions, ticket status updates, and audit events.
- Ticket summaries, recommended next steps, macro recommendations, and a richer
  copilot side panel for agent review.
- Suggestion feedback, failure tags, support-case evaluation runs, and an
  evaluation dashboard for classifier, escalation, and groundedness metrics.
- CI workflow with Django checks, migration checks, Ruff, pytest, Playwright E2E
  smoke coverage, support evaluation smoke run, Docker image build, and Trivy scan.
- Deployment and demo-recording notes.

## Architecture

```text
Browser -> Django/DRF -> PostgreSQL
                  |--> Redis
                  |--> Celery workers
                  |--> AI services
```

## Tech Stack

- Django 5.2
- Django REST Framework
- Django Channels
- Celery
- PostgreSQL with pgvector-ready image
- Redis
- Docker Compose

## Local Setup

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Build and start the services:

```powershell
docker compose up --build
```

PostgreSQL is exposed to the host on port `5433` to avoid common local conflicts,
while containers still connect to it as `postgres:5432`.

In another terminal, run migrations:

```powershell
docker compose exec web python manage.py migrate
```

Open the app:

```text
http://localhost:8000/health/
```

Expected response:

```json
{"status": "ok", "service": "support-operations-copilot"}
```

The protected dashboard is available at:

```text
http://localhost:8000/
```

The agent inbox is available at:

```text
http://localhost:8000/inbox/
```

The knowledge base is available at:

```text
http://localhost:8000/knowledge/
```

Ticket classification can be run from a ticket detail page:

```text
http://localhost:8000/inbox/
```

Reply drafting is also available from the ticket detail page. Drafts are shown
for agent review and can be edited before they are added to the ticket timeline.

The support lead approval queue is available at:

```text
http://localhost:8000/approvals/
```

The evaluation dashboard is available at:

```text
http://localhost:8000/evaluations/
```

To load the ecommerce demo workspace:

```powershell
docker compose exec web python manage.py seed_ecommerce_demo
```

Demo users:

```text
Agent: demo.agent / DemoPass123!
Lead: demo.lead / DemoPass123!
```

Create an admin user before using the Django admin:

```powershell
docker compose exec web python manage.py createsuperuser
```

## Useful Commands

```powershell
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web python manage.py test
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web python manage.py collectstatic --dry-run --noinput -v 0
docker compose exec worker celery -A config inspect ping
docker build -f infra/docker/Dockerfile -t support-operations-copilot:local .
.\scripts\verify.ps1
```

## AI Workflow

Milestone 5 adds ticket classification. Ticket text is redacted before model
classification, parsed against a structured JSON schema, and written back to the
ticket as intent, priority, SLA risk, sentiment, escalation need, and a short
reason. If `OPENAI_API_KEY` is not configured, the app uses a deterministic local
heuristic classifier so development still works offline.

Set these optional environment variables to use OpenAI classification:

```env
OPENAI_API_KEY=your-api-key
OPENAI_CLASSIFICATION_MODEL=gpt-4.1-mini
OPENAI_REPLY_MODEL=gpt-4.1-mini
```

Milestone 6 adds grounded reply drafting. The app retrieves team-scoped
knowledge chunks before drafting, redacts ticket text before model calls, asks
for a structured reply object, stores the suggested reply and retrieved source
snapshots, and records draft lifecycle events in the audit log. If OpenAI is not
configured or a model request fails, the app uses a deterministic local fallback
draft so the workflow remains demoable.

Milestone 7 adds human approval routing. If a reply draft proposes a sensitive
action such as a refund, cancellation, account closure, credit adjustment, data
export, or data deletion, accepting the draft creates an approval request instead
of adding the reply directly to the timeline. Support leads can approve or reject
requests from the approval queue, and each request and decision is audit logged.

Milestone 8 adds the operational copilot panel. Agents can generate an internal
ticket summary, recommended next step, and macro recommendation from the ticket
detail page. Summary generation uses redacted ticket conversation text before
external model calls and falls back to local heuristics when OpenAI is not
configured or fails.

Milestone 9 adds feedback and evaluation. Agents can rate AI suggestions and tag
failure modes from the ticket detail page. The evaluation dashboard can run the
support-case dataset in `eval/datasets/support_cases.yml` and records classifier
F1, escalation precision/recall, groundedness, latency, and failed cases.

Milestone 10 adds testing, CI, and deployment hardening. The GitHub Actions
workflow in `.github/workflows/ci.yml` runs the project quality gate, builds the
Docker image, and performs a Trivy vulnerability scan. Deployment notes are in
`docs/deployment.md`, and a short product demo storyboard is in
`docs/demo_script.md`.

## Human Approval Model

The AI may suggest sensitive actions, but it must not execute or promise refunds,
cancellations, credits, account closures, data exports, or data deletion without
support lead approval.

## Security and Privacy

The project redacts sensitive customer data before external model calls and keeps
an audit trail for AI suggestions, human edits, approvals, and rejections.

## Roadmap

1. Project setup - complete
2. Auth, teams, and roles - complete
3. Ticket inbox - complete
4. Knowledge base - complete
5. Classification - complete
6. Reply drafting - complete
7. Approvals - complete
8. Summaries and copilot panel - complete
9. Feedback and evaluation - complete
10. Testing, CI, and deployment - complete
