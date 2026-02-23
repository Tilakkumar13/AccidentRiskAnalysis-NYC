🗽 NYC Accident Risk Analysis & Prediction System

🚀 Project Overview

The Accident Risk Analysis System is a data-driven geospatial intelligence platform designed to analyze, detect, and predict accident risk across New York City.
• This system uses historical NYC crash data, spatial clustering techniques, and machine learning models to:
• Identify accident hotspots
• Predict accident risk at specific locations and times
• Provide a risk score (Low / Medium / High)
• Allow users to report new accidents
• Continuously improve predictions using new data
The goal of this project is to support smarter urban planning, safer route analysis, and real-time accident risk awareness.

⸻

🧠 System Architecture

It combines:
	•	Live ETL data ingestion
	•	PostGIS spatial database
	•	Machine Learning risk prediction
	•	DBSCAN hotspot clustering
	•	Real-time user-reported accident integration
	•	Spatial proximity risk propagation

The system predicts accident risk levels (LOW / MEDIUM / HIGH) for any location in NYC and identifies nearby hotspots using spatial clustering.

⸻
🔄 Workflow

• Crash data is fetched from NYC Open Data.
• Data is cleaned and transformed.
• Data is stored in PostgreSQL with spatial indexing.
• Hotspots are detected using DBSCAN clustering.
• ML model is trained on historical crash patterns.
• User queries API → system returns risk score + probability.

⸻

🎯 Key Features

🔍 1. Risk Prediction
	•	Predicts accident probability using a trained ML model.
	•	Inputs: latitude, longitude, hour, day of week.
	•	Returns:
	•	Risk level
	•	Probability distribution
	•	Nearby accidents within 300m
	•	Nearby hotspots within 400m

⸻

🗺 2. Spatial Hotspot Detection
	•	DBSCAN clustering on crash coordinates.
	•	Automatically generates accident_hotspots table.
	•	Heatmap + centroid visualization.
	•	Spatial index using GiST for performance.

⸻

🚨 3. Live User Accident Reporting

Users can report new accidents via API:
	•	Automatically generates a valid BIGINT crash_id
	•	Inserts into:
	•	crashes
	•	user_reports
	•	Linked by foreign key
	•	Instantly affects spatial predictions

⸻

🔄 4. Automated ETL Pipeline
	•	Extracts live NYC crash data
	•	Cleans & transforms
	•	Upserts into PostGIS
	•	Designed for cron automation

⸻

🧠 5. Neighbor Risk Propagation

When predicting risk:
	•	Counts crashes within 300 meters
	•	Detects hotspot clusters within 400 meters
	•	Adds temporal crash density (same hour)

This creates spatial + temporal intelligence.

⸻

🛠️ Tech Stack

Backend
	•	Python
	•	Flask
	•	SQLAlchemy
	•	Joblib (ML model loading)

Database
	•	PostgreSQL
	•	PostGIS
	•	GiST spatial indexes

Machine Learning
	•	Scikit-learn
	•	Random Forest classifier

Geospatial
	•	GeoPandas
	•	DBSCAN clustering
	•	Folium heatmaps

🗄️ Database Design

crashes (Merged Design)

Column
Type
crash_id
BIGINT (PK)
crash_datetime
TIMESTAMP
borough
VARCHAR
latitude
DOUBLE
longitude
DOUBLE
geom
GEOMETRY(Point, 4326)
persons_injured
INT
persons_killed
INT
vehicle_type
VARCHAR
contributing_factor
VARCHAR
source
VARCHAR (open_data / user_report)
created_at
TIMESTAMP

user_reports

Column
Type
crash_id
BIGINT (FK → crashes)
report_time
TIMESTAMP
description
TEXT
severity
VARCHAR
latitude
DOUBLE
longitude
DOUBLE

accident_hotspots
Column
Type
cluster_id
INT
accident_count
INT
severity_avg
FLOAT
geom
GEOMETRY(Point, 4326)

🏗️ Project Structure

accident-risk-nyc/
├── etl/                 # Extract, transform, load pipeline
│   ├── extract/
│   ├── transform/
│   ├── load/
│   └── pipeline.py
│
├── database/
│   └── schema/
│       └── schema.sql
│
├── api/
│   ├── app.py           # Main Flask API
│   └── hotspots.py      # DBSCAN clustering script
│
├── ml/
│   ├── train.py
│   └── model.pkl
│
├── frontend/
│   ├── index.html
│   └── map visualizations
│
├── analysis/
│   └── eda.py
│
└── README.md

⚡ How To Run Locally

Endpoint
Description
/health
API + DB status
/stats
Borough statistics
/accidents
Recent crash list
/hotspots
Cluster summary
/predict
Risk prediction
/report (POST)
Submit new accident
/reports
View user reports


👨‍💻 Author

Tilak Kumar
MSc Geospatial Technologies

