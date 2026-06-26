from .models import Team, TeamMembership


def get_membership(user, team: Team) -> TeamMembership | None:
    return team.membership_for(user)


def can_manage_team(user, team: Team) -> bool:
    membership = get_membership(user, team)
    return bool(membership and membership.can_manage_team)


def can_review_approvals(user, team: Team) -> bool:
    membership = get_membership(user, team)
    return bool(membership and membership.can_review_approvals)


def can_work_tickets(user, team: Team) -> bool:
    membership = get_membership(user, team)
    return bool(membership and membership.can_work_tickets)
