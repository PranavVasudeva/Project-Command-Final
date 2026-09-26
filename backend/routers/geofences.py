import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from pymongo import ReturnDocument

from lib.db import db
from models.geofences import Geofence, GeofenceCreate, GeofenceStats, GeofenceUpdate, GeofenceWithStats
from routers.auth import require_user
from routers.incidents import DEMO_INCIDENTS

router = APIRouter(prefix="/geofences", tags=["geofences"])


def _contains(points: list, latitude: float, longitude: float) -> bool:
    inside = False
    previous = len(points) - 1
    for current, point in enumerate(points):
        current_lat, current_lng = point.latitude, point.longitude
        previous_lat, previous_lng = points[previous].latitude, points[previous].longitude
        crosses = (current_lng > longitude) != (previous_lng > longitude)
        if crosses:
            boundary_lat = (previous_lat - current_lat) * (longitude - current_lng) / (previous_lng - current_lng) + current_lat
            if latitude < boundary_lat:
                inside = not inside
        previous = current
    return inside


def _stats(geofence: Geofence) -> GeofenceStats:
    contained = [incident for incident in DEMO_INCIDENTS if _contains(geofence.points, incident.latitude, incident.longitude)]
    weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    weighted = sum(weights.get(incident.severity, 1) for incident in contained)
    categories: dict[str, int] = {}
    for incident in contained:
        categories[incident.category] = categories.get(incident.category, 0) + 1
    average_response = round(sum(incident.resolution_minutes for incident in contained) / len(contained)) if contained else 0
    risk_score = min(100, round((weighted / max(1, len(contained) * 4)) * 70 + min(30, len(contained) * 4))) if contained else 0
    return GeofenceStats(incident_count=len(contained), risk_score=risk_score, average_response_minutes=average_response, category_breakdown=categories)


def _with_stats(document: dict) -> GeofenceWithStats:
    geofence = Geofence(**document)
    return GeofenceWithStats(**geofence.model_dump(), stats=_stats(geofence))


@router.get("", response_model=list[GeofenceWithStats])
async def list_geofences(user: dict = Depends(require_user)):
    documents = await db.geofences.find({"created_by": user["id"]}).sort("updated_at", -1).to_list(100)
    return [_with_stats(document) for document in documents]


@router.post("", response_model=GeofenceWithStats, status_code=201)
async def create_geofence(payload: GeofenceCreate, user: dict = Depends(require_user)):
    now = datetime.now(timezone.utc)
    document = {
        "id": str(uuid.uuid4()),
        **payload.model_dump(),
        "created_by": user["id"],
        "created_at": now,
        "updated_at": now,
    }
    await db.geofences.insert_one(document)
    return _with_stats(document)


@router.put("/{geofence_id}", response_model=GeofenceWithStats)
async def update_geofence(geofence_id: str, payload: GeofenceUpdate, user: dict = Depends(require_user)):
    update = {**payload.model_dump(), "updated_at": datetime.now(timezone.utc)}
    result = await db.geofences.find_one_and_update(
        {"id": geofence_id, "created_by": user["id"]},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Patrol zone not found")
    return _with_stats(result)


@router.delete("/{geofence_id}", status_code=204)
async def delete_geofence(geofence_id: str, response: Response, user: dict = Depends(require_user)):
    result = await db.geofences.delete_one({"id": geofence_id, "created_by": user["id"]})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Patrol zone not found")
    response.status_code = 204