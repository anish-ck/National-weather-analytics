CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS weather_events (
  id BIGSERIAL PRIMARY KEY,
  event_id UUID UNIQUE NOT NULL,
  source VARCHAR(80) NOT NULL,
  source_url TEXT,
  event_type VARCHAR(40) NOT NULL,
  description TEXT NOT NULL,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  location GEOGRAPHY(POINT, 4326),
  location_name VARCHAR(255),
  state VARCHAR(100),
  district VARCHAR(100),
  timestamp TIMESTAMPTZ NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  verification_status VARCHAR(20) NOT NULL,
  confidence_score DOUBLE PRECISION NOT NULL,
  verification_reason TEXT NOT NULL,
  image_url TEXT,
  ai_verdict VARCHAR(20),
  human_verdict VARCHAR(20),
  reviewer VARCHAR(100),
  review_time TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_events_status ON weather_events (verification_status);
CREATE INDEX IF NOT EXISTS idx_events_type ON weather_events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_time ON weather_events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_location ON weather_events USING GIST (location);

CREATE TABLE IF NOT EXISTS reports (
  id BIGSERIAL PRIMARY KEY, event_id UUID NOT NULL, source VARCHAR(80) NOT NULL,
  raw_text TEXT NOT NULL, image_url TEXT, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION,
  timestamp TIMESTAMPTZ NOT NULL, metadata JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS evidence (
  id BIGSERIAL PRIMARY KEY, event_id UUID NOT NULL, source VARCHAR(100) NOT NULL,
  source_url TEXT, title TEXT NOT NULL, content TEXT NOT NULL, published_at TIMESTAMPTZ,
  similarity_score DOUBLE PRECISION, rerank_score DOUBLE PRECISION, evidence_type VARCHAR(40), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS verification_results (
  id BIGSERIAL PRIMARY KEY, event_id UUID NOT NULL, verdict VARCHAR(20) NOT NULL,
  confidence DOUBLE PRECISION NOT NULL, reasoning TEXT NOT NULL, model_name VARCHAR(100) NOT NULL,
  evidence_ids JSONB NOT NULL DEFAULT '[]', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
