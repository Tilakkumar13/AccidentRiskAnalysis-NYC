# NYC Accident Risk Analysis

## 🚀 Project Overview
This project predicts high-risk accident zones in New York City using historical crash data and spatial analysis. By combining data engineering, machine learning, and geospatial visualization, it helps identify accident hotspots to improve urban safety and inform city planning.

---

## 🛠️ Tech Stack
- **Python** – Data processing, ML modeling, API backend  
- **PostgreSQL + PostGIS** – Database & spatial queries  
- **FastAPI** – RESTful API endpoints  
- **Pandas & Scikit-learn** – Data manipulation and modeling  
- **HTML / JavaScript / Leaflet** – Frontend map visualization  

---

## 🏗️ Architecture & Folder Structure

accident-risk-nyc/
├── etl/ → Data extraction, transformation, and loading
├── database/ → PostgreSQL schema & SQL scripts
│ └── schema/ → DB table definitions
├── api/ → FastAPI backend endpoints
├── ml/ → Machine learning models and training scripts
├── frontend/ → HTML/JS visualization interface
├── analysis/ → Exploratory Data Analysis (EDA)
├── data/ → Sample datasets (for demo purposes)
└── README.md → Project documentation


---

## ⚡ How to Run Locally

1. **Clone the repo**
```bash
git clone https://github.com/Tilakkumar13/AccidentRiskAnalysis-NYC.git
cd AccidentRiskAnalysis-NYC

Install dependencies

pip install -r requirements.txt


Setup database

psql -U <username> -d nyc_accident_db -f database/schema/schema.sql


Run ETL pipeline

python etl/pipeline.py


Start API

uvicorn api.app:app --reload


Open frontend

Navigate to frontend/index.html in your browser
