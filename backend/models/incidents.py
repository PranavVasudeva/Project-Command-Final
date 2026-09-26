from datetime import datetime

from pydantic import BaseModel


class Incident(BaseModel):
    id: str
    category: str
    title: str
    zone_id: str
    zone_name: str
    severity: str
    status: str
    occurred_at: datetime
    dispatch_unit: str
    resolution_minutes: int
    description: str
    latitude: float
    longitude: float


class CampusZone(BaseModel):
    id: str
    name: str
    incidents: int
    risk_level: str
    is_highest_risk: bool
    latitude: float
    longitude: float
    scope: str
    area_note: str
    peak_hours: str
    category_breakdown: dict[str, int]


class IncidentDashboard(BaseModel):
    incidents: list[Incident]
    zones: list[CampusZone]
    total_incidents: int
    filtered_incidents: int
    high_risk_zone_id: str
    generated_at: datetime