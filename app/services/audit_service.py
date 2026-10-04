"""Admin audit trail: one row per state-changing admin action."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AdminAuditLog


def record_admin_action(
    session: AsyncSession,
    admin_id: str,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    detail: Optional[str] = None,
) -> None:
    """
    Queue an audit row in the caller's session so it commits (or rolls back) together
    with the action itself. Pass identifiers only; never names, emails or phone numbers.
    """
    session.add(AdminAuditLog(
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail[:255] if detail else None,
    ))
