"""Evidence-grounded verifier.

The provider boundary below deliberately makes this service replaceable by Qwen3-VL
through Ollama/vLLM.  The default uses transparent heuristics so the demo does not
claim a model result when no local model has been provisioned.
"""
from datetime import datetime, timezone
from enum import StrEnum
import re
from fastapi import FastAPI
from pydantic import BaseModel, Field

try:
 from qdrant_client import QdrantClient, models
except ImportError:  # keeps local source inspection runnable before dependencies are installed
 QdrantClient = None

app = FastAPI(title="Weather Verification Service", version="0.1.0")
qdrant = None
COLLECTION = "weather_evidence"

EVIDENCE = [
 {"source":"IMD demo bulletin","title":"Tamil Nadu rainfall advisory","content":"Heavy rainfall and local waterlogging are possible around Madurai and southern Tamil Nadu during the active monsoon period.","location":"Madurai","types":["HEAVY_RAINFALL","FLOOD"]},
 {"source":"IMD demo bulletin","title":"Chennai urban flood watch","content":"Intense rainfall may cause temporary waterlogging in low-lying parts of Chennai.","location":"Chennai","types":["HEAVY_RAINFALL","FLOOD"]},
 {"source":"State disaster management demo","title":"Kerala wind advisory","content":"Strong gusty winds and thunderstorms are forecast across parts of Kerala.","location":"Kerala","types":["STRONG_WIND","THUNDERSTORM"]},
 {"source":"Heat action plan demo","title":"Rajasthan heat advisory","content":"Heatwave conditions are likely in western Rajasthan; residents should take heat precautions.","location":"Rajasthan","types":["HEATWAVE"]},
]

KEYWORDS = {
 "FLOOD": ["flood", "flooding", "waterlogging", "inundat"], "HEAVY_RAINFALL": ["rain", "rainfall", "downpour"],
 "THUNDERSTORM": ["thunder", "storm"], "LIGHTNING": ["lightning"], "CYCLONE": ["cyclone"],
 "HEATWAVE": ["heatwave", "extreme heat", "heat wave"], "COLDWAVE": ["coldwave", "cold wave"],
 "FOG": ["fog"], "DUST_STORM": ["dust storm"], "STRONG_WIND": ["wind", "gust"], "LANDSLIDE": ["landslide"], "DROUGHT": ["drought"]}

class VerifyRequest(BaseModel):
 event_id: str; source: str; text: str; event_type: str = "OTHER"; latitude: float | None = None; longitude: float | None = None
 location_name: str | None = None; timestamp: datetime; image_url: str | None = None; metadata: dict = {}

def embed(text: str) -> list[float]:
 """Deterministic development embedding; swap this seam for Qwen3-Embedding."""
 values = [0.0] * 32
 for token in re.findall(r"[a-z]{2,}", text.lower()): values[hash(token) % len(values)] += 1
 norm = sum(v*v for v in values) ** .5 or 1
 return [v / norm for v in values]

@app.on_event("startup")
def prepare_evidence_collection():
 global qdrant
 if not QdrantClient: return
 try:
  import os
  qdrant = QdrantClient(host=os.getenv("QDRANT_HOST", "localhost"), port=int(os.getenv("QDRANT_PORT", "6333")), timeout=2)
  if not qdrant.collection_exists(COLLECTION):
   qdrant.create_collection(COLLECTION, vectors_config=models.VectorParams(size=32, distance=models.Distance.COSINE))
   qdrant.upsert(COLLECTION, points=[models.PointStruct(id=i, vector=embed(item["content"]), payload=item) for i,item in enumerate(EVIDENCE)])
 except Exception:
  qdrant = None

def infer_type(text: str, requested: str) -> str:
 low = text.lower()
 for name, words in KEYWORDS.items():
  if any(word in low for word in words): return name
 return requested if requested != "OTHER" else "OTHER"

def extract_location(text: str, supplied: str | None) -> tuple[str | None, str | None]:
 known = {"madurai": ("Madurai", "Tamil Nadu"), "chennai": ("Chennai", "Tamil Nadu"), "coimbatore": ("Coimbatore", "Tamil Nadu"), "kerala": ("Kerala", "Kerala"), "rajasthan": ("Rajasthan", "Rajasthan")}
 low = f"{text} {supplied or ''}".lower()
 for key, answer in known.items():
  if key in low: return answer
 return supplied, None

def retrieve(text: str, event_type: str, location: str | None) -> list[dict]:
 if qdrant:
  try:
   hits = qdrant.query_points(COLLECTION, query=embed(text), limit=3).points
   result = []
   for hit in hits:
    item = dict(hit.payload)
    # Vector search provides candidates only; keyword/location reranking remains explicit.
    bonus = (.25 if event_type in item["types"] else 0) + (.15 if location and location.lower() in item["location"].lower() else 0)
    score = max(0, min(1, float(hit.score) + bonus))
    result.append({"source":item["source"], "title":item["title"], "content":item["content"], "similarity_score":round(float(hit.score),2), "rerank_score":round(score,2)})
   if result: return sorted(result, key=lambda x:x["rerank_score"], reverse=True)
  except Exception:
   pass
 tokens = set(re.findall(r"[a-z]{4,}", text.lower()))
 ranked = []
 for item in EVIDENCE:
  overlap = len(tokens & set(re.findall(r"[a-z]{4,}", item["content"].lower()))) / max(1, len(tokens))
  score = overlap + (0.55 if event_type in item["types"] else 0) + (0.35 if location and location.lower() in item["location"].lower() else 0)
  ranked.append((score, item))
 return [{"source": x["source"], "title": x["title"], "content": x["content"], "similarity_score": round(score, 2), "rerank_score": round(score, 2)} for score, x in sorted(ranked, reverse=True, key=lambda p:p[0])[:3] if score > .15]

def duplicate_or_stale(request: VerifyRequest) -> bool:
 # Real deployment uses OCR + pHash; URL hints allow a transparent demo case.
 return bool(request.image_url and any(x in request.image_url.lower() for x in ("old", "archive", "reused")))

@app.get("/health")
def health(): return {"status":"ok", "provider":"local-heuristic", "evidence_documents":len(EVIDENCE)}

@app.post("/verify")
def verify(request: VerifyRequest):
 event_type = infer_type(request.text, request.event_type)
 location, state = extract_location(request.text, request.location_name)
 evidence = retrieve(request.text, event_type, location)
 low = request.text.lower()
 if duplicate_or_stale(request):
  verdict, confidence, reason = "MISLEADING", .72, "The image appears marked as archived or reused. It may depict a real event, but it does not establish this report's time or location."
 elif any(term in low for term in ("no rain", "nothing happened", "false alarm")) and event_type in ("FLOOD", "HEAVY_RAINFALL"):
  verdict, confidence, reason = "REFUTED", .62, "The report's wording contradicts its selected weather-event claim and requires correction."
 elif evidence and evidence[0]["rerank_score"] >= .55:
  verdict, confidence, reason = "SUPPORTED", min(.92, round(.58 + evidence[0]["rerank_score"]*.27, 2)), "Retrieved advisory evidence is geographically and event-type consistent with the report; it supports, but does not independently prove, the observation."
 else:
  verdict, confidence, reason = "UNCERTAIN", .34, "No sufficiently specific trusted evidence was retrieved for the claimed location and time. Human review is recommended."
 return {"verdict": verdict, "confidence": confidence, "event_type": event_type, "location_name": location, "state": state, "district": location, "reason": reason, "evidence": evidence, "model_name": "local-heuristic-v1"}
