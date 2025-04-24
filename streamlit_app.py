
# streamlit_app.py
# To run: `streamlit run streamlit_app.py`

import streamlit as st
import gpxpy
import folium
import srtm
import math
from streamlit_folium import st_folium
from io import StringIO

st.set_page_config(page_title="Drive Alive Risk Analyzer", layout="wide")

st.title("Drive Alive - Route Risk Analyzer")
st.markdown("Upload your GPX file and we’ll identify hidden bends and crests based on curvature and elevation gain.")

uploaded_file = st.file_uploader("Choose a GPX file", type="gpx")

if uploaded_file:
    gpx = gpxpy.parse(uploaded_file)

    # Extract points
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))

    # Elevation data
    elevation_data = srtm.get_data()
    elevation_data.load()

    elevated_points = []
    for lat, lon in points:
        elev = elevation_data.get_elevation(lat, lon)
        if elev is None:
            elev = 0
        elevated_points.append((lat, lon, elev))

    # Calculate risk
    risk_segments = []
    for i in range(1, len(elevated_points) - 1):
        lat1, lon1, ele1 = elevated_points[i - 1]
        lat2, lon2, ele2 = elevated_points[i]
        lat3, lon3, ele3 = elevated_points[i + 1]

        elev_gain = max(ele1, ele2, ele3) - min(ele1, ele2, ele3)

        def angle(a, b, c):
            ba = (a[0] - b[0], a[1] - b[1])
            bc = (c[0] - b[0], c[1] - b[1])
            cos_angle = (ba[0]*bc[0] + ba[1]*bc[1]) / (
                math.sqrt(ba[0]**2 + ba[1]**2) * math.sqrt(bc[0]**2 + bc[1]**2))
            return math.degrees(math.acos(max(min(cos_angle, 1), -1)))

        ang = angle((lon1, lat1), (lon2, lat2), (lon3, lat3))
        risk_score = elev_gain + (180 - ang)

        risk_segments.append({
            "lat": lat2,
            "lon": lon2,
            "risk": risk_score
        })

    # Create map
    m = folium.Map(location=[points[0][0], points[0][1]], zoom_start=13)
    folium.PolyLine(points, color="blue", weight=3, opacity=0.8).add_to(m)

    for segment in risk_segments:
        if segment['risk'] > 40:
            folium.CircleMarker(
                location=(segment["lat"], segment["lon"]),
                radius=5,
                color="red",
                fill=True,
                fill_opacity=0.7,
                popup=f"Risk Score: {segment['risk']:.1f}"
            ).add_to(m)

    st.markdown("### Risk Map")
    st_folium(m, width=1000, height=600)
