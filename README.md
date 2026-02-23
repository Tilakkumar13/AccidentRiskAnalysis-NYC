# NYC Accident Risk Intelligence (GPSPA Project)

A full-stack geospatial system that analyzes NYC crash data with **PostGIS spatial queries**, **hotspot detection**, and an **ML severity-risk predictor**, exposed through a **Flask API** and an interactive **Mapbox web UI**.

---

## Project Overview

This project helps users explore accident patterns in New York City by:

- Visualizing **accident hotspots** (cluster-based points ranked by crash counts)
- Predicting **severity risk level** (LOW / MEDIUM / HIGH) for a location + time
- Showing nearby crash density (e.g., number of crashes within **300m**)
- Allowing users to **submit accident reports** (stored in DB + shown on map)
- Providing a responsive UI with search, layers, and time controls

> Important note (honest definition):  
> The ML model in this project predicts **severity level** (based on injuries/fatalities), not the probability that an accident will occur.

---

## Technical Stack

- **Language:** Python 3.10+
- **Database:** PostgreSQL + PostGIS
- **Backend/API:** Flask + SQLAlchemy
- **Data/ML:** Pandas, Scikit-learn, Joblib
- **Frontend:** HTML/CSS/JS + Mapbox GL JS

---

## Repository Structure (Typical)
accident-risk-nyc/
etl/                 # ETL scripts (extract/transform/load)
database/            # schema SQL, helpers
ml/                  # training scripts + saved model.pkl
api/                 # Flask API (app.py)
frontend/            # Mapbox UI (index.html)
requirements.txt

---

## Data Extraction / ETL

Crash data is loaded into PostGIS and cleaned to ensure usable spatial records.

### ETL tasks include:
- Removing rows with invalid coordinates (NULL or 0,0)
- Creating a geometry column:
  - `geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)`
- Creating/refreshing spatial indexes for fast queries
- Preparing data for:
  - Hotspot detection
  - Severity scoring
  - ML training

---

## Spatial Analysis: Hotspots

Hotspots represent areas with high crash density and are returned via the API from a dedicated table:

- **Table:** `accident_hotspots`
- **Fields used in UI:** `geom`, `accident_count`, `severity_avg`
- The frontend displays hotspots as circles sized by `accident_count`.

Endpoint:
- `GET /hotspots?limit=60`

---

## Machine Learning (Severity Risk Model)

The ML component predicts **severity risk level** for a location and time.

### Label definition (severity-based)
A severity score is computed from crash outcomes:

- `severity_score = persons_injured + (persons_killed * 10)`

Risk levels are derived from severity thresholds into:
- LOW
- MEDIUM
- HIGH

### Features (current model)
- latitude, longitude
- hour, day_of_week
- is_night, is_weekend
- borough_code (set to 0 for arbitrary map points unless borough is known)

Endpoint:
- `GET /predict?lat=..&lon=..&hour=..&day_of_week=..`

The API returns:
- predicted label
- class probabilities
- count of nearby crashes within 300m (PostGIS `ST_DWithin`)

---

## Database

### Main Tables

#### 1) `crashes`
Stores crash records (open data + user reports)

Key columns:
- crash_id (BIGINT, PK)
- crash_datetime
- borough
- latitude, longitude
- geom (Point, 4326)
- persons_injured, persons_killed
- source (`open_data` or `user_report`)

#### 2) `user_reports`
User-submitted incidents.

**Requirement implemented:** the report uses the **same crash_id** in both `crashes` and `user_reports`.

#### 3) `accident_hotspots`
Stores hotspot point geometry + stats.

#### 4) `predictions`
Optional logging table for saved predictions.

---

## API

The Flask API connects the PostGIS database and the frontend UI.

### Core endpoints

| Method | Endpoint | Description |
|-------:|----------|-------------|
| GET | `/health` | Check DB + model status |
| GET | `/stats` | Crash stats by borough |
| GET | `/hotspots?limit=60` | Hotspot points |
| GET | `/accidents?limit=200` | Recent crashes |
| GET | `/accident/<crash_id>` | Crash details |
| GET | `/predict?lat=&lon=&hour=&day_of_week=` | ML severity risk prediction + 300m count |
| POST | `/report` | Create user report (inserts into crashes + user_reports) |
| PUT | `/report/<crash_id>` | Update user report |
| DELETE | `/report/<crash_id>` | Delete user report |
| GET | `/reports?limit=50` | List reports |

---

## Frontend (Mapbox UI)

Main UI features:
- Search place/address (Mapbox Geocoding)
- Click map to set inspector + predict risk
- Toggle layers:
  - hotspots
  - risk shading grid
  - user reports
- 24-hour animation (changes hour and updates prediction)
- Submit accident report

> “Risk shading (grid)” is a sampled overlay created by calling `/predict` on a grid of points in the viewport.

---

## How to Run

### 1) Install dependencies
```bash
pip install -r requirements.txt

2) Create DB + enable PostGIS
createdb nyc_accident_db
psql -d nyc_accident_db -c "CREATE EXTENSION postgis;"

3) Run database schema
psql -U postgres -d nyc_accident_db -f database/schema.sql

4) Run ETL
python etl/pipeline.py

5) Train ML model (optional)
python ml/train.py

6) Start API
python api/app.py

7) Open Frontend

Open:
	•	frontend/index.html

⸻

Example Use Case
	1.	User opens the app and searches “Times Square”
	2.	Map flies to location and auto-predicts severity risk
	3.	User toggles hotspots and sees crash cluster points
	4.	User turns on risk shading to see how risk varies in the visible area
	5.	User submits a report (stored and immediately visible on map)

Future Improvements
	•	Predict accident probability (not only severity) using exposure factors (traffic volume, road class, intersections)
	•	Add borough inference using polygon lookup (point-in-polygon)
	•	Improve risk grid rendering (server-side tiles or vector grid)
	•	Deploy with Docker + production WSGI (gunicorn)
	•	Add authentication for user reports
Author(s)

Tilak Kumar 
vijay
