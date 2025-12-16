from app.security.principal import resolve_principal_from_headers


def test_resolve_principal_from_headers():
    headers = {"X-User": "u1", "X-Tenant": "t1", "X-Role": "intern"}
    p = resolve_principal_from_headers(headers)
    assert p.user_id == "u1"
    assert p.tenant_id == "t1"
    assert p.role == "intern"


def test_resolve_principal_defaults():
    headers = {}
    p = resolve_principal_from_headers(headers)
    assert p.user_id == "anonymous"
    assert p.tenant_id == "unknown"
    assert p.role == "unknown"
