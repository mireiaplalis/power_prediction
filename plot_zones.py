from entsoe.geo.utils import load_zones
import plotly.express as px
import pandas as pd
import entsoe

avail_zones = [
    "AT", "BE", "BG", "CH", "CZ", "DE_LU", "DK_1", "DK_2", "EE",
    "ES", "FI", "FR", "GR", "HR", "HU", "IT_CNOR", 
    "IT_CSUD", "IT_NORD", "IT_SARD", "IT_SICI", "IT_SUD", "LT", 
    "LV", "NL", "NO_1", "NO_2", "NO_3", "NO_4", "NO_5", "PL", "PT", 
    "RO", "RS", "SE_1", "SE_2", "SE_3", "SE_4", "SI", "SK"]

geo_df = load_zones(avail_zones, pd.Timestamp(202201010000))
geo_df['value'] = range(1,len(geo_df)+1)

fig = px.choropleth(geo_df,
                   geojson=geo_df.geometry,
                   locations=geo_df.index,
                   color="value",
                   projection="mercator",
                   color_continuous_scale='rainbow')
fig.update_geos(fitbounds="locations", visible=False)
fig.show()