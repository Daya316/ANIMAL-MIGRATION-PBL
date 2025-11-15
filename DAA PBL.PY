
import pandas as pd
import folium
from shapely.geometry import MultiPoint, Polygon
import matplotlib.pyplot as plt
from datetime import datetime

# Step 1: Load dataset
# Add on_bad_lines='skip' to handle potential parsing errors
df = pd.read_csv("/content/migration_original.csv", on_bad_lines='skip', engine='python')

# Rename columns for simplicity
df = df.rename(columns={"location-long": "longitude", "location-lat": "latitude",
                        "individual-local-identifier": "animal_id",
                        "individual-taxon-canonical-name": "species"})
df.head()
# Convert timestamp to datetime
df["timestamp"] = pd.to_datetime(df["timestamp"])
# Step 2: Derive Season from Month
def get_season(month):
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Autumn"

df["season"] = df["timestamp"].dt.month.apply(get_season)

# Step 3: Create migration zones (Convex Hulls)

zones = {}

for season, group in df.groupby("season"):
    points = MultiPoint([(lon, lat) for lon, lat in zip(group["longitude"], group["latitude"])])

    if len(points.geoms) >= 3:
        hull = points.convex_hull
    else:
        hull = points.envelope  # fallback

    zones[season] = hull


# Step 4: Area measurement

for season, hull in zones.items():
    area = hull.area  # in degrees² (approx)
    print(f"Season: {season}, Zone Area (deg² approx): {area:.4f}")


# Step 5: Folium visualization

center_lat = df["latitude"].mean()
center_lon = df["longitude"].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
colors = {"Winter": "blue", "Spring": "green", "Summer": "red", "Autumn": "orange"}

for season, hull in zones.items():
    if isinstance(hull, Polygon):
        coords = [(lat, lon) for lon, lat in hull.exterior.coords]
        folium.Polygon(coords, color=colors.get(season, "black"),
                       fill=True, fill_opacity=0.3,
                       tooltip=f"{season} Migration Zone").add_to(m)

    # Add GPS points
    season_data = df[df["season"] == season]
    for _, row in season_data.iterrows():
        folium.CircleMarker(location=[row["latitude"], row["longitude"]],
                            radius=2, color=colors.get(season, "black"),
                            fill=True).add_to(m)

m.save("migration_zones_map.html")
print("✅ Map saved as migration_zones_map.html")


# Step 6: Matplotlib comparison

plt.figure(figsize=(8,6))

for season, hull in zones.items():
    if isinstance(hull, Polygon):
        x, y = hull.exterior.xy
        plt.plot(x, y, color=colors.get(season, "black"), label=f"{season} Zone")
        plt.fill(x, y, alpha=0.2, color=colors.get(season, "black"))

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Seasonal Migration Zones")
plt.legend()
plt.show()
