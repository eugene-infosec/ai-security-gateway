from typing import Optional, Any
from app.logger import log_safe
from app.auth import Principal

def emit_audit_event(
    event_name: str,
    principal: Optional[Principal],
    reason: str,
    extra: dict[str, Any] | None = None
):
    """
    Centralized Audit Emitter.
    Ensures every security decision (Allow/Deny) has the same shape.
    """
    payload = {
        "event": event_name,
        "reason_code": reason,
    }
    
    if principal:
        payload["tenant_id"] = principal.tenant_id
        payload["role"] = principal.role.value
        payload["user"] = principal.user_id
    
    if extra:
        payload.update(extra)
        
    log_safe(payload)