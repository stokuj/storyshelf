from django.db import models


class RelationType(models.TextChoices):
    PARENT = "parent", "Parent"
    CHILD = "child", "Child"
    SIBLING = "sibling", "Sibling"
    SPOUSE = "spouse", "Spouse"
    RELATIVE = "relative", "Relative"
    LOVER = "lover", "Lover"
    EX_PARTNER = "ex_partner", "Ex-partner"
    FRIEND = "friend", "Friend"
    ALLY = "ally", "Ally"
    MENTOR = "mentor", "Mentor"
    MENTEE = "mentee", "Mentee"
    MASTER = "master", "Master"
    SERVANT = "servant", "Servant"
    LEADER = "leader", "Leader"
    FOLLOWER = "follower", "Follower"
    ENEMY = "enemy", "Enemy"
    RIVAL = "rival", "Rival"
    COLLEAGUE = "colleague", "Colleague"
    ACQUAINTANCE = "acquaintance", "Acquaintance"
    OTHER = "other", "Other"


# Colour-group membership. Group is derived, never stored on the model.
_GROUP_MEMBERS = {
    "family": (
        RelationType.PARENT,
        RelationType.CHILD,
        RelationType.SIBLING,
        RelationType.SPOUSE,
        RelationType.RELATIVE,
    ),
    "romance": (RelationType.LOVER, RelationType.EX_PARTNER),
    "friendship": (RelationType.FRIEND, RelationType.ALLY),
    "mentorship": (RelationType.MENTOR, RelationType.MENTEE),
    "power": (
        RelationType.MASTER,
        RelationType.SERVANT,
        RelationType.LEADER,
        RelationType.FOLLOWER,
    ),
    "conflict": (RelationType.ENEMY, RelationType.RIVAL),
    "other": (RelationType.COLLEAGUE, RelationType.ACQUAINTANCE, RelationType.OTHER),
}

RELATION_GROUPS = {t: group for group, members in _GROUP_MEMBERS.items() for t in members}


def relation_group(relation_type: str) -> str:
    """Colour-group for a relation type; unknown values map to 'other'."""
    return RELATION_GROUPS.get(relation_type, "other")
