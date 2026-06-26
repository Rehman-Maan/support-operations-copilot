from django.conf import settings
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_teams",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def membership_for(self, user):
        if not user or not user.is_authenticated:
            return None
        return self.memberships.filter(user=user).first()

    def user_role(self, user) -> str:
        membership = self.membership_for(user)
        return membership.role if membership else ""

    def has_member(self, user) -> bool:
        return self.membership_for(user) is not None

    def user_has_role(self, user, *roles: str) -> bool:
        return self.user_role(user) in roles


class TeamMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        SUPPORT_LEAD = "support_lead", "Support Lead"
        SUPPORT_AGENT = "support_agent", "Support Agent"
        VIEWER = "viewer", "Viewer"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.SUPPORT_AGENT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "user"], name="unique_team_membership"),
        ]
        ordering = ["team__name", "user__username"]

    def __str__(self) -> str:
        return f"{self.user} in {self.team} as {self.get_role_display()}"

    @property
    def can_manage_team(self) -> bool:
        return self.role in {self.Role.OWNER, self.Role.ADMIN}

    @property
    def can_review_approvals(self) -> bool:
        return self.role in {self.Role.OWNER, self.Role.ADMIN, self.Role.SUPPORT_LEAD}

    @property
    def can_work_tickets(self) -> bool:
        return self.role in {
            self.Role.OWNER,
            self.Role.ADMIN,
            self.Role.SUPPORT_LEAD,
            self.Role.SUPPORT_AGENT,
        }
