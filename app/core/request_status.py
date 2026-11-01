"""Status enums and the single blood-request transition table."""
from enum import Enum


class BloodRequestStatus(str, Enum):
    """Valid blood request statuses."""

    PENDING = "Pending"
    APPROVED = "Approved"
    NOT_APPROVED = "Not_Approved"
    DECLINED = "Declined"
    ONGOING = "Ongoing"
    CLOSED = "Closed"
    EXPIRED = "Expired"


class AdminStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


# Allowed transitions, derived from what the API and scheduler actually do:
#   approve  Pending            -> Approved
#   decline  Pending            -> Declined
#   close    Approved, Expired  -> Closed
#   expire   Pending, Approved, Not_Approved -> Expired   (daily job)
# Declined and Closed are terminal. Ongoing is never assigned by any code path.
TRANSITIONS: dict[BloodRequestStatus, frozenset[BloodRequestStatus]] = {
    BloodRequestStatus.PENDING: frozenset({
        BloodRequestStatus.APPROVED, BloodRequestStatus.DECLINED, BloodRequestStatus.EXPIRED,
    }),
    BloodRequestStatus.NOT_APPROVED: frozenset({BloodRequestStatus.EXPIRED}),
    BloodRequestStatus.APPROVED: frozenset({
        BloodRequestStatus.CLOSED, BloodRequestStatus.EXPIRED,
    }),
    BloodRequestStatus.EXPIRED: frozenset({BloodRequestStatus.CLOSED}),
    BloodRequestStatus.DECLINED: frozenset(),
    BloodRequestStatus.ONGOING: frozenset(),
    BloodRequestStatus.CLOSED: frozenset(),
}


def can_transition(current: str, target: BloodRequestStatus) -> bool:
    try:
        return target in TRANSITIONS[BloodRequestStatus(current)]
    except (ValueError, KeyError):
        return False


def sources_for(target: BloodRequestStatus) -> list[BloodRequestStatus]:
    """Statuses from which `target` may be reached."""
    return [src for src, dsts in TRANSITIONS.items() if target in dsts]
