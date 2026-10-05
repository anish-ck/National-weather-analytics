import logging, os
from datetime import datetime
from uuid import UUID

import httpx

from app.db.repository import get_event, save_event
from app.kafka.producer import publish
from app.schemas.events import VerificationRequest
from app.services.broadcaster import broadcaster

logger = logging.getLogger(__name__)

async def verify_and_store(report: VerificationRequest) -> dict:
    existing = get_event(report.event_id)
    if existing:
        return existing
    payload = report.model_dump(mode="json")
    await publish("weather.processed", payload)
    await publish("verification.requests", payload)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{os.getenv('AI_SERVICE_URL', 'http://localhost:8001')}/verify", json=payload)
            response.raise_for_status(); result = response.json()
    except Exception as exc:
        logger.warning("event_id=%s stage=verification status=fallback error=%s", report.event_id, exc)
        result = {"verdict": "UNCERTAIN", "confidence": 0.2, "reason": "Automated verification is temporarily unavailable; human review is required.", "evidence": [], "state": None, "district": None, "event_type": report.event_type.value, "model_name": "unavailable"}
    event = {
        "event_id": str(report.event_id), "source": report.source, "event_type": result.get("event_type", report.event_type.value),
        "description": report.text, "latitude": report.latitude, "longitude": report.longitude,
        "location_name": result.get("location_name") or report.location_name, "state": result.get("state"), "district": result.get("district"),
        "timestamp": report.timestamp.isoformat(), "verification_status": result["verdict"], "confidence_score": result["confidence"],
        "verification_reason": result["reason"], "image_url": report.image_url, "evidence": result.get("evidence", []), "model_name": result.get("model_name", "local-heuristic"), "ai_verdict": result["verdict"]}
    save_event(event)
    await publish("verification.results", {"event_id": str(report.event_id), **result})
    await publish("weather.events", event)
    await broadcaster.broadcast(event)
    logger.info("event_id=%s stage=stored status=%s", report.event_id, result["verdict"])
    return event
