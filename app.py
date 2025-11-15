import streamlit as st
import pandas as pd
import folium
from shapely.geometry import MultiPoint, Polygon
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(page_title="Animal Migration Zones", layout="wide")

st.title("🐾 Animal Migration Zone Mapping")
st.write("Upload a migration dataset to visualize seasonal migration zones.")

# --------------------------- File Upload ---------------------------
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, on_bad_lines='skip', engine='python')

    # Rename required columns
    df = df.rename(columns={
        "location-long": "longitude",
        "location-lat": "latitude",
        "individual-local-identifier": "animal_id",
        "individual-taxon-canonical-name": "species"
    })

    st.subheader("📌 Preview of Data")
    st.dataframe(df.head())

    # --------------------------- Timestamp ---------------------------
    st.success("⏳ Detecting timestamp column...")

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # --------------------------- Season Column ---------------------------
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

    # --------------------------- User Filters ---------------------------
    st.subheader("🔍 Apply Filters")

    species_list = df["species"].unique()
    selected_species = st.selectbox("Select Species", species_list)

    filtered_df = df[df["species"] == selected_species]

    st.write("Filtered Rows:", len(filtered_df))

    # --------------------------- Convex Hull Zones ---------------------------
    st.subheader("📍 Generating Migration Zones...")
    zones = {}

    for season, group in filtered_df.groupby("season"):
        points = MultiPoint([(lon, lat) for lon, lat in zip(group["longitude"], group["latitude"])])

        hull = points.convex_hull if len(points.geoms) >= 3 else points.envelope
        zones[season] = hull

    # --------------------------- Folium Map ---------------------------
    st.subheader("🗺️ Migration Map")

    center_lat = filtered_df["latitude"].mean()
    center_lon = filtered_df["longitude"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
    colors = {"Winter": "blue", "Spring": "green", "Summer": "red", "Autumn": "orange"}

    for season, hull in zones.items():
        if isinstance(hull, Polygon):
            coords = [(lat, lon) for lon, lat in hull.exterior.coords]
            folium.Polygon(coords,
                           color=colors.get(season, "black"),
                           fill=True,
                           fill_opacity=0.3,
                           tooltip=f"{season} Zone").add_to(m)

    st_folium(m, width=900, height=500)

    st.success("✅ Migration map generated!")

else:
    st.info("Please upload a CSV file to continue.")
