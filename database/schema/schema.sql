CREATE EXTENSION IF NOT EXISTS postgis;

-- Drop (only the ones we use)
DROP TABLE IF EXISTS user_reports CASCADE;
DROP TABLE IF EXISTS crashes CASCADE;

-- MAIN TABLE (merged: crash + location + casualties + basic vehicle/factor)
CREATE TABLE crashes (
    crash_id BIGINT PRIMARY KEY,
    crash_datetime TIMESTAMP,
    borough VARCHAR(50),

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326),

    persons_injured INT DEFAULT 0,
    persons_killed INT DEFAULT 0,

    vehicle_type VARCHAR(100),
    contributing_factor VARCHAR(200),

    source VARCHAR(20) NOT NULL DEFAULT 'open_data',  -- open_data | user
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_crashes_geom ON crashes USING GIST (geom);
CREATE INDEX idx_crashes_datetime ON crashes (crash_datetime);
CREATE INDEX idx_crashes_borough ON crashes (borough);

-- USER REPORTS (linked via crash_id as prof requested)
CREATE TABLE user_reports (
    crash_id BIGINT PRIMARY KEY REFERENCES crashes(crash_id) ON DELETE CASCADE,
    report_time TIMESTAMP NOT NULL DEFAULT NOW(),
    description TEXT,
    severity VARCHAR(10) DEFAULT 'MEDIUM'
);
