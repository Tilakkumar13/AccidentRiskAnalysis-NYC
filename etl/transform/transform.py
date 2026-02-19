import pandas as pd

def transform(df: pd.DataFrame) -> pd.DataFrame:
    # keep only what we need + make consistent types
    df = df.copy()

    # crash_date from Socrata is timestamp string
    df["crash_datetime"] = pd.to_datetime(df["crash_date"], errors="coerce")

    # numeric clean
    for col in ["latitude", "longitude"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["number_of_persons_injured", "number_of_persons_killed"]:
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0).astype(int)

    # use collision_id as crash_id
    df["crash_id"] = pd.to_numeric(df["collision_id"], errors="coerce").astype("Int64")

    # first vehicle type + first contributing factor (merged columns)
    df["vehicle_type"] = df.get("vehicle_type_code1", None)
    df["contributing_factor"] = df.get("contributing_factor_vehicle_1", None)

    df["borough"] = df.get("borough", None)

    df = df.dropna(subset=["crash_id", "crash_datetime", "latitude", "longitude"])

    out = df[[
        "crash_id",
        "crash_datetime",
        "borough",
        "latitude",
        "longitude",
        "number_of_persons_injured",
        "number_of_persons_killed",
        "vehicle_type",
        "contributing_factor",
    ]].rename(columns={
        "number_of_persons_injured": "persons_injured",
        "number_of_persons_killed": "persons_killed",
    })

    return out
