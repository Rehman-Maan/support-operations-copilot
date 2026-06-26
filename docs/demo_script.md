# Demo Script

Use this as the storyboard for a short demo video or GIF.

## Setup

Seed ecommerce demo data:

```powershell
docker compose exec web python manage.py seed_ecommerce_demo
```

Log in as:

```text
Agent: demo.agent / DemoPass123!
Lead: demo.lead / DemoPass123!
```

## Walkthrough

1. Open `http://localhost:8000/` and show the operational dashboard.
2. Open the inbox and point out assigned tickets, urgent tickets, SLA risk, and
   pending approval filters.
3. Open an ecommerce ticket and run classification to show intent, priority,
   escalation, sentiment, and reason.
4. Open the knowledge base and show uploaded policy or FAQ documents and macros.
5. Return to the ticket and generate a grounded reply draft.
6. Accept a sensitive refund or cancellation draft to create an approval request.
7. Log in as the support lead and approve or reject the request from `/approvals/`.
8. Return to the ticket to show the audit trail and final timeline.
9. Open `/evaluations/`, run the support-case evaluation, and show metrics.

## Recording Tips

- Keep browser width around 1440 px for the cleanest dashboard and ticket layout.
- Use the seeded ecommerce records so the story feels realistic.
- Mention the safety model: AI suggests and drafts, humans approve sensitive action.
