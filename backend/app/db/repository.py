import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql+psycopg://{user}:{password}@{host}:{port}/{db}".format(
    user=os.getenv("POSTGRES_USER", "weather"), password=os.getenv("POSTGRES_PASSWORD", "weather"),
    host=os.getenv("POSTGRES_HOST", "localhost"), port=os.getenv("POSTGRES_PORT", "5432"), db=os.getenv("POSTGRES_DB", "weather"))
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
_memory: dict[str, dict[str, Any]] = {}


def _as_event(row: dict[str, Any]) -> dict[str, Any]:
    row["evidence"] = row.get("evidence", [])
    return row


def save_event(event: dict[str, Any]) -> None:
    _memory[str(event["event_id"])] = event
    try:
        with engine.begin() as conn:
            conn.execute(text("""INSERT INTO weather_events
              (event_id,source,event_type,description,latitude,longitude,location,location_name,state,district,timestamp,verification_status,confidence_score,verification_reason,image_url,ai_verdict)
              VALUES (:event_id,:source,:event_type,:description,:latitude,:longitude,
                CASE WHEN :latitude IS NULL OR :longitude IS NULL THEN NULL ELSE ST_SetSRID(ST_MakePoint(:longitude,:latitude),4326)::geography END,
                :location_name,:state,:district,:timestamp,:verification_status,:confidence_score,:verification_reason,:image_url,:ai_verdict)
              ON CONFLICT (event_id) DO UPDATE SET verification_status=EXCLUDED.verification_status, confidence_score=EXCLUDED.confidence_score, verification_reason=EXCLUDED.verification_reason, updated_at=NOW()"""), event)
            conn.execute(text("INSERT INTO verification_results (event_id,verdict,confidence,reasoning,model_name,evidence_ids) VALUES (:event_id,:verdict,:confidence,:reasoning,:model_name,'[]')"), {
                "event_id": event["event_id"], "verdict": event["verification_status"], "confidence": event["confidence_score"], "reasoning": event["verification_reason"], "model_name": event.get("model_name", "local-heuristic")})
            for item in event.get("evidence", []):
                conn.execute(text("INSERT INTO evidence(event_id,source,title,content,similarity_score,rerank_score,evidence_type) VALUES(:event_id,:source,:title,:content,:similarity_score,:rerank_score,'RETRIEVED')"), {"event_id": event["event_id"], **item})
    except SQLAlchemyError:
        pass


def list_events(filters: dict[str, Any]) -> list[dict[str, Any]]:
    # Memory is the resilient local-development fallback; DB is the canonical Docker path.
    values = list(_memory.values())
    for key in ("event_type", "verification_status", "state", "district", "source"):
        if filters.get(key): values = [e for e in values if str(e.get(key, "")).upper() == str(filters[key]).upper()]
    if filters.get("min_confidence") is not None: values = [e for e in values if e["confidence_score"] >= filters["min_confidence"]]
    return sorted(values, key=lambda x: x["timestamp"], reverse=True)


def get_event(event_id: UUID) -> dict[str, Any] | None:
    return _memory.get(str(event_id))


def review_event(event_id: UUID, verdict: str, reviewer: str, reason: str) -> dict[str, Any] | None:
    event = get_event(event_id)
    if not event: return None
    event.update({"verification_status": verdict, "human_verdict": verdict, "reviewer": reviewer, "verification_reason": reason})
    save_event(event)
    try:
        with engine.begin() as conn:
            conn.execute(text("UPDATE weather_events SET human_verdict=:v, reviewer=:r, review_time=NOW(), verification_status=:v, verification_reason=:reason WHERE event_id=:id"), {"v": verdict, "r": reviewer, "reason": reason, "id": event_id})
    except SQLAlchemyError: pass
    return event
