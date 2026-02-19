import os
import pandas as pd
from sqlalchemy import create_engine, text

def load(df: pd.DataFrame) -> int:
    db_url = os.getenv("NYC_DB_URL", "postgresql+psycopg2://postgres@localhost/nyc_accident_db")
    engine = create_engine(db_url, pool_pre_ping=True)

    insert_sql = text("""
        INSERT INTO crashes (
            crash_id, crash_datetime, borough,
            latitude, longitude, geom,
            persons_injured, persons_killed,
            vehicle_type, contributing_factor,
            source
        )
        VALUES (
            :crash_id, :crash_datetime, :borough,
            :latitude, :longitude,
            ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
            :persons_injured, :persons_killed,
            :vehicle_type, :contributing_factor,
            'open_data'
        )
        ON CONFLICT (crash_id) DO UPDATE SET
            crash_datetime = EXCLUDED.crash_datetime,
            borough = EXCLUDED.borough,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            geom = EXCLUDED.geom,
            persons_injured = EXCLUDED.persons_injured,
            persons_killed = EXCLUDED.persons_killed,
            vehicle_type = EXCLUDED.vehicle_type,
            contributing_factor = EXCLUDED.contributing_factor,
            source = 'open_data';
    """)

    rows = df.to_dict("records")
    with engine.begin() as conn:
        conn.execute(insert_sql, rows)

    return len(rows)
