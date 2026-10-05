# National Weather Intelligence Platform

A Dockerized MVP that turns citizen and mock weather reports into explainable, geospatial events. It has a complete vertical slice: Kafka topics, normalisation, evidence-aware verification, PostGIS storage, REST/WebSocket APIs, and a live dashboard.

## Run

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`.

Submit a report with `POST /api/reports`; it is published to `weather.raw`, verified, stored, then broadcast at `/ws/events`. The collector emits a demo event every 20 seconds.

## AI design

The `ai-service` seeds Qdrant's `weather_evidence` collection on startup and reranks its retrieval candidates; similarity only supplies candidates, never a truth verdict. The default `local-heuristic` provider makes the prototype fully offline and deterministic; replace its embedding/verifier seams with an Ollama/vLLM Qwen3-Embedding, Qwen3-Reranker, and Qwen3-VL adapter without changing backend contracts. An unavailable vector service degrades safely to an `UNCERTAIN`-leaning result.

## Topics

`weather.raw`, `weather.processed`, `verification.requests`, `verification.results`, `weather.events`, and `weather.dlq` are created/used by the services.
# National-weather-analytics
