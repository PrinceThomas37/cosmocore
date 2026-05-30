CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    display_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    birth_time TIME NOT NULL,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    timezone_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS astrology_profiles (
    profile_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    western_planets JSONB NOT NULL,
    western_houses JSONB NOT NULL,
    western_aspects JSONB NOT NULL,
    vedic_d1 JSONB NOT NULL,
    vedic_d9 JSONB NOT NULL,
    vedic_dashas JSONB NOT NULL DEFAULT '{}'::jsonb,
    firdaria_timeline JSONB NOT NULL,
    astrocartography JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS global_transit_cache (
    id SERIAL PRIMARY KEY,
    calculation_timestamp TIMESTAMP WITH TIME ZONE UNIQUE NOT NULL,
    planet_positions_json JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_global_transit_ts
    ON global_transit_cache (calculation_timestamp DESC);
