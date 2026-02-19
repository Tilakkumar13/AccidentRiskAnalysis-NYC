DROP TABLE IF EXISTS accident_hotspots CASCADE;

-- Grid-based hotspots (fast + stable) using H3-like grid via snapping
-- We cluster points into ~150m cells using WebMercator then back to WGS84.

CREATE TABLE accident_hotspots AS
WITH pts AS (
  SELECT
    crash_id,
    persons_injured,
    persons_killed,
    geom
  FROM crashes
  WHERE geom IS NOT NULL
),
grid AS (
  SELECT
    ST_SnapToGrid(ST_Transform(geom, 3857), 150) AS cell_geom_3857,
    persons_injured,
    persons_killed
  FROM pts
),
agg AS (
  SELECT
    cell_geom_3857,
    COUNT(*) AS accident_count,
    AVG(persons_injured + persons_killed * 10.0) AS severity_avg
  FROM grid
  GROUP BY cell_geom_3857
)
SELECT
  row_number() OVER () AS hotspot_id,
  ST_Transform(cell_geom_3857, 4326) AS geom,
  accident_count,
  severity_avg
FROM agg;

CREATE INDEX idx_accident_hotspots_geom ON accident_hotspots USING GIST (geom);
