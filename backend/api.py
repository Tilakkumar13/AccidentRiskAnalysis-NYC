# api.py - NYC Crash Risk Predictor 
# My GPSPA project backend. ETL is done, now serving predictions + stats

from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy import create_engine, text
import os
from datetime import datetime
import logging

# basic logging so I can see what's happening
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# postgres connection - had to change password 3 times to make this work lol
DB_URL = "postgresql+psycopg2://postgres:mypassword@localhost/nyc_accident_db"
engine = create_engine(DB_URL)

# try to load my random forest model
MODEL_PATH = "models/rf_model.pkl"
try:
    model = joblib.load(MODEL_PATH)
    print("✅ Model loaded ok")
except:
    print("❌ No model file, predictions will fail")
    model = None

def risk_category(prob):
    if prob > 0.7:
        return "HIGH RISK 🚨"
    elif prob > 0.4:
        return "MEDIUM ⚠️" 
    return "LOW 🟢"

@app.route('/')
def home():
    return jsonify({
        "NYC Crash Risk API": "Working!",
        "Try these": {
            "/predict?lat=40.7589&lon=-73.9851": "Times Square prediction", 
            "/hotspots": "Top crash clusters",
            "/stats": "Borough breakdown"
        }
    })

@app.route('/predict')
def predict():
    """Main prediction endpoint - click map → get instant risk score"""
    
    try:
        lat = float(request.args['lat'])
        lon = float(request.args['lon'])
        hour = int(request.args.get('hour', 17))  # evening rush hour default
        day = int(request.args.get('day_of_week', 4))  # Friday default
        
        if model is None:
            return jsonify({"error": "Need to train model first"}), 500
        
        # make feature vector exactly like training data
        features = pd.DataFrame([{
            'latitude': lat,
            'longitude': lon, 
            'hour': hour,
            'day_of_week': day
        }])
        
        prob = model.predict_proba(features)[0,1]  # accident probability
        risk = risk_category(prob)
        
        print(f"PREDICT: {lat},{lon} -> {risk} ({prob:.1%})")
        
        return jsonify({
            'lat': lat,
            'lon': lon,
            'crash_probability': round(prob, 3),
            'risk': risk,
            'safe_to_drive': prob < 0.3
        })
        
    except Exception as e:
        print(f"Predict error: {e}")
        return jsonify({"error": "Bad lat/lon or missing params"}), 400

@app.route('/hotspots')
def hotspots():
    """Get the worst crash clusters from PostGIS"""
    limit = int(request.args.get('limit', 20))
    
    sql = """
    SELECT 
        ST_X(ST_Centroid(geom)) as lon,
        ST_Y(ST_Centroid(geom)) as lat, 
        accident_count,
        ROUND(severity_avg::numeric, 1) as severity
    FROM accident_hotspots 
    ORDER BY accident_count DESC
    LIMIT %s
    """
    
    with engine.connect() as conn:
        result = conn.execute(sql, limit)
        data = []
        for row in result:
            data.append({
                'lat': row.lat,
                'lon': row.lon,
                'crashes': row.accident_count,
                'severity': float(row.severity)
            })
    return jsonify(data)

@app.route('/stats') 
def stats():
    """Borough crash density - good for charts"""
    
    sql = """
    SELECT 
        borough,
        accident_count,
        ROUND(avg_severity::numeric, 2) as avg_severity
    FROM borough_stats 
    ORDER BY accident_count DESC
    """
    
    with engine.connect() as conn:
        result = conn.execute(sql)
        data = []
        for row in result:
            data.append({
                'borough': row.borough,
                'total_crashes': row.accident_count,
                'avg_severity': float(row.avg_severity)
            })
    
    return jsonify(data)

@app.route('/health')
def health():
    return jsonify({
        "status": "API live ✅", 
        "model": model is not None,
        "database": "PostGIS connected",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

if __name__ == '__main__':
    print("🌃 NYC Crash Risk API")
    print("📊 PostGIS:", "Connected" if engine else "Failed") 
    print("🤖 ML Model:", "Ready" if model else "Missing - run training first")
    print("\n🔗 Test these URLs:")
    print("  curl 'http://localhost:5001/predict?lat=40.7589&lon=-73.9851'")
    print("  curl 'http://localhost:5001/hotspots'") 
    print("  curl 'http://localhost:5001/stats'")
    print("\n🚀 Starting on http://localhost:5001")
    print("-" * 50)
    
    app.run(debug=True, port=5001)
