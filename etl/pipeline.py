from etl.extract.extract import extract
from etl.transform.transform import transform
from etl.load.load import load

def run(limit: int = 50000):
    print("🔄 ETL started...")
    raw = extract(limit=limit)
    print(f"✅ Extracted: {len(raw)} rows")

    clean = transform(raw)
    print(f"✅ Transformed: {len(clean)} rows")

    n = load(clean)
    print(f"✅ Loaded/Upserted: {n} rows into PostGIS")

if __name__ == "__main__":
    run(limit=50000)
