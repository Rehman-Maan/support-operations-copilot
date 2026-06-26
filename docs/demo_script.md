# Demo Script

Use this as the storyboard for a short portfolio video or GIF.

Suggested title:

```text
Support Operations Copilot - AI support workflow with human approvals
```

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

## Short Voiceover

This is a support operations copilot for ecommerce teams. It helps agents triage
tickets, draft replies from policy knowledge, and route sensitive actions like
refunds or data deletion through human approval. The goal is faster support
without letting AI make unsafe customer-impacting decisions.

## Walkthrough

1. Open `http://localhost:8000/`.
   Show the dashboard metrics: open tickets, urgent work, SLA risk, and pending
   approvals.

2. Open `/inbox/`.
   Show filters for assigned tickets, urgent tickets, pending approvals, waiting
   on customer, and high SLA risk.

3. Open an ecommerce ticket.
   Run classification and show intent, priority, sentiment, SLA risk, escalation,
   and explanation.

4. Generate a summary.
   Show the copilot panel with internal summary, recommended next step, and macro
   recommendation.

5. Draft a reply.
   Show that the draft is editable and grounded in retrieved knowledge.

6. Trigger a sensitive action.
   Use a refund, cancellation, privacy, or data deletion scenario to show that the
   AI cannot directly execute the action.

7. Log in as `demo.lead`.
   Open `/approvals/` and approve or reject the request.

8. Return to the ticket.
   Show the ticket timeline and approval audit trail.

9. Open `/knowledge/`.
   Show policy documents, ingestion status, chunks, and macros.

10. Open `/evaluations/`.
    Run the support-case evaluation and show classifier, escalation, groundedness,
    latency, and failed-case metrics.

## Suggested Recording Order

Use this order for a 90 to 120 second demo:

1. Dashboard.
2. Inbox.
3. Ticket detail.
4. Copilot summary and draft.
5. Approval queue.
6. Knowledge base.
7. Evaluation dashboard.

## Recording Tips

- Keep browser width around 1440 px for the cleanest dashboard and ticket layout.
- Use the seeded ecommerce records so the story feels realistic.
- Mention the safety model: AI suggests and drafts, humans approve sensitive action.
- Keep the browser zoom at 100%.
- Hide local terminal windows unless you are showing setup commands.
