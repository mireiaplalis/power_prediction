import logging
import os
import pandas as pd
import plotly
from tqdm import tqdm
import plotly.express as px
from entsoe.geo.utils import load_zones
import numpy as np

TIMEZONE="Europe/Brussels"


class InflowPlotter:
	def __init__(self, inflow_data: str, zone_list: list[str]):
		self.zone_list = zone_list
		self.log = logging.getLogger("InflowPlotter")
		
		# Read dataframe
		self.inflow_data: pd.DataFrame
		try:
			self.inflow_data = pd.read_csv(inflow_data, parse_dates=True, index_col=0)
		except:
			raise RuntimeError("Failed to read data from file {}".format(inflow_data))
	

	def plot_timestamp(self, timestamp: pd.Timestamp) -> plotly.graph_objs.Figure:
		# Round timestamp to nearest hour
		rounded_timestamp = timestamp.floor(freq='H')
		if rounded_timestamp != timestamp:
			warn_string="Rounded timestamp {} down to {}."
			self.log.warning(warn_string.format(timestamp, rounded_timestamp))

		# Accumulate inflow for every bidding zone
		inflows = {}
		time_entry = self.inflow_data.loc[rounded_timestamp]
		time_entry = time_entry.fillna(0)
		for name, values in time_entry.items():
			# Cast to string because name is a hashable (whatever that may be)
			country_from, country_to = str(name).split('>')
			inflows.setdefault(country_to, 0)
			inflows[country_to] += values
		inflows = pd.Series(inflows)
		
		# Plot (save and show as desired)
		geo_df = load_zones(self.zone_list, rounded_timestamp.tz_localize(None))
		inflows.name = "inflows"
		df = geo_df.join(inflows)
		fig = px.choropleth(df,
			geojson=df.geometry,
			locations=df.index,
			color="inflows",
			projection="mercator",
			color_continuous_scale='greys')
		fig.update_geos(fitbounds="locations", visible=False)
		
		return fig
	
	def create_flow_matrix(self, timestamp: pd.Timestamp) -> np.ndarray:
		# Round timestamp to nearest hour
		rounded_timestamp = timestamp.floor(freq='H')
		if rounded_timestamp != timestamp:
			warn_string="Rounded timestamp {} down to {}."
			self.log.warning(warn_string.format(timestamp, rounded_timestamp))

		n_countries = len(self.zone_list)
		flow_matrix = np.zeros((n_countries, n_countries))

		ind = {}
		for i, country in enumerate(self.zone_list):
			ind[country] = i

		time_entry = self.inflow_data.loc[rounded_timestamp]
		time_entry = time_entry.fillna(0)
		for name, values in time_entry.items():
			# Cast to string because name is a hashable (whatever that may be)
			country_from, country_to = str(name).split('>')
			flow_matrix[ind[country_from]][ind[country_to]] = values
		return flow_matrix
		

	def generate_all(self, output_dir, res: int=512):
		# Create output directory if needed
		os.makedirs(output_dir, exist_ok=True)

		bar = tqdm(total=len(self.inflow_data.index))
		for index, _ in self.inflow_data.iterrows():
			#print(str(index))
			#print(index)
			index_str = str(index)
			figure = self.plot_timestamp(pd.Timestamp(index_str))
			figure.update_coloraxes(showscale=False)
			figure.update_layout(width=res, height=res)

			path = os.path.join(output_dir, index_str + ".png")
			figure.write_image(path, format="png", )

			bar.update()
		bar.close()