from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.teams.models import Team


class Customer(models.Model):
    class Tier(models.TextChoices):
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"
        ENTERPRISE = "enterprise", "Enterprise"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="customers")
    external_id = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    tier = models.CharField(max_length=32, choices=Tier.choices, default=Tier.STANDARD)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "email"],
                name="unique_customer_email_per_team",
            ),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"


class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        OPEN = "open", "Open"
        PENDING_CUSTOMER = "pending_customer", "Pending Customer"
        PENDING_INTERNAL = "pending_internal", "Pending Internal"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class SlaRiskLevel(models.TextChoices):
        NONE = "none", "None"
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class Intent(models.TextChoices):
        REFUND_REQUEST = "refund_request", "Refund Request"
        SHIPPING_DELAY = "shipping_delay", "Shipping Delay"
        PRODUCT_QUESTION = "product_question", "Product Question"
        ACCOUNT_ACCESS = "account_access", "Account Access"
        BILLING_ISSUE = "billing_issue", "Billing Issue"
        CANCELLATION = "cancellation", "Cancellation"
        BUG_REPORT = "bug_report", "Bug Report"
        COMPLAINT = "complaint", "Complaint"
        OTHER = "other", "Other"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="tickets")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="tickets")
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.NEW)
    priority = models.CharField(max_length=32, choices=Priority.choices, default=Priority.NORMAL)
    intent = models.CharField(max_length=64, choices=Intent.choices, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
    )
    sla_due_at = models.DateTimeField(blank=True, null=True)
    sla_risk_level = models.CharField(
        max_length=32,
        choices=SlaRiskLevel.choices,
        default=SlaRiskLevel.NONE,
    )
    sentiment = models.CharField(max_length=64, blank=True)
    needs_escalation = models.BooleanField(default=False)
    classification_reason = models.TextField(blank=True)
    classified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.subject

    @property
    def is_closed(self) -> bool:
        return self.status in {self.Status.RESOLVED, self.Status.CLOSED}

    def assign_to(self, user):
        if user is not None and not self.team.has_member(user):
            raise ValueError("Ticket can only be assigned to a member of its team.")
        self.assigned_to = user
        if self.status == self.Status.NEW and user is not None:
            self.status = self.Status.OPEN

    def transition_to(self, status: str):
        valid_statuses = {choice.value for choice in self.Status}
        if status not in valid_statuses:
            raise ValueError(f"{status!r} is not a valid ticket status.")
        self.status = status
        if status in {self.Status.RESOLVED, self.Status.CLOSED}:
            self.closed_at = timezone.now()
        else:
            self.closed_at = None

    def latest_message(self):
        return self.messages.order_by("-created_at").first()


class TicketMessage(models.Model):
    class SenderType(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        AGENT = "agent", "Agent"
        SYSTEM = "system", "System"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        CHAT = "chat", "Chat"
        WEB_FORM = "web_form", "Web Form"
        PHONE_SUMMARY = "phone_summary", "Phone Summary"

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="messages")
    sender_type = models.CharField(max_length=32, choices=SenderType.choices)
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="ticket_messages",
    )
    customer = models.ForeignKey(
        Customer,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="ticket_messages",
    )
    body = models.TextField()
    redacted_body = models.TextField(blank=True)
    channel = models.CharField(max_length=32, choices=Channel.choices, default=Channel.EMAIL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.get_sender_type_display()} message on {self.ticket}"
