"""OpenAPI and response-shape contract tests."""

from .conftest import RESIDENT_PAYLOAD


def test_openapi_exposes_explicit_resident_response_schema(client):
    schema = client.get("/openapi.json").json()
    components = schema["components"]["schemas"]
    assert "ResidentOut" in components
    assert "QualificationOut" in components
    assert "AuditEventOut" in components

    resident_fields = components["ResidentOut"]["properties"]
    assert set(resident_fields) == {
        "id",
        "first_name",
        "last_name",
        "dob",
        "gender",
        "village",
        "cellphone_no",
        "cellphone_no2",
        "email",
        "qualifications",
        "experiences",
        "skills",
    }


def test_openapi_documents_pagination_and_audit(client):
    schema = client.get("/openapi.json").json()
    list_params = {
        parameter["name"]
        for parameter in schema["paths"]["/api/residents"]["get"]["parameters"]
    }
    assert {"limit", "offset"} <= list_params

    search_params = {
        parameter["name"]
        for parameter in schema["paths"]["/api/search"]["get"]["parameters"]
    }
    assert {"query", "search_type", "limit", "offset"} <= search_params

    audit_params = {
        parameter["name"]
        for parameter in schema["paths"]["/api/audit"]["get"]["parameters"]
    }
    assert {"action", "resident_id", "limit", "offset"} <= audit_params


def test_resident_response_has_only_documented_fields(client):
    created = client.post("/api/residents", json=RESIDENT_PAYLOAD).json()
    assert set(created) == {
        "id",
        "first_name",
        "last_name",
        "dob",
        "gender",
        "village",
        "cellphone_no",
        "cellphone_no2",
        "email",
        "qualifications",
        "experiences",
        "skills",
    }
    assert set(created["qualifications"][0]) == {
        "id",
        "institution",
        "name",
        "type",
        "level",
        "year",
    }


def test_openapi_declares_auth_status_and_health_schemas(client):
    schema = client.get("/openapi.json").json()
    assert schema["paths"]["/api/auth/status"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]["$ref"].endswith("/AuthStatusOut")
    assert schema["paths"]["/health"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"].endswith("/HealthOut")
