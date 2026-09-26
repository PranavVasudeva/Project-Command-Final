from datetime import datetime

from pydantic import BaseModel, Field


class IncidentTimelineEvent(BaseModel):
    status: str
    note: str
    actor_name: str
    actor_role: str
    timestamp: datetime


class IncidentReportCreate(BaseModel):
    title: str = Field(min_length=4, max_length=120)
    category: str = Field(min_length=2, max_length=60)
    severity: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    description: str = Field(min_length=10, max_length=1200)
    location_name: str = Field(min_length=2, max_length=140)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    contact: str = Field(default="", max_length=100)
    photo_name: str = Field(default="", max_length=180)


class IncidentReport(BaseModel):
    id: str
    reporter_id: str
    reporter_name: str
    title: str
    category: str
    severity: str
    description: str
    location_name: str
    latitude: float
    longitude: float
    contact: str
    photo_name: str
    status: str
    assigned_team_ids: list[str]
    primary_team_id: str | None
    assignment_deadline: datetime | None = None
    team_acknowledged_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    timeline: list[IncidentTimelineEvent]


class IncidentAssignment(BaseModel):
    team_ids: list[str] = Field(min_length=1, max_length=5)
    primary_team_id: str
    note: str = Field(default="", max_length=300)


class IncidentStatusUpdate(BaseModel):
    status: str = Field(pattern="^(ACKNOWLEDGED|TEAM_ACCEPTED|EN_ROUTE|RESOLVED)$")
    note: str = Field(default="", max_length=300)


class ResponseTeam(BaseModel):
    id: str
    user_id: str
    name: str
    capabilities: list[str]
    latitude: float
    longitude: float
    status: str
    active_incidents: int


class TeamAvailabilityUpdate(BaseModel):
    status: str = Field(pattern="^(AVAILABLE|OFF_DUTY)$")


class TeamLocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class IncidentMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=700)


class IncidentMessage(BaseModel):
    id: str
    report_id: str
    sender_id: str
    sender_name: str
    sender_role: str
    message: str
    created_at: datetime


class TeamRecommendation(BaseModel):
    team: ResponseTeam
    score: int
    distance_km: float
    capability_match: bool
    reasoning: list[str]