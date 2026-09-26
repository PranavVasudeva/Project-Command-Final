import uuid

import httpx
import pytest

from tests.conftest import API_URL, login_client

OFFICER = {"email": "control@kiit.ac.in", "password": "KIIT-Control-2026-Shield", "portal_role": "OFFICER"}
TEAM = {"email": "security.alpha@kiit.ac.in", "password": "KIIT-Hero-2026-Respond", "portal_role": "RESPONSE_TEAM"}


def _new_civilian(client: httpx.Client) -> dict:
    email = f"tscheck-dispatch-{uuid.uuid4().hex[:10]}@kiit.ac.in"
    response = client.post("/auth/signup", json={"full_name": "TS Check Reporter", "email": email, "password": "tscheckpass123"})
    assert response.status_code == 200, response.text
    token = response.cookies.get("kiit_session")
    if token:
        client.cookies.clear()
        client.cookies.set("kiit_session", token)
    return response.json()


def test_report_lifecycle_ack_score_assign_accept_resolve():
    """Full accountable loop: civilian report -> officer ack+score+assign -> team accept/en-route/resolve."""
    with httpx.Client(base_url=API_URL, timeout=30.0) as civilian:
        _new_civilian(civilian)
        create = civilian.post("/dispatch/reports", json={
            "title": "tscheck-dispatch fire near hostel gate",
            "category": "Fire Hazard",
            "severity": "HIGH",
            "description": "tscheck-dispatch: smoke reported near hostel zone gate, needs urgent review",
            "location_name": "Hostel Zone 15",
            "latitude": 20.3589,
            "longitude": 85.8162,
        })
        assert create.status_code == 201, create.text
        report = create.json()
        assert report["status"] == "NEW"
        assert report["timeline"][0]["status"] == "NEW"
        report_id = report["id"]

        # Civilian cannot list teams or change status - object-level authorization.
        forbidden_teams = civilian.get("/dispatch/teams")
        assert forbidden_teams.status_code == 403
        forbidden_status = civilian.patch(f"/dispatch/reports/{report_id}/status", json={"status": "ACKNOWLEDGED"})
        assert forbidden_status.status_code == 403

    with httpx.Client(base_url=API_URL, timeout=30.0) as officer:
        login = login_client(officer, **OFFICER)
        assert login.status_code == 200, login.text

        ack = officer.patch(f"/dispatch/reports/{report_id}/status", json={"status": "ACKNOWLEDGED", "note": "tscheck ack"})
        assert ack.status_code == 200, ack.text
        assert ack.json()["status"] == "ACKNOWLEDGED"

        recs = officer.get(f"/dispatch/reports/{report_id}/recommendations")
        assert recs.status_code == 200, recs.text
        recommendations = recs.json()
        assert len(recommendations) > 0
        for item in recommendations:
            assert set(["team", "score", "distance_km", "capability_match", "reasoning"]).issubset(item.keys())
        fire_team = next(item for item in recommendations if item["team"]["name"] == "Campus Fire Unit")
        assert fire_team["capability_match"] is True

        assign = officer.post(f"/dispatch/reports/{report_id}/assign", json={"team_ids": [fire_team["team"]["id"]], "primary_team_id": fire_team["team"]["id"], "note": "tscheck assign"})
        assert assign.status_code == 200, assign.text
        assigned = assign.json()
        assert assigned["status"] == "TEAM_ASSIGNED"
        assert assigned["assigned_team_ids"] == [fire_team["team"]["id"]]
        assert assigned["primary_team_id"] == fire_team["team"]["id"]

    with httpx.Client(base_url=API_URL, timeout=30.0) as team:
        login = login_client(team, "fire.response@kiit.ac.in", "KIIT-Hero-2026-Respond", "RESPONSE_TEAM")
        assert login.status_code == 200, login.text

        accept = team.patch(f"/dispatch/reports/{report_id}/status", json={"status": "TEAM_ACCEPTED"})
        assert accept.status_code == 200, accept.text
        assert accept.json()["status"] == "TEAM_ACCEPTED"

        en_route = team.patch(f"/dispatch/reports/{report_id}/status", json={"status": "EN_ROUTE"})
        assert en_route.status_code == 200, en_route.text

        resolve = team.patch(f"/dispatch/reports/{report_id}/status", json={"status": "RESOLVED"})
        assert resolve.status_code == 200, resolve.text
        resolved = resolve.json()
        assert resolved["status"] == "RESOLVED"
        statuses = [event["status"] for event in resolved["timeline"]]
        assert statuses == ["NEW", "ACKNOWLEDGED", "TEAM_ASSIGNED", "TEAM_ACCEPTED", "EN_ROUTE", "RESOLVED"]


def test_officer_can_escalate_unacknowledged_assignment_and_clear_teams():
    """Officer escalation returns a TEAM_ASSIGNED report to ACKNOWLEDGED with teams cleared."""
    with httpx.Client(base_url=API_URL, timeout=30.0) as civilian:
        _new_civilian(civilian)
        create = civilian.post("/dispatch/reports", json={
            "title": "tscheck-escalate theft near library",
            "category": "Asset Theft",
            "severity": "MEDIUM",
            "description": "tscheck-escalate: unattended bag reported missing near the library approach",
            "location_name": "Central Library",
            "latitude": 20.3524,
            "longitude": 85.8171,
        })
        assert create.status_code == 201, create.text
        report_id = create.json()["id"]

    with httpx.Client(base_url=API_URL, timeout=30.0) as officer:
        login = login_client(officer, **OFFICER)
        assert login.status_code == 200, login.text
        officer.patch(f"/dispatch/reports/{report_id}/status", json={"status": "ACKNOWLEDGED"})
        recs = officer.get(f"/dispatch/reports/{report_id}/recommendations").json()
        team_id = recs[0]["team"]["id"]
        assign = officer.post(f"/dispatch/reports/{report_id}/assign", json={"team_ids": [team_id], "primary_team_id": team_id})
        assert assign.status_code == 200
        assert assign.json()["status"] == "TEAM_ASSIGNED"

        escalate = officer.post(f"/dispatch/reports/{report_id}/escalate")
        assert escalate.status_code == 200, escalate.text
        escalated = escalate.json()
        assert escalated["status"] == "ACKNOWLEDGED"
        assert escalated["assigned_team_ids"] == []
        assert escalated["primary_team_id"] is None
        assert escalated["timeline"][-1]["status"] == "ESCALATED"
