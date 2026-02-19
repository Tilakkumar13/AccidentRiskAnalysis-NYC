from flask import Flask, jsonify, request
import joblib
import pandas as pd
import os
import random
import datetime
import uuid
from sqlalchemy import create_engine, text

app = Flask(__name__)

# -----------------------------
# CORS
# -----------------------------
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


# -----------------------------
# Database
# -----------------------------
DB_URL = os.getenv("NYC_DB_URL", "postgresql+psycopg2://postgres@localhost/nyc_accident_db")
engine = create_engine(DB_URL, pool_pre_ping=True)


# -----------------------------
# Model
# -----------------------------
MODEL_PATH = os.getenv("NYC_MODEL_PATH", "/Users/tilakkumarsh/accident-risk-nyc/ml/model.pkl")
try:
    model = joblib.load(MODEL_PATH)
    MODEL_LOADED = True
except Exception as e:
    model = None
    MODEL_LOADED = False
    print(f"⚠️ Model not loaded: {e}")


def generate_bigint_id() -> int:
    """
    Safe BIGINT id:
    yymmddHHMMSSmmm * 1000 + rand(0..999)
    Always < BIGINT max.
    """
    base = int(datetime.datetime.utcnow().strftime("%y%m%d%H%M%S%f")[:-3])  # milliseconds
    return base * 1000 + random.randint(0, 999)


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return jsonify({
        "status": "NYC Risk API LIVE",
        "endpoints": [
            "/health",
            "/stats",
            "/hotspots?limit=20",
            "/accidents?limit=200",
            "/accident/<crash_id>",
            "/predict?lat=..&lon=..&hour=..&day_of_week=..",
            "/report (POST)",
            "/reports?limit=200"
        ]
    })


# -----------------------------
# HEALTH
# -----------------------------
@app.route("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "model_loaded": MODEL_LOADED
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


# -----------------------------
# STATS
# -----------------------------
@app.route("/stats")
def stats():
    try:
        q = """
        SELECT borough,
               COUNT(*) AS total_accidents,
               COALESCE(SUM(persons_injured), 0) AS total_injured,
               COALESCE(SUM(persons_killed), 0) AS total_killed
        FROM crashes
        WHERE borough IS NOT NULL
        GROUP BY borough
        ORDER BY total_accidents DESC;
        """
        df = pd.read_sql(q, engine)
        return jsonify({"success": True, "data": df.to_dict("records")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------
# HOTSPOTS
# -----------------------------
@app.route("/hotspots")
def hotspots():
    limit = int(request.args.get("limit", 20))

    # Filter out (0,0) junk + null geom
    sql = text("""
        SELECT
            ST_Y(geom) AS lat,
            ST_X(geom) AS lon,
            accident_count,
            ROUND(severity_avg::numeric, 1) AS severity
        FROM accident_hotspots
        WHERE geom IS NOT NULL
          AND NOT (ST_X(geom) = 0 AND ST_Y(geom) = 0)
        ORDER BY accident_count DESC
        LIMIT :limit
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, {"limit": limit}).fetchall()

    data = [{
        "lat": float(r.lat),
        "lon": float(r.lon),
        "crashes": int(r.accident_count),
        "severity": float(r.severity)
    } for r in rows]

    return jsonify({"success": True, "count": len(data), "hotspots": data})


# -----------------------------
# ACCIDENT LIST
# -----------------------------
@app.route("/accidents")
def accidents():
    try:
        limit = int(request.args.get("limit", 200))

        q = text("""
            SELECT crash_id, crash_datetime, borough, latitude, longitude,
                   persons_injured, persons_killed, source
            FROM crashes
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
              AND NOT (latitude = 0 AND longitude = 0)
            ORDER BY crash_datetime DESC NULLS LAST
            LIMIT :limit
        """)

        df = pd.read_sql(q, engine, params={"limit": limit})
        df["crash_datetime"] = df["crash_datetime"].astype(str)

        return jsonify({"success": True, "count": len(df), "accidents": df.to_dict("records")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------
# ACCIDENT DETAILS (click marker)
# -----------------------------
@app.route("/accident/<int:crash_id>")
def accident_detail(crash_id: int):
    try:
        q = text("""
            SELECT crash_id, crash_datetime, borough, latitude, longitude,
                   persons_injured, persons_killed,
                   vehicle_type, contributing_factor, source, created_at
            FROM crashes
            WHERE crash_id = :crash_id
        """)
        df = pd.read_sql(q, engine, params={"crash_id": crash_id})

        if df.empty:
            return jsonify({"success": False, "error": "Accident not found"}), 404

        row = df.iloc[0].to_dict()
        row["crash_datetime"] = str(row["crash_datetime"])
        row["created_at"] = str(row["created_at"])

        return jsonify({"success": True, "accident": row})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------
# PREDICT + 300m neighbor alert
# -----------------------------
@app.route("/predict")
def predict_risk():
    lat = float(request.args.get("lat", 40.7128))
    lon = float(request.args.get("lon", -74.0060))
    hour = int(request.args.get("hour", 18))
    day_of_week = int(request.args.get("day_of_week", 4))

    is_night = 1 if (hour >= 22 or hour <= 6) else 0
    is_weekend = 1 if day_of_week in [0, 6] else 0

    borough_code = 0  # keep stable for your model

    features = pd.DataFrame({
        "latitude": [lat],
        "longitude": [lon],
        "hour": [hour],
        "day_of_week": [day_of_week],
        "is_night": [is_night],
        "is_weekend": [is_weekend],
        "borough_code": [borough_code],
    })

    if MODEL_LOADED:
        pred = model.predict(features)[0]
        proba = model.predict_proba(features)[0]
        probs = {"LOW": float(proba[0]), "MEDIUM": float(proba[1]), "HIGH": float(proba[2])}
        mode = "model"
    else:
        pred = "MEDIUM"
        probs = {"LOW": 0.3, "MEDIUM": 0.4, "HIGH": 0.3}
        mode = "fallback"

    spatial_sql = text("""
        SELECT COUNT(*)
        FROM crashes
        WHERE geom IS NOT NULL
          AND ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
            300
          )
    """)

    with engine.connect() as conn:
        nearby_count = conn.execute(spatial_sql, {"lat": lat, "lon": lon}).scalar()

    return jsonify({
        "success": True,
        "mode": mode,
        "location": {"lat": lat, "lon": lon},
        "risk_level": str(pred),
        "probabilities": probs,
        "nearby_accidents_300m": int(nearby_count)
    })


# -----------------------------
# USER REPORT (POST)
# prof requirement: SAME crash_id in crashes + user_reports
# -----------------------------
@app.route("/report", methods=["POST"])
def report_accident():
    try:
        data = request.json or {}

        lat = float(data["latitude"])
        lon = float(data["longitude"])
        description = data.get("description", "")
        severity = data.get("severity", "MEDIUM")
        borough = data.get("borough", "UNKNOWN")

        # ✅ FIXED BIGINT-safe crash_id
        crash_id = uuid.uuid4().int % (2**63 - 1)

        insert_crash = text("""
            INSERT INTO crashes (
                crash_id, crash_datetime, borough,
                latitude, longitude, geom,
                persons_injured, persons_killed,
                vehicle_type, contributing_factor,
                source
            )
            VALUES (
                :crash_id, NOW(), :borough,
                :lat, :lon,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                0, 0,
                NULL, NULL,
                'user_report'
            )
        """)

        insert_report = text("""
            INSERT INTO user_reports (
                crash_id, report_time, description, severity,
                latitude, longitude, geom
            )
            VALUES (
                :crash_id, NOW(), :description, :severity,
                :lat, :lon,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
            )
        """)

        with engine.begin() as conn:
            conn.execute(insert_crash, {
                "crash_id": crash_id,
                "borough": borough,
                "lat": lat,
                "lon": lon
            })

            conn.execute(insert_report, {
                "crash_id": crash_id,
                "description": description,
                "severity": severity,
                "lat": lat,
                "lon": lon
            })

        return jsonify({
            "success": True,
            "message": "Accident reported successfully",
            "crash_id": crash_id
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------
# LIST REPORTS
# -----------------------------
@app.route("/reports")
def reports():
    limit = int(request.args.get("limit", 50))
    q = text("""
        SELECT crash_id, report_time, description, severity,
               latitude, longitude
        FROM user_reports
        ORDER BY report_time DESC
        LIMIT :limit
    """)
    df = pd.read_sql(q, engine, params={"limit": limit})
    df["report_time"] = df["report_time"].astype(str)
    return jsonify({"success": True, "count": len(df), "reports": df.to_dict("records")})


if __name__ == "__main__":
    print("🚀 NYC Accident Risk API Starting...")
    app.run(debug=True, port=5001, host="0.0.0.0")