from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from models.incidents import CampusZone, Incident, IncidentDashboard

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _when(days_ago: int, hours_ago: int = 0, minutes_ago: int = 0) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)


ZONES = [
    CampusZone(id="zone-1", name="KIIT Square Junction", incidents=42, risk_level="CRITICAL", is_highest_risk=True, latitude=20.3533, longitude=85.8188, scope="KIIT", area_note="The primary KIIT hotspot, driven by evening pedestrian and two-wheeler conflict around the square.", peak_hours="17:00–20:00", category_breakdown={"Traffic Accident": 21, "Medical Emergency": 8, "CCTV/Network Glitch": 7, "Campus Disturbance": 6}),
    CampusZone(id="zone-2", name="Campus 3 / Central Library", incidents=18, risk_level="MODERATE", is_highest_risk=False, latitude=20.3524, longitude=85.8171, scope="KIIT", area_note="High footfall around the library approach and cycle stand.", peak_hours="10:00–13:00", category_breakdown={"Asset Theft": 7, "Campus Disturbance": 6, "Medical Emergency": 3, "CCTV/Network Glitch": 2}),
    CampusZone(id="zone-3", name="KIMS Hospital & Medical Gate", incidents=29, risk_level="HIGH", is_highest_risk=False, latitude=20.3498, longitude=85.8175, scope="KIIT", area_note="Medical response corridor with frequent ambulance and visitor movement.", peak_hours="08:00–11:00", category_breakdown={"Medical Emergency": 14, "Traffic Accident": 8, "CCTV/Network Glitch": 4, "Campus Disturbance": 3}),
    CampusZone(id="zone-4", name="KSOM & Campus 7 Gate", incidents=12, risk_level="LOW", is_highest_risk=False, latitude=20.3560, longitude=85.8214, scope="KIIT", area_note="Lower-volume academic gate with occasional queue congestion.", peak_hours="08:00–09:30", category_breakdown={"Campus Disturbance": 5, "CCTV/Network Glitch": 4, "Traffic Accident": 3}),
    CampusZone(id="zone-5", name="Hostel Zone 15 & QC Square", incidents=24, risk_level="HIGH", is_highest_risk=False, latitude=20.3589, longitude=85.8162, scope="KIIT", area_note="Hostel lane sees evening traffic, theft reports and fire-safety alerts.", peak_hours="18:00–22:00", category_breakdown={"Fire Hazard": 7, "Traffic Accident": 6, "Asset Theft": 6, "Medical Emergency": 5}),
    CampusZone(id="zone-6", name="Campus 6 & Law School", incidents=15, risk_level="MODERATE", is_highest_risk=False, latitude=20.3572, longitude=85.8144, scope="KIIT", area_note="Event-led crowd surges and sports-related medical calls.", peak_hours="16:00–19:00", category_breakdown={"Medical Emergency": 6, "Campus Disturbance": 5, "Fire Hazard": 2, "CCTV/Network Glitch": 2}),
    CampusZone(id="zone-7", name="Patia & Infocity Junction", incidents=31, risk_level="HIGH", is_highest_risk=False, latitude=20.3585, longitude=85.8115, scope="Bhubaneswar", area_note="Dense commuter corridor serving Infocity, Patia and north Bhubaneswar.", peak_hours="08:30–10:30", category_breakdown={"Traffic Accident": 17, "Medical Emergency": 5, "Campus Disturbance": 5, "CCTV/Network Glitch": 4}),
    CampusZone(id="zone-8", name="Jayadev Vihar Overbridge", incidents=38, risk_level="CRITICAL", is_highest_risk=False, latitude=20.3021, longitude=85.8239, scope="Bhubaneswar", area_note="High-speed interchange with recurring peak-hour traffic incidents.", peak_hours="18:00–21:00", category_breakdown={"Traffic Accident": 25, "Medical Emergency": 7, "Campus Disturbance": 4, "CCTV/Network Glitch": 2}),
    CampusZone(id="zone-9", name="Master Canteen & Station Area", incidents=29, risk_level="HIGH", is_highest_risk=False, latitude=20.2667, longitude=85.8436, scope="Bhubaneswar", area_note="Transit-heavy zone around Bhubaneswar railway station and Master Canteen.", peak_hours="17:00–22:00", category_breakdown={"Traffic Accident": 12, "Asset Theft": 8, "Medical Emergency": 5, "Campus Disturbance": 4}),
    CampusZone(id="zone-10", name="Rasulgarh Square / NH16", incidents=40, risk_level="CRITICAL", is_highest_risk=False, latitude=20.3051, longitude=85.8672, scope="Bhubaneswar", area_note="Major NH16 junction with high commercial and through-traffic volume.", peak_hours="08:00–11:00", category_breakdown={"Traffic Accident": 24, "Medical Emergency": 7, "Fire Hazard": 5, "Campus Disturbance": 4}),
    CampusZone(id="zone-11", name="Khandagiri Square", incidents=24, risk_level="HIGH", is_highest_risk=False, latitude=20.2589, longitude=85.7865, scope="Bhubaneswar", area_note="Tourism and highway traffic converge around the Khandagiri junction.", peak_hours="16:00–19:00", category_breakdown={"Traffic Accident": 15, "Medical Emergency": 4, "Campus Disturbance": 3, "CCTV/Network Glitch": 2}),
    CampusZone(id="zone-12", name="Saheed Nagar Market", incidents=19, risk_level="MODERATE", is_highest_risk=False, latitude=20.2885, longitude=85.8453, scope="Bhubaneswar", area_note="Busy retail area with crowd management and property-safety reports.", peak_hours="18:00–21:00", category_breakdown={"Asset Theft": 8, "Campus Disturbance": 5, "Traffic Accident": 4, "Medical Emergency": 2}),
]

ZONE_BY_ID = {zone.id: zone for zone in ZONES}


def _event(
    incident_id: str,
    zone_id: str,
    category: str,
    title: str,
    severity: str,
    status: str,
    days_ago: int,
    hours_ago: int,
    dispatch_unit: str,
    resolution_minutes: int,
    description: str,
) -> Incident:
    zone = ZONE_BY_ID[zone_id]
    return Incident(
        id=incident_id,
        category=category,
        title=title,
        zone_id=zone_id,
        zone_name=zone.name,
        severity=severity,
        status=status,
        occurred_at=_when(days_ago, hours_ago),
        dispatch_unit=dispatch_unit,
        resolution_minutes=resolution_minutes,
        description=description,
        latitude=zone.latitude,
        longitude=zone.longitude,
    )


DEMO_INCIDENTS = [
    _event("INC-2601", "zone-1", "Traffic Accident", "Two-wheeler collision at KIIT Square", "CRITICAL", "Dispatched", 0, 1, "KIIT Unit Alpha", 18, "A representative minor collision affecting the northbound approach; the campus response team is on scene."),
    _event("INC-2602", "zone-3", "Medical Emergency", "Student assistance at KIMS gate", "HIGH", "Resolved", 0, 4, "KIMS Medical 02", 11, "First-aid response completed with a direct handoff to the medical gate."),
    _event("INC-2603", "zone-8", "Traffic Accident", "Overbridge lane obstruction", "CRITICAL", "Dispatched", 0, 7, "City Traffic 14", 27, "A stalled vehicle has reduced the Jayadev Vihar overbridge to a single moving lane."),
    _event("INC-2604", "zone-10", "Traffic Accident", "NH16 merge collision", "HIGH", "Investigating", 1, 2, "City Patrol 09", 34, "Two vehicles reported a low-speed merge collision near Rasulgarh Square."),
    _event("INC-2605", "zone-1", "CCTV/Network Glitch", "Camera cluster intermittent", "MEDIUM", "Monitoring", 1, 5, "KIIT Tech 04", 26, "Perimeter camera feeds around KIIT Square are being monitored after packet loss."),
    _event("INC-2606", "zone-7", "Campus Disturbance", "Patia commuter queue spillover", "MEDIUM", "Resolved", 1, 8, "Patia Patrol 03", 22, "Peak-hour footfall temporarily extended into the service lane near Infocity."),
    _event("INC-2607", "zone-2", "Asset Theft", "Unattended cycle reported", "MEDIUM", "Investigating", 2, 3, "KIIT Security 07", 39, "CCTV review started for the cycle stand near Central Library."),
    _event("INC-2608", "zone-9", "Asset Theft", "Luggage complaint near station", "HIGH", "Investigating", 2, 6, "Railway Security 02", 31, "A representative luggage complaint is under camera review at the station approach."),
    _event("INC-2609", "zone-5", "Fire Hazard", "Hostel kitchen smoke alert", "HIGH", "Resolved", 3, 1, "KIIT Fire 01", 9, "Cooking smoke was isolated; no spread or injury was reported."),
    _event("INC-2610", "zone-11", "Medical Emergency", "Tourist assistance request", "MEDIUM", "Resolved", 3, 4, "Medical Unit 06", 17, "Heat-related assistance was provided near Khandagiri Square."),
    _event("INC-2611", "zone-1", "Traffic Accident", "Pedestrian crossing alert", "HIGH", "Resolved", 4, 2, "KIIT Unit Alpha", 13, "Crossing support was added during evening peak around KIIT Square."),
    _event("INC-2612", "zone-12", "Campus Disturbance", "Market crowd congestion", "MEDIUM", "Resolved", 4, 6, "Saheed Nagar Beat", 24, "Pedestrian flow was redirected around a congested market entrance."),
    _event("INC-2613", "zone-4", "CCTV/Network Glitch", "Gate camera packet loss", "LOW", "Resolved", 5, 3, "KIIT Tech 02", 31, "A switch reset restored the Campus 7 gate camera."),
    _event("INC-2614", "zone-8", "Medical Emergency", "Roadside assistance dispatched", "HIGH", "Resolved", 5, 5, "Medical Unit 03", 19, "Medical support was provided near the overbridge slip road."),
    _event("INC-2615", "zone-6", "Campus Disturbance", "Event exit crowd surge", "MEDIUM", "Resolved", 6, 2, "KIIT Unit Delta", 27, "Event attendees were redistributed across two campus exits."),
    _event("INC-2616", "zone-3", "Traffic Accident", "Medical gate bay obstruction", "MEDIUM", "Resolved", 6, 7, "KIIT Unit Bravo", 20, "A stopped vehicle was removed from the KIMS gate approach."),
    _event("INC-2617", "zone-10", "Fire Hazard", "Commercial vehicle smoke report", "HIGH", "Resolved", 8, 1, "City Fire 05", 23, "A commercial vehicle was isolated and checked near the NH16 junction."),
    _event("INC-2618", "zone-5", "Asset Theft", "Helmet missing from stand", "MEDIUM", "Investigating", 9, 4, "KIIT Security 03", 44, "Security is reviewing hostel stand access and nearby cameras."),
    _event("INC-2619", "zone-7", "Traffic Accident", "Infocity signal near-miss", "HIGH", "Resolved", 11, 2, "Patia Patrol 03", 16, "Traffic marshals restored lane discipline after a reported near-miss."),
    _event("INC-2620", "zone-9", "Medical Emergency", "Passenger assistance at station", "MEDIUM", "Resolved", 12, 5, "Railway Medical 01", 14, "A passenger received first aid near the station forecourt."),
    _event("INC-2621", "zone-1", "Medical Emergency", "Minor fall near food court", "MEDIUM", "Resolved", 14, 3, "KIMS Medical 02", 10, "On-site care was provided and the student was escorted for observation."),
    _event("INC-2622", "zone-12", "Asset Theft", "Phone complaint in market lane", "LOW", "Resolved", 16, 6, "Saheed Nagar Beat", 36, "The device was located after a short CCTV and merchant review."),
    _event("INC-2623", "zone-11", "Traffic Accident", "Khandagiri queue collision", "MEDIUM", "Resolved", 19, 4, "City Traffic 11", 21, "A low-speed queue collision was cleared from the square approach."),
    _event("INC-2624", "zone-2", "Campus Disturbance", "Library gate congestion", "LOW", "Resolved", 21, 2, "KIIT Unit Bravo", 12, "The queue was split into two pedestrian lanes and normal flow restored."),
    _event("INC-2625", "zone-8", "CCTV/Network Glitch", "Traffic camera sync delay", "LOW", "Monitoring", 24, 5, "City Tech 08", 40, "A traffic recorder is under observation after a time-sync delay."),
    _event("INC-2626", "zone-10", "Traffic Accident", "Late-night lane scrape", "MEDIUM", "Resolved", 27, 3, "City Patrol 09", 18, "Vehicles were moved to the shoulder and the NH16 lane reopened."),
]


@router.get("", response_model=IncidentDashboard)
async def get_incidents(
    range_key: str = Query(default="all", alias="range"),
    category: str = Query(default="all"),
):
    now = datetime.now(timezone.utc)
    cutoff = {"24h": now - timedelta(hours=24), "7d": now - timedelta(days=7), "30d": now - timedelta(days=30)}.get(range_key)
    incidents = [
        incident for incident in DEMO_INCIDENTS
        if (cutoff is None or incident.occurred_at >= cutoff)
        and (category.lower() == "all" or incident.category.lower() == category.lower())
    ]
    return IncidentDashboard(
        incidents=incidents,
        zones=ZONES,
        total_incidents=sum(zone.incidents for zone in ZONES),
        filtered_incidents=len(incidents),
        high_risk_zone_id="zone-1",
        generated_at=now,
    )