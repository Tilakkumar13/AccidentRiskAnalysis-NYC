import geopandas as gpd
import folium
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://postgres@localhost/nyc_accident_db")

gdf = gpd.read_postgis(
    """
    SELECT geom
    FROM crashes
    WHERE geom IS NOT NULL
    LIMIT 5000
    """,
    engine,
    geom_col="geom",
    crs="EPSG:4326"
)

m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)

for row in gdf.itertuples():
    folium.CircleMarker(
        location=[row.geom.y, row.geom.x],
        radius=2,
        color="red",
        fill=True,
        fill_opacity=0.6
    ).add_to(m)

m.save("nyc_crashes_map.html")
print("✅ Map generated successfully")
