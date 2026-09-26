import uuid

from tests.conftest import login_client


def test_civilian_signup_forces_civilian_role_and_rejects_wrong_portal(client):
    """Civilian self-signup always writes CIVILIAN; officer/team portal selection is server-checked."""
    email = f"tscheck-auth-{uuid.uuid4().hex[:10]}@kiit.ac.in"
    response = client.post("/auth/signup", json={"full_name": "TS Check Civilian", "email": email, "password": "tscheckpass123"})
    assert response.status_code == 200, response.text
    user = response.json()
    assert user["email"] == email
    assert user["role"] == "CIVILIAN"
    token = response.cookies.get("kiit_session")
    if token:
        client.cookies.clear()
        client.cookies.set("kiit_session", token)

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == user["id"]

    invalid = client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert invalid.status_code == 401
    assert "Invalid email or password" in invalid.text

    # Same account, correct password, but wrong portal selection must be rejected server-side.
    wrong_portal = client.post("/auth/login", json={"email": email, "password": "tscheckpass123", "portal_role": "OFFICER"})
    assert wrong_portal.status_code == 403, wrong_portal.text

    right_portal = login_client(client, email, "tscheckpass123", "CIVILIAN")
    assert right_portal.status_code == 200
    assert right_portal.json()["role"] == "CIVILIAN"


def test_seeded_officer_can_login_with_correct_portal_and_wrong_portal_is_rejected(client):
    """Seeded officer account: correct portal opens session, mismatched portal is a 403, not silently accepted."""
    response = login_client(client, "control@kiit.ac.in", "KIIT-Control-2026-Shield", "OFFICER")
    assert response.status_code == 200, response.text
    assert response.json()["role"] == "OFFICER"
    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "control@kiit.ac.in"

    wrong_portal = client.post("/auth/login", json={"email": "control@kiit.ac.in", "password": "KIIT-Control-2026-Shield", "portal_role": "RESPONSE_TEAM"})
    assert wrong_portal.status_code == 403, wrong_portal.text

