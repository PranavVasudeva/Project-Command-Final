import math
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from lib.events import dispatch_events
from lib.db import db
from models.dispatch import IncidentAssignment, IncidentMessage, IncidentMessageCreate, IncidentReport, IncidentReportCreate, IncidentStatusUpdate, IncidentTimelineEvent, ResponseTeam, TeamAvailabilityUpdate, TeamLocationUpdate, TeamRecommendation
from routers.auth import require_user

router = APIRouter(prefix="/dispatch", tags=["dispatch"])


def _role(user: dict) -> str:
    legacy = {"Control Room Officer": "OFFICER", "Civilian / Student": "CIVILIAN", "Response Team": "RESPONSE_TEAM"}
    return legacy.get(user.get("role", ""), user.get("role", "CIVILIAN"))


def _require_role(user: dict, *roles: str) -> None:
    if _role(user) not in roles:
        raise HTTPException(status_code=403, detail="This portal is not available for your account role")


def _timeline(status: str, note: str, user: dict) -> dict:
    return IncidentTimelineEvent(status=status, note=note, actor_name=user["full_name"], actor_role=_role(user), timestamp=datetime.now(timezone.utc)).model_dump()


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _report(document: dict) -> IncidentReport:
    return IncidentReport(**document)


@router.post("/reports", response_model=IncidentReport, status_code=201)
async def create_report(payload: IncidentReportCreate, user: dict = Depends(require_user)):
    _require_role(user, "CIVILIAN")
    now = datetime.now(timezone.utc)
    document = {
        "id": str(uuid.uuid4()),
        "reporter_id": user["id"],
        "reporter_name": user["full_name"],
        **payload.model_dump(),
        "status": "NEW",
        "assigned_team_ids": [],
        "primary_team_id": None,
        "assignment_deadline": None,
        "team_acknowledged_at": None,
        "created_at": now,
        "updated_at": now,
        "timeline": [_timeline("NEW", "Incident submitted to the KIIT control room", user)],
    }
    await db.incident_reports.insert_one(document)
    await dispatch_events.publish("report.created", document["id"])
    return _report(document)


@router.get("/reports", response_model=list[IncidentReport])
async def list_reports(user: dict = Depends(require_user)):
    role = _role(user)
    if role == "CIVILIAN":
        query = {"reporter_id": user["id"]}
    elif role == "RESPONSE_TEAM":
        team = await db.response_teams.find_one({"user_id": user["id"]})
        query = {"assigned_team_ids": team["id"]} if team else {"id": "__none__"}
    elif role == "OFFICER":
        query = {}
    else:
        raise HTTPException(status_code=403, detail="Unknown account role")
    documents = await db.incident_reports.find(query).sort("created_at", -1).to_list(500)
    return [_report(document) for document in documents]


@router.get("/teams", response_model=list[ResponseTeam])
async def list_teams(user: dict = Depends(require_user)):
    _require_role(user, "OFFICER", "RESPONSE_TEAM")
    documents = await db.response_teams.find().sort("name", 1).to_list(100)
    return [ResponseTeam(**document) for document in documents]


@router.get("/events")
async def stream_events(user: dict = Depends(require_user)):
    _require_role(user, "CIVILIAN", "OFFICER", "RESPONSE_TEAM")
    return StreamingResponse(dispatch_events.stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.patch("/teams/me/availability", response_model=ResponseTeam)
async def update_availability(payload: TeamAvailabilityUpdate, user: dict = Depends(require_user)):
    _require_role(user, "RESPONSE_TEAM")
    team = await db.response_teams.find_one({"user_id": user["id"]})
    if not team:
        raise HTTPException(status_code=404, detail="Response team profile not found")
    if team.get("active_incidents", 0) > 0:
        raise HTTPException(status_code=409, detail="Resolve active incidents before changing availability")
    await db.response_teams.update_one({"id": team["id"]}, {"$set": {"status": payload.status}})
    updated = await db.response_teams.find_one({"id": team["id"]})
    await dispatch_events.publish("team.availability", team["id"])
    return ResponseTeam(**updated)


@router.patch("/teams/me/location", response_model=ResponseTeam)
async def update_team_location(payload: TeamLocationUpdate, user: dict = Depends(require_user)):
    _require_role(user, "RESPONSE_TEAM")
    team = await db.response_teams.find_one_and_update({"user_id": user["id"]}, {"$set": payload.model_dump()}, return_document=True)
    if not team:
        raise HTTPException(status_code=404, detail="Response team profile not found")
    await dispatch_events.publish("team.location", team["id"])
    return ResponseTeam(**team)


@router.get("/reports/{report_id}/recommendations", response_model=list[TeamRecommendation])
async def recommend_teams(report_id: str, user: dict = Depends(require_user)):
    _require_role(user, "OFFICER")
    report = await db.incident_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found")
    teams = await db.response_teams.find().to_list(100)
    recommendations = []
    for document in teams:
        team = ResponseTeam(**document)
        distance = _distance_km(report["latitude"], report["longitude"], team.latitude, team.longitude)
        capability_match = report["category"] in team.capabilities
        capability_score = 50 if capability_match else 10
        distance_score = max(0, 30 - round(distance * 5))
        workload_score = max(0, 20 - team.active_incidents * 5)
        availability_penalty = 0 if team.status == "AVAILABLE" else 15 if team.status == "BUSY" else 100
        score = max(0, min(100, capability_score + distance_score + workload_score - availability_penalty))
        reasoning = ["Capability match" if capability_match else "Support capability", f"{distance:.1f} km from incident", f"{team.active_incidents} active assignment(s)", team.status.replace("_", " ").title()]
        recommendations.append(TeamRecommendation(team=team, score=score, distance_km=round(distance, 1), capability_match=capability_match, reasoning=reasoning))
    return sorted(recommendations, key=lambda item: item.score, reverse=True)


@router.post("/reports/{report_id}/assign", response_model=IncidentReport)
async def assign_report(report_id: str, payload: IncidentAssignment, user: dict = Depends(require_user)):
    _require_role(user, "OFFICER")
    report = await db.incident_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found")
    if payload.primary_team_id not in payload.team_ids:
        raise HTTPException(status_code=422, detail="Primary team must be included in assigned teams")
    teams = await db.response_teams.find({"id": {"$in": payload.team_ids}}).to_list(10)
    if len(teams) != len(set(payload.team_ids)):
        raise HTTPException(status_code=422, detail="One or more response teams were not found")
    now = datetime.now(timezone.utc)
    event = _timeline("TEAM_ASSIGNED", payload.note or "Response team assigned by control room", user)
    await db.incident_reports.update_one({"id": report_id}, {"$set": {"status": "TEAM_ASSIGNED", "assigned_team_ids": payload.team_ids, "primary_team_id": payload.primary_team_id, "assignment_deadline": now + timedelta(minutes=2), "team_acknowledged_at": None, "updated_at": now}, "$push": {"timeline": event}})
    await db.response_teams.update_many({"id": {"$in": payload.team_ids}}, {"$set": {"status": "BUSY"}, "$inc": {"active_incidents": 1}})
    updated = await db.incident_reports.find_one({"id": report_id})
    await dispatch_events.publish("report.assigned", report_id)
    return _report(updated)


@router.patch("/reports/{report_id}/status", response_model=IncidentReport)
async def update_report_status(report_id: str, payload: IncidentStatusUpdate, user: dict = Depends(require_user)):
    role = _role(user)
    report = await db.incident_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found")
    if role == "RESPONSE_TEAM":
        team = await db.response_teams.find_one({"user_id": user["id"]})
        if not team or team["id"] not in report.get("assigned_team_ids", []) or payload.status not in {"TEAM_ACCEPTED", "EN_ROUTE", "RESOLVED"}:
            raise HTTPException(status_code=403, detail="Team is not authorized for this incident transition")
    elif role == "OFFICER":
        if payload.status not in {"ACKNOWLEDGED", "EN_ROUTE", "RESOLVED"}:
            raise HTTPException(status_code=422, detail="Unsupported status transition")
    else:
        raise HTTPException(status_code=403, detail="Civilians cannot change incident status")
    now = datetime.now(timezone.utc)
    event = _timeline(payload.status, payload.note or f"Incident moved to {payload.status.replace('_', ' ').title()}", user)
    status_update = {"status": payload.status, "updated_at": now}
    if payload.status == "TEAM_ACCEPTED":
        status_update["team_acknowledged_at"] = now
    await db.incident_reports.update_one({"id": report_id}, {"$set": status_update, "$push": {"timeline": event}})
    if payload.status == "RESOLVED" and report.get("assigned_team_ids"):
        await db.response_teams.update_many({"id": {"$in": report["assigned_team_ids"]}}, {"$set": {"status": "AVAILABLE"}, "$inc": {"active_incidents": -1}})
    updated = await db.incident_reports.find_one({"id": report_id})
    await dispatch_events.publish("report.status", report_id)
    return _report(updated)


@router.post("/reports/{report_id}/escalate", response_model=IncidentReport)
async def escalate_report(report_id: str, user: dict = Depends(require_user)):
    _require_role(user, "OFFICER")
    report = await db.incident_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found")
    previous_teams = report.get("assigned_team_ids", [])
    event = _timeline("ESCALATED", "Unacknowledged dispatch returned to the matching queue", user)
    await db.incident_reports.update_one({"id": report_id}, {"$set": {"status": "ACKNOWLEDGED", "assigned_team_ids": [], "primary_team_id": None, "assignment_deadline": None, "team_acknowledged_at": None, "updated_at": datetime.now(timezone.utc)}, "$push": {"timeline": event}})
    if previous_teams:
        await db.response_teams.update_many({"id": {"$in": previous_teams}, "active_incidents": {"$gt": 0}}, {"$set": {"status": "AVAILABLE"}, "$inc": {"active_incidents": -1}})
    updated = await db.incident_reports.find_one({"id": report_id})
    await dispatch_events.publish("report.escalated", report_id)
    return _report(updated)


async def _authorize_report_access(report_id: str, user: dict) -> dict:
    report = await db.incident_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found")
    role = _role(user)
    if role == "CIVILIAN" and report["reporter_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized for this incident")
    if role == "RESPONSE_TEAM":
        team = await db.response_teams.find_one({"user_id": user["id"]})
        if not team or team["id"] not in report.get("assigned_team_ids", []):
            raise HTTPException(status_code=403, detail="Not assigned to this incident")
    return report


@router.get("/reports/{report_id}/messages", response_model=list[IncidentMessage])
async def list_messages(report_id: str, user: dict = Depends(require_user)):
    await _authorize_report_access(report_id, user)
    documents = await db.incident_messages.find({"report_id": report_id}).sort("created_at", 1).to_list(500)
    return [IncidentMessage(**document) for document in documents]


@router.post("/reports/{report_id}/messages", response_model=IncidentMessage, status_code=201)
async def create_message(report_id: str, payload: IncidentMessageCreate, user: dict = Depends(require_user)):
    await _authorize_report_access(report_id, user)
    document = {"id": str(uuid.uuid4()), "report_id": report_id, "sender_id": user["id"], "sender_name": user["full_name"], "sender_role": _role(user), "message": payload.message.strip(), "created_at": datetime.now(timezone.utc)}
    await db.incident_messages.insert_one(document)
    await dispatch_events.publish("message.created", report_id)
    return IncidentMessage(**document)