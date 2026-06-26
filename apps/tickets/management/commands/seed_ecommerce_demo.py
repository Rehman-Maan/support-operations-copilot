from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.approvals.models import ApprovalRequest
from apps.audit.models import AuditEvent
from apps.copilot.models import CopilotSuggestion, RetrievedContext
from apps.knowledge_base.models import KnowledgeChunk, KnowledgeDocument, Macro
from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket, TicketMessage
from services.embeddings.local import embed_text


class Command(BaseCommand):
    help = "Seed an ecommerce support demo workspace with tickets, policies, drafts, and approvals."

    def handle(self, *args, **options):
        agent, lead = self._users()
        team = self._team(agent, lead)
        documents, chunks = self._knowledge(team, agent)
        self._macros(team, agent)
        customers = self._customers(team)
        tickets = self._tickets(team, agent, customers)
        self._suggestions_and_approvals(agent, lead, tickets, chunks)

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded ecommerce demo: "
                f"{len(customers)} customers, {len(tickets)} tickets, "
                f"{len(documents)} documents, {len(chunks)} chunks."
            )
        )
        self.stdout.write("Demo agent: demo.agent / DemoPass123!")
        self.stdout.write("Demo lead: demo.lead / DemoPass123!")

    def _users(self):
        User = get_user_model()
        agent, _ = User.objects.get_or_create(
            username="demo.agent",
            defaults={
                "email": "agent@shopwise.example",
                "first_name": "Maya",
                "last_name": "Agent",
                "is_staff": True,
            },
        )
        lead, _ = User.objects.get_or_create(
            username="demo.lead",
            defaults={
                "email": "lead@shopwise.example",
                "first_name": "Omar",
                "last_name": "Lead",
                "is_staff": True,
            },
        )
        agent.email = "agent@shopwise.example"
        agent.first_name = "Maya"
        agent.last_name = "Agent"
        agent.is_staff = True
        lead.email = "lead@shopwise.example"
        lead.first_name = "Omar"
        lead.last_name = "Lead"
        lead.is_staff = True
        agent.set_password("DemoPass123!")
        lead.set_password("DemoPass123!")
        agent.save(update_fields=["password", "email", "first_name", "last_name", "is_staff"])
        lead.save(update_fields=["password", "email", "first_name", "last_name", "is_staff"])
        return agent, lead

    def _team(self, agent, lead):
        team, _ = Team.objects.get_or_create(
            slug="shopwise-support",
            defaults={"name": "ShopWise Support", "created_by": agent},
        )
        if team.created_by_id != agent.id:
            team.created_by = agent
            team.save(update_fields=["created_by", "updated_at"])
        TeamMembership.objects.update_or_create(
            team=team,
            user=agent,
            defaults={"role": TeamMembership.Role.SUPPORT_AGENT},
        )
        TeamMembership.objects.update_or_create(
            team=team,
            user=lead,
            defaults={"role": TeamMembership.Role.SUPPORT_LEAD},
        )
        return team

    def _knowledge(self, team, user):
        document_payloads = [
            (
                "Refund and Returns Policy",
                KnowledgeDocument.DocumentType.POLICY,
                [
                    (
                        "Refund eligibility",
                        "Refunds for late or missing deliveries require order verification, "
                        "tracking review, and support lead approval before any customer promise.",
                    ),
                    (
                        "Return window",
                        "Most unopened ecommerce items can be returned within 30 days. "
                        "Opened electronics require troubleshooting before return approval.",
                    ),
                ],
            ),
            (
                "Shipping and Delivery Policy",
                KnowledgeDocument.DocumentType.POLICY,
                [
                    (
                        "Delayed shipments",
                        "If tracking has not moved for 72 hours, agents should apologize, "
                        "confirm the shipping address, and open a carrier investigation.",
                    ),
                    (
                        "Premium customers",
                        "Premium customers with missed delivery promises should receive "
                        "priority handling and proactive follow-up within one business day.",
                    ),
                ],
            ),
            (
                "Damaged Item Playbook",
                KnowledgeDocument.DocumentType.TROUBLESHOOTING,
                [
                    (
                        "Damaged goods",
                        "Agents should request photos, packaging condition, and order number. "
                        "Replacement or refund decisions require lead approval if value is high.",
                    ),
                ],
            ),
            (
                "Privacy and Account Requests",
                KnowledgeDocument.DocumentType.POLICY,
                [
                    (
                        "Data requests",
                        "Personal data export and deletion requests must be escalated. "
                        "Agents can acknowledge the request but cannot confirm completion.",
                    ),
                ],
            ),
        ]

        documents = []
        chunks = []
        for title, document_type, chunk_payloads in document_payloads:
            document, _ = KnowledgeDocument.objects.update_or_create(
                team=team,
                title=title,
                defaults={
                    "document_type": document_type,
                    "status": KnowledgeDocument.Status.READY,
                    "uploaded_by": user,
                    "failure_reason": "",
                },
            )
            documents.append(document)
            for index, (section_title, content) in enumerate(chunk_payloads):
                chunk, _ = KnowledgeChunk.objects.update_or_create(
                    document=document,
                    chunk_index=index,
                    defaults={
                        "team": team,
                        "section_title": section_title,
                        "content": content,
                        "source_metadata": {"seed": "ecommerce_demo"},
                        "embedding": embed_text(content),
                    },
                )
                chunks.append(chunk)
        return documents, chunks

    def _macros(self, team, user):
        macros = [
            (
                "Refund acknowledgement",
                Ticket.Intent.REFUND_REQUEST,
                "Thanks for reaching out. I understand you are asking about a refund. "
                "I will verify the order and policy details before confirming the next step.",
            ),
            (
                "Shipping delay update",
                Ticket.Intent.SHIPPING_DELAY,
                "I am sorry your delivery is delayed. I will check tracking and follow up "
                "with the carrier status as soon as possible.",
            ),
            (
                "Damaged item intake",
                Ticket.Intent.COMPLAINT,
                "I am sorry the item arrived damaged. Please share photos of the item and "
                "packaging so we can review the best resolution.",
            ),
        ]
        for name, intent, body in macros:
            Macro.objects.update_or_create(
                team=team,
                name=name,
                defaults={
                    "intent": intent,
                    "body": body,
                    "active": True,
                    "created_by": user,
                },
            )

    def _customers(self, team):
        payloads = [
            ("SW-1001", "Amina Khan", "amina.khan@example.com", Customer.Tier.PREMIUM),
            ("SW-1002", "Daniel Brooks", "daniel.brooks@example.com", Customer.Tier.STANDARD),
            ("SW-1003", "Priya Shah", "priya.shah@example.com", Customer.Tier.ENTERPRISE),
            ("SW-1004", "Sara Ahmed", "sara.ahmed@example.com", Customer.Tier.PREMIUM),
            ("SW-1005", "Noah Williams", "noah.williams@example.com", Customer.Tier.STANDARD),
            ("SW-1006", "Leena Patel", "leena.patel@example.com", Customer.Tier.STANDARD),
        ]
        customers = {}
        for external_id, name, email, tier in payloads:
            customer, _ = Customer.objects.update_or_create(
                team=team,
                email=email,
                defaults={"external_id": external_id, "name": name, "tier": tier},
            )
            customers[external_id] = customer
        return customers

    def _tickets(self, team, agent, customers):
        now = timezone.now()
        ticket_payloads = [
            {
                "key": "late_refund",
                "customer": customers["SW-1001"],
                "subject": "Package never arrived and I want a refund",
                "status": Ticket.Status.PENDING_INTERNAL,
                "priority": Ticket.Priority.HIGH,
                "intent": Ticket.Intent.REFUND_REQUEST,
                "sla_risk_level": Ticket.SlaRiskLevel.MEDIUM,
                "sentiment": "frustrated",
                "needs_escalation": True,
                "classification_reason": "Customer requests a refund for a missing delivery.",
                "sla_due_at": now + timezone.timedelta(hours=6),
                "messages": [
                    (
                        TicketMessage.SenderType.CUSTOMER,
                        "My order ORD-77821 was supposed to arrive last week. "
                        "Tracking has not moved and I want a refund.",
                    ),
                    (
                        TicketMessage.SenderType.SYSTEM,
                        "Carrier tracking has not updated for 96 hours.",
                    ),
                ],
            },
            {
                "key": "shipping_delay",
                "customer": customers["SW-1002"],
                "subject": "Tracking has not updated for my headphones",
                "status": Ticket.Status.OPEN,
                "priority": Ticket.Priority.NORMAL,
                "intent": Ticket.Intent.SHIPPING_DELAY,
                "sla_risk_level": Ticket.SlaRiskLevel.LOW,
                "sentiment": "concerned",
                "needs_escalation": False,
                "classification_reason": "Customer needs delivery status for a delayed shipment.",
                "sla_due_at": now + timezone.timedelta(days=1),
                "messages": [
                    (
                        TicketMessage.SenderType.CUSTOMER,
                        "Hi, my wireless headphones order ORD-77844 still says label created. "
                        "Can someone check what is happening?",
                    ),
                ],
            },
            {
                "key": "damaged_item",
                "customer": customers["SW-1003"],
                "subject": "Espresso machine arrived damaged",
                "status": Ticket.Status.OPEN,
                "priority": Ticket.Priority.URGENT,
                "intent": Ticket.Intent.COMPLAINT,
                "sla_risk_level": Ticket.SlaRiskLevel.HIGH,
                "sentiment": "angry",
                "needs_escalation": True,
                "classification_reason": "Enterprise customer reports a high-value damaged item.",
                "sla_due_at": now + timezone.timedelta(hours=2),
                "messages": [
                    (
                        TicketMessage.SenderType.CUSTOMER,
                        "This is unacceptable. The espresso machine arrived cracked and wet. "
                        "I need a replacement today.",
                    ),
                ],
            },
            {
                "key": "billing_issue",
                "customer": customers["SW-1004"],
                "subject": "Charged twice for one order",
                "status": Ticket.Status.NEW,
                "priority": Ticket.Priority.HIGH,
                "intent": Ticket.Intent.BILLING_ISSUE,
                "sla_risk_level": Ticket.SlaRiskLevel.MEDIUM,
                "sentiment": "worried",
                "needs_escalation": True,
                "classification_reason": (
                    "Customer reports duplicate payment and may need credit adjustment."
                ),
                "sla_due_at": now + timezone.timedelta(hours=8),
                "messages": [
                    (
                        TicketMessage.SenderType.CUSTOMER,
                        "My card was charged twice for order ORD-77890. "
                        "Please fix this before my statement closes.",
                    ),
                ],
            },
            {
                "key": "account_access",
                "customer": customers["SW-1005"],
                "subject": "Cannot log in to track my order",
                "status": Ticket.Status.PENDING_CUSTOMER,
                "priority": Ticket.Priority.NORMAL,
                "intent": Ticket.Intent.ACCOUNT_ACCESS,
                "sla_risk_level": Ticket.SlaRiskLevel.NONE,
                "sentiment": "neutral",
                "needs_escalation": False,
                "classification_reason": "Customer has account access issue.",
                "sla_due_at": now + timezone.timedelta(days=2),
                "messages": [
                    (
                        TicketMessage.SenderType.CUSTOMER,
                        "I forgot my password and the reset email is not arriving.",
                    ),
                    (
                        TicketMessage.SenderType.AGENT,
                        "Please check your spam folder and confirm the email on your account.",
                    ),
                ],
            },
            {
                "key": "data_deletion",
                "customer": customers["SW-1006"],
                "subject": "Delete my ShopWise account data",
                "status": Ticket.Status.PENDING_INTERNAL,
                "priority": Ticket.Priority.URGENT,
                "intent": Ticket.Intent.OTHER,
                "sla_risk_level": Ticket.SlaRiskLevel.HIGH,
                "sentiment": "firm",
                "needs_escalation": True,
                "classification_reason": "Customer requests personal data deletion.",
                "sla_due_at": now + timezone.timedelta(hours=4),
                "messages": [
                    (
                        TicketMessage.SenderType.CUSTOMER,
                        "Please delete my account and all personal data from your store.",
                    ),
                ],
            },
        ]
        tickets = {}
        for payload in ticket_payloads:
            ticket, _ = Ticket.objects.update_or_create(
                team=team,
                customer=payload["customer"],
                subject=payload["subject"],
                defaults={
                    "status": payload["status"],
                    "priority": payload["priority"],
                    "intent": payload["intent"],
                    "assigned_to": agent,
                    "sla_due_at": payload["sla_due_at"],
                    "sla_risk_level": payload["sla_risk_level"],
                    "sentiment": payload["sentiment"],
                    "needs_escalation": payload["needs_escalation"],
                    "classification_reason": payload["classification_reason"],
                    "classified_at": now,
                },
            )
            for sender_type, body in payload["messages"]:
                TicketMessage.objects.get_or_create(
                    ticket=ticket,
                    sender_type=sender_type,
                    body=body,
                    defaults={
                        "customer": payload["customer"]
                        if sender_type == TicketMessage.SenderType.CUSTOMER
                        else None,
                        "sender_user": agent
                        if sender_type == TicketMessage.SenderType.AGENT
                        else None,
                        "channel": TicketMessage.Channel.EMAIL,
                    },
                )
            tickets[payload["key"]] = ticket
        return tickets

    def _suggestions_and_approvals(self, agent, lead, tickets, chunks):
        refund_ticket = tickets["late_refund"]
        refund_suggestion = self._suggestion(
            ticket=refund_ticket,
            content=(
                "Hi Amina,\n\nI am sorry your package has not arrived. I can see the tracking "
                "has been stalled, so I am escalating this for refund review. We need to verify "
                "the order and get support lead approval before confirming a refund.\n\nBest,\n"
                "ShopWise Support"
            ),
            internal_notes="Refund requires order verification and support lead approval.",
            needs_approval=True,
            proposed_sensitive_action="refund",
        )
        self._context(refund_suggestion, chunks[0], 0.08)
        self._approval(
            ticket=refund_ticket,
            suggestion=refund_suggestion,
            requested_by=agent,
            action_type=ApprovalRequest.ActionType.REFUND,
            status=ApprovalRequest.Status.PENDING,
            reason="Customer requested refund for missing delivery. Policy requires lead approval.",
            reply_draft=refund_suggestion.content,
        )

        shipping_ticket = tickets["shipping_delay"]
        shipping_suggestion = self._suggestion(
            ticket=shipping_ticket,
            content=(
                "Hi Daniel,\n\nThanks for checking in. I am sorry the tracking has not updated. "
                "I will review the carrier status and confirm the shipping address so we can "
                "open an investigation if the label remains stalled.\n\nBest,\nShopWise Support"
            ),
            internal_notes="No approval needed. Carrier investigation is the next step.",
            needs_approval=False,
            proposed_sensitive_action="",
        )
        self._context(shipping_suggestion, chunks[2], 0.12)

        data_ticket = tickets["data_deletion"]
        data_suggestion = self._suggestion(
            ticket=data_ticket,
            content=(
                "Hi Leena,\n\nWe received your request to delete your ShopWise account data. "
                "I will route this to the privacy review process. We cannot confirm deletion "
                "until the approved privacy workflow is complete.\n\nBest,\nShopWise Support"
            ),
            internal_notes="Data deletion must be reviewed by a support lead or privacy owner.",
            needs_approval=True,
            proposed_sensitive_action="data_deletion",
        )
        self._context(data_suggestion, chunks[-1], 0.06)
        self._approval(
            ticket=data_ticket,
            suggestion=data_suggestion,
            requested_by=agent,
            action_type=ApprovalRequest.ActionType.DATA_DELETION,
            status=ApprovalRequest.Status.APPROVED,
            reason="Customer requested personal data deletion.",
            reply_draft=data_suggestion.content,
            decided_by=lead,
            decision_note="Approved for privacy workflow intake. Do not promise completion yet.",
        )

    def _suggestion(
        self,
        *,
        ticket,
        content,
        internal_notes,
        needs_approval,
        proposed_sensitive_action,
    ):
        suggestion, _ = CopilotSuggestion.objects.update_or_create(
            ticket=ticket,
            suggestion_type=CopilotSuggestion.SuggestionType.REPLY_DRAFT,
            status=CopilotSuggestion.Status.PROPOSED,
            defaults={
                "content": content,
                "internal_notes": internal_notes,
                "needs_approval": needs_approval,
                "proposed_sensitive_action": proposed_sensitive_action,
                "model_name": "seeded-demo",
                "prompt_version": "ecommerce-demo-v1",
                "created_by_ai": True,
            },
        )
        return suggestion

    def _context(self, suggestion, chunk, relevance_score):
        RetrievedContext.objects.update_or_create(
            suggestion=suggestion,
            knowledge_chunk=chunk,
            defaults={
                "relevance_score": relevance_score,
                "content_snapshot": chunk.content,
                "source_title": chunk.document.title,
            },
        )

    def _approval(
        self,
        *,
        ticket,
        suggestion,
        requested_by,
        action_type,
        status,
        reason,
        reply_draft,
        decided_by=None,
        decision_note="",
    ):
        defaults = {
            "suggestion": suggestion,
            "requested_by": requested_by,
            "status": status,
            "reason": reason,
            "proposed_payload": {
                "suggestion_id": suggestion.id,
                "reply_draft": reply_draft,
                "model_name": suggestion.model_name,
                "prompt_version": suggestion.prompt_version,
                "proposed_sensitive_action": suggestion.proposed_sensitive_action,
            },
            "decided_by": decided_by,
            "decision_note": decision_note,
        }
        if decided_by:
            defaults["decided_at"] = timezone.now()
        approval, _ = ApprovalRequest.objects.update_or_create(
            ticket=ticket,
            action_type=action_type,
            defaults=defaults,
        )
        self._audit_once(
            team=ticket.team,
            ticket=ticket,
            actor_user=requested_by,
            event_type="approval_requested",
            payload={"approval_id": approval.id, "action_type": action_type},
        )
        if decided_by:
            event_type = (
                "approval_approved"
                if status == ApprovalRequest.Status.APPROVED
                else "approval_rejected"
            )
            self._audit_once(
                team=ticket.team,
                ticket=ticket,
                actor_user=decided_by,
                event_type=event_type,
                payload={"approval_id": approval.id, "action_type": action_type},
            )

    def _audit_once(self, *, team, ticket, actor_user, event_type, payload):
        if AuditEvent.objects.filter(
            ticket=ticket,
            event_type=event_type,
            payload=payload,
        ).exists():
            return
        AuditEvent.objects.create(
            team=team,
            ticket=ticket,
            actor_user=actor_user,
            actor_type=AuditEvent.ActorType.USER,
            event_type=event_type,
            payload=payload,
        )
