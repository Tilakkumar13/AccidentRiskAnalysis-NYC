import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import numpy as np

print("🧠 Training ML Risk Prediction Model...")

# 1. Connect to PostGIS
engine = create_engine("postgresql+psycopg2://postgres@localhost/nyc_accident_db")

# 2. Load crash data with additional features
query = """
    SELECT 
        latitude,
        longitude,
        persons_injured,
        persons_killed,
        borough,
        EXTRACT(HOUR FROM crash_time) as hour,
        EXTRACT(DOW FROM crash_date) as day_of_week
    FROM crashes
    WHERE latitude IS NOT NULL 
    AND longitude IS NOT NULL
    AND crash_time IS NOT NULL
    LIMIT 100000
"""

df = pd.read_sql(query, engine)

print(f"Loaded {len(df)} crash records")

# 3. Feature Engineering

# Calculate severity score
df['severity_score'] = df['persons_injured'] + (df['persons_killed'] * 10)

# Time-based features
df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
df['is_weekend'] = (df['day_of_week'].isin([0, 6])).astype(int)

# Borough encoding
borough_map = {
    'MANHATTAN': 4,
    'BROOKLYN': 3,
    'QUEENS': 2,
    'BRONX': 1,
    'STATEN ISLAND': 0
}
df['borough_code'] = df['borough'].map(borough_map).fillna(0)

# 4. Create risk labels (target variable)
# Define risk based on severity percentiles
df['risk_level'] = pd.cut(
    df['severity_score'],
    bins=[-1, 0, 2, 100],
    labels=['LOW', 'MEDIUM', 'HIGH']
)

print("\nRisk distribution:")
print(df['risk_level'].value_counts())

# 5. Prepare features and target
feature_cols = [
    'latitude', 'longitude', 'hour', 'day_of_week',
    'is_night', 'is_weekend', 'borough_code'
]

X = df[feature_cols]
y = df['risk_level']

# Remove any NaN
mask = ~(X.isna().any(axis=1) | y.isna())
X = X[mask]
y = y[mask]

# 6. Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTraining set size: {len(X_train)}")
print(f"Test set size: {len(X_test)}")

# 7. Train Random Forest model
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    class_weight='balanced'
)

model.fit(X_train, y_train)

# 8. Evaluate
y_pred = model.predict(X_test)

print("\n📊 Model Performance:")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# 9. Feature importance
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n🔍 Feature Importance:")
print(feature_importance)

# 10. Save model
joblib.dump(model, 'models/risk_model.pkl')
print("\n✅ Model saved to models/risk_model.pkl")

# 11. Example prediction
sample = pd.DataFrame({
    'latitude': [40.7589],
    'longitude': [-73.9851],  # Times Square
    'hour': [18],
    'day_of_week': [4],
    'is_night': [0],
    'is_weekend': [0],
    'borough_code': [4]
})

prediction = model.predict(sample)
proba = model.predict_proba(sample)

print("\n🧪 Example Prediction (Times Square, 6 PM, Friday):")
print(f"Predicted Risk: {prediction[0]}")
print(f"Probabilities: LOW={proba[0][0]:.2f}, MEDIUM={proba[0][1]:.2f}, HIGH={proba[0][2]:.2f}")