from datetime import datetime

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class GeofenceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    points: list[GeoPoint] = Field(min_length=3, max_length=80)
    patrol_owner: str = Field(min_length=2, max_length=80)
    risk_threshold: str = Field(pattern="^(LOW|MODERATE|HIGH|CRITICAL)$")
    notes: str = Field(default="", max_length=500)


class GeofenceUpdate(GeofenceCreate):
    pass


class Geofence(BaseModel):
    id: str
    name: str
    points: list[GeoPoint]
    patrol_owner: str
    risk_threshold: str
    notes: str
    created_by: str
    created_at: datetime
    updated_at: datetime


class GeofenceStats(BaseModel):
    incident_count: int
    risk_score: int
    average_response_minutes: int
    category_breakdown: dict[str, int]


class GeofenceWithStats(Geofence):
    stats: GeofenceStats