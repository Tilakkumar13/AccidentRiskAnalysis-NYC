import pandas as pd
import psycopg2

# Load CSV safely
df = pd.read_csv("data/nyc_crashes.csv", low_memory=False)

# Keep only relevant columns
df = df[['CRASH DATE','CRASH TIME','BOROUGH','LATITUDE','LONGITUDE','NUMBER OF PERSONS INJURED','NUMBER OF PERSONS KILLED']]

# Convert numeric columns safely
df['LATITUDE'] = pd.to_numeric(df['LATITUDE'], errors='coerce')
df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')

# Replace invalid numbers with 0 and ensure they are integers
df['NUMBER OF PERSONS INJURED'] = pd.to_numeric(df['NUMBER OF PERSONS INJURED'], errors='coerce').fillna(0).astype(int)
df['NUMBER OF PERSONS KILLED'] = pd.to_numeric(df['NUMBER OF PERSONS KILLED'], errors='coerce').fillna(0).astype(int)

# Drop rows without valid coordinates
df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])

# Connect to PostgreSQL
conn = psycopg2.connect(dbname="nyc_accident_db", user="postgres")
cur = conn.cursor()

# Insert data
for _, row in df.iterrows():
    try:
        cur.execute("""
            INSERT INTO crashes (
                crash_date,
                crash_time,
                borough,
                latitude,
                longitude,
                persons_injured,
                persons_killed,
                geom
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            );
        """, (
            row['CRASH DATE'],
            row['CRASH TIME'],
            row['BOROUGH'],
            row['LATITUDE'],
            row['LONGITUDE'],
            min(row['NUMBER OF PERSONS INJURED'], 999),  # cap at 999
            min(row['NUMBER OF PERSONS KILLED'], 999),   # cap at 999
            row['LONGITUDE'],
            row['LATITUDE']
        ))
    except Exception as e:
        print(f"Skipping row due to error: {e}")

conn.commit()
cur.close()
conn.close()

print("✅ Data loaded safely into PostGIS")
