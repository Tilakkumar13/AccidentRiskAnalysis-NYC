import geopandas as gpd
import folium
from sqlalchemy import create_engine
from sklearn.cluster import DBSCAN

# 1. Connect to PostGIS
engine = create_engine("postgresql+psycopg2://postgres@localhost/nyc_accident_db")

# 2. Load data (geometry column = geom)
gdf = gpd.read_postgis(
    "SELECT geom FROM crashes WHERE geom IS NOT NULL LIMIT 50000",
    engine,
    geom_col="geom"
)

print("Total points:", len(gdf))

# 3. Reproject to meters (CRITICAL STEP)
gdf = gdf.set_crs(epsg=4326)
gdf = gdf.to_crs(epsg=3857)  # Web Mercator (meters)

# 4. Extract coordinates
coords = list(zip(gdf.geometry.x, gdf.geometry.y))

# 5. Run DBSCAN with STRICTER parameters
db = DBSCAN(
    eps=100,        # 100 meters radius (tighter)
    min_samples=20  # fewer points needed (more sensitive)
).fit(coords)

gdf["cluster"] = db.labels_

num_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
print(f"Found {num_clusters} hotspot clusters")
print(f"Noise points (not in any cluster): {sum(db.labels_ == -1)}")

# 6. Back to lat/lon for Folium
gdf = gdf.to_crs(epsg=4326)

# 7. Create map with HEATMAP for better visualization
from folium.plugins import HeatMap

m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)

# Add heatmap layer (shows density)
heat_data = [[row.geom.y, row.geom.x] for row in gdf.itertuples()]
HeatMap(heat_data, radius=10, blur=15, max_zoom=13).add_to(m)

# Add cluster centroids as markers
hotspots = gdf[gdf["cluster"] != -1]
cluster_centers = hotspots.groupby("cluster").apply(
    lambda x: (x.geometry.y.mean(), x.geometry.x.mean(), len(x))
)

for cluster_id, (lat, lon, count) in cluster_centers.items():
    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        color="red",
        fill=True,
        fillColor="red",
        fillOpacity=0.7,
        popup=f"Cluster {cluster_id}: {count} crashes"
    ).add_to(m)

# 8. Save map
m.save("nyc_accident_hotspots.html")
print(" Hotspot map with heatmap generated successfully")