from flask import Flask, jsonify, request
import joblib
import pandas as pd
import os
from sqlalchemy import create_engine, text

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response

DB_URL = os.getenv("NYC_DB_URL", "postgresql+psycopg2://postgres@localhost/nyc_accident_db")
engine = create_engine(DB_URL, pool_pre_ping=True)

MODEL_PATH = os.getenv("NYC_MODEL_PATH", "/Users/tilakkumarsh/accident-risk-nyc/ml/model.pkl")
try:
    model = joblib.load(MODEL_PATH)
    MODEL_LOADED = True
except Exception as e:
    model = None
    MODEL_LOADED = False
    print(f"⚠️ Model not loaded from {MODEL_PATH}: {e}")

@app.route("/")
def home():
    return jsonify({
        "status": "NYC Risk API  LIVE",
        "port": 5001,
        "model_loaded": MODEL_LOADED,
        "endpoints": ["/health", "/stats", "/hotspots", "/accidents", "/predict"]
    })

@app.route("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

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

@app.route('/hotspots')
def hotspots():
    """Get the worst crash clusters from PostGIS"""
    limit = int(request.args.get('limit', 20))
    
    sql = text("""
    SELECT 
        ST_X(ST_Centroid(geom)) as lon,
        ST_Y(ST_Centroid(geom)) as lat, 
        accident_count,
        ROUND(severity_avg::numeric, 1) as severity
    FROM accident_hotspots 
    ORDER BY accident_count DESC
    LIMIT :limit
    """)
    
    with engine.connect() as conn:
        result = conn.execute(sql, {"limit": limit})
        data = []
        for row in result:
            data.append({
                'lat': float(row.lat),
                'lon': float(row.lon),
                'crashes': int(row.accident_count),
                'severity': float(row.severity)
            })
    return jsonify(data)


@app.route("/accidents")
def accidents():
    try:
        limit = int(request.args.get("limit", 200))
        borough = request.args.get("borough")
        min_injuries = int(request.args.get("min_injuries", 0))

        q = """
        SELECT crash_date, crash_time, borough, latitude, longitude, persons_injured, persons_killed
        FROM crashes
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
          AND COALESCE(persons_injured, 0) >= :min_injuries
        """
        params = {"min_injuries": min_injuries, "limit": limit}

        if borough:
            q += " AND UPPER(borough) = UPPER(:borough)"
            params["borough"] = borough

        q += " ORDER BY crash_date DESC NULLS LAST LIMIT :limit"

        df = pd.read_sql(text(q), engine, params=params)
        df["crash_date"] = df["crash_date"].astype(str)
        df["crash_time"] = df["crash_time"].astype(str)

        return jsonify({"success": True, "count": len(df), "accidents": df.to_dict("records")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/predict")
def predict_risk():
    lat = float(request.args.get("lat", 40.7128))
    lon = float(request.args.get("lon", -74.0060))
    hour = int(request.args.get("hour", 18))
    day_of_week = int(request.args.get("day_of_week", 4))

    is_night = 1 if (hour >= 22 or hour <= 6) else 0
    is_weekend = 1 if day_of_week in [0, 6] else 0

    if lat > 40.8:
        borough_code = 1  # Bronx
    elif lon > -73.9 and lat > 40.7:
        borough_code = 4  # Manhattan
    elif lon < -73.95 and lat < 40.7:
        borough_code = 3  # Brooklyn
    elif lon > -73.85:
        borough_code = 2  # Queens
    else:
        borough_code = 0  # Staten Island

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
        # Demo fallback
        pred = "HIGH" if lon > -73.95 else "MEDIUM"
        probs = {"LOW": 0.10, "MEDIUM": 0.30, "HIGH": 0.60} if pred == "HIGH" else {"LOW": 0.40, "MEDIUM": 0.40, "HIGH": 0.20}
        mode = "fallback"

    return jsonify({
        "mode": mode,
        "location": {"lat": lat, "lon": lon},
        "risk_level": str(pred),
        "probabilities": probs
    })

if __name__ == "__main__":
    print("🚀 NYC Accident Risk API Starting...")
    app.run(debug=True, port=5001, host="0.0.0.0")




