from entsoe.geo.utils import load_zones
import plotly.express as px
import pandas as pd

zones = ['NL', 'BE', 'DE_LU']

geo_df = load_zones(zones, pd.Timestamp(202201010000))
geo_df['value'] = range(1,len(geo_df)+1)

fig = px.choropleth(geo_df,
                   geojson=geo_df.geometry,
                   locations=geo_df.index,
                   color="value",
                   projection="mercator",
                   color_continuous_scale='rainbow')
fig.update_geos(fitbounds="locations", visible=False)
fig.show()