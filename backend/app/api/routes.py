from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.db.repository import get_event, list_events, review_event
from app.kafka.producer import publish
from app.schemas.events import AdminVerification, EventType, ReportAccepted, ReportCreate, VerificationRequest, Verdict
from app.services.broadcaster import broadcaster
from app.services.pipeline import verify_and_store

router = APIRouter()

@router.get("/health")
async def health(): return {"status": "ok", "service": "weather-api"}

@router.post("/api/reports", response_model=ReportAccepted, status_code=202)
async def submit_report(report: ReportCreate, tasks: BackgroundTasks):
    verification = VerificationRequest(text=report.text, event_type=report.event_type, latitude=report.latitude, longitude=report.longitude, timestamp=report.timestamp, image_url=report.image_url, location_name=report.location_name)
    body = verification.model_dump(mode="json")
    await publish("weather.raw", body)
    tasks.add_task(verify_and_store, verification)
    return ReportAccepted(event_id=verification.event_id)

@router.get("/api/events")
async def events(event_type: EventType | None = None, verification_status: Verdict | None = None, state: str | None = None, district: str | None = None, source: str | None = None, min_confidence: float | None = Query(None, ge=0, le=1)):
    return list_events({"event_type": event_type, "verification_status": verification_status, "state": state, "district": district, "source": source, "min_confidence": min_confidence})

@router.get("/api/events/nearby")
async def nearby(latitude: float = Query(ge=-90, le=90), longitude: float = Query(ge=-180, le=180), radius_km: float = Query(50, gt=0, le=500)):
    # Haversine check retains offline functionality; PostGIS index is ready for production-scale replacement.
    from math import asin, cos, radians, sin, sqrt
    result = []
    for event in list_events({}):
        if event["latitude"] is None: continue
        dlat, dlon = radians(event["latitude"]-latitude), radians(event["longitude"]-longitude)
        a = sin(dlat/2)**2 + cos(radians(latitude))*cos(radians(event["latitude"]))*sin(dlon/2)**2
        if 6371 * 2 * asin(sqrt(a)) <= radius_km: result.append(event)
    return result

@router.get("/api/events/heatmap")
async def heatmap():
    return [{"latitude": e["latitude"], "longitude": e["longitude"], "weight": e["confidence_score"]} for e in list_events({}) if e["latitude"] is not None]

@router.get("/api/events/{event_id}")
async def event_detail(event_id: UUID):
    event = get_event(event_id)
    if not event: raise HTTPException(404, "Event not found")
    return event

@router.get("/api/evidence/{event_id}")
async def evidence(event_id: UUID):
    event = get_event(event_id)
    if not event: raise HTTPException(404, "Event not found")
    return event.get("evidence", [])

@router.get("/api/statistics")
async def statistics():
    items = list_events({}); counts = {v.value: 0 for v in Verdict}
    types: dict[str, int] = {}; regions: dict[str, int] = {}
    for e in items:
        counts[e["verification_status"]] = counts.get(e["verification_status"], 0) + 1
        types[e["event_type"]] = types.get(e["event_type"], 0) + 1
        if e.get("state"): regions[e["state"]] = regions.get(e["state"], 0) + 1
    return {"total_reports": len(items), "verified_events": sum(counts[k] for k in ("SUPPORTED", "REFUTED", "MISLEADING")), "events_today": len(items), "active_hazards": len([e for e in items if e["verification_status"] == "SUPPORTED"]), "verdicts": counts, "top_event_types": types, "top_affected_regions": regions}

@router.post("/api/admin/events/{event_id}/verify")
async def admin_verify(event_id: UUID, decision: AdminVerification):
    event = review_event(event_id, decision.verdict.value, decision.reviewer, decision.reason)
    if not event: raise HTTPException(404, "Event not found")
    await broadcaster.broadcast(event)
    return event

@router.websocket("/ws/events")
async def websocket_events(socket: WebSocket):
    await broadcaster.connect(socket)
    try:
        while True: await socket.receive_text()
    except WebSocketDisconnect: broadcaster.disconnect(socket)
