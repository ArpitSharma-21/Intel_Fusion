from geopy.geocoders import Nominatim
import pandas as pd
import plotly.express as px

geolocator = Nominatim(user_agent="intel_fusion")

def get_coordinates(location):
    try:
        loc = geolocator.geocode(location)
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None

def create_geo_map(locations):
    data = []

    for loc in set(locations):
        coords = get_coordinates(loc)
        if coords:
            data.append({
                "location": loc,
                "lat": coords[0],
                "lon": coords[1]
            })

    if not data:
        return None

    df = pd.DataFrame(data)

    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        hover_name="location",
        projection="natural earth",
        title="🌍 Geographical Intelligence Map"
    )
    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        geo=dict(
            bgcolor="#0e1117",
            showland=True,
            landcolor="#1e1e2e",
            showocean=True,
            oceancolor="#0e1117",
            showcountries=True,
            countrycolor="#444",
            showcoastlines=True,
            coastlinecolor="#444"
        )
    )

    return fig