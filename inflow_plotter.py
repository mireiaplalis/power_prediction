import logging
import os
import io
import pandas as pd
import plotly
from tqdm import tqdm
import plotly.express as px
from entsoe.geo.utils import load_zones
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


TIMEZONE="Europe/Brussels"
MAP_TIMESTAMP = pd.Timestamp("2021-12-31 22:00:00+00:00")


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
		self.data_preprocessing()
	

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
		geo_df = load_zones(self.zone_list, MAP_TIMESTAMP.tz_localize(None))
		inflows.name = "inflows"
		df = geo_df.join(inflows)
		fig = px.choropleth(df,
			geojson=df.geometry,
			locations=df.index,
			color="inflows",
			projection="mercator",
			color_continuous_scale='greys')
		fig.update_geos(fitbounds="locations", visible=False)
		fig.show()
		return fig

	def data_preprocessing(self):
		self.inflow_data.fillna(0)
		print("Data preprocessing")
		bar = tqdm(total=len(self.inflow_data.index))
		for index, _ in self.inflow_data.iterrows():
			index_str = str(index)
			timestamp = pd.Timestamp(index_str)
			rounded_timestamp = timestamp.floor(freq='H')
			if timestamp.tz_localize(None) < pd.Timestamp('2021-01-01'):
				time_entry = self.inflow_data.loc[rounded_timestamp]
				for name, _ in time_entry.items():
					country_from, country_to = str(name).split('>')
					if country_from == "IT_SUD":
						self.inflow_data["IT_SUD"+">"+country_to] /= 2
						self.inflow_data["IT_CALA"+">"+country_to] = self.inflow_data["IT_SUD"+">"+country_to]
					if country_to == "IT_SUD":
						it = 0
						self.inflow_data[country_from+">"+"IT_SUD"] /= 2
						self.inflow_data[country_from+">"+"IT_CALA"] = self.inflow_data[country_from+">"+"IT_SUD"]	
			if timestamp.tz_localize(None) < pd.Timestamp('2018-10-01'):
				time_entry = self.inflow_data.loc[rounded_timestamp]
				for name, _ in time_entry.items():
					country_from, country_to = str(name).split('>')
					if country_from == "DE_AT_LU":
						self.inflow_data["DE_LU"+">"+country_to] = self.inflow_data["DE_AT_LU"+">"+country_to] / 2
						self.inflow_data["AT"+">"+country_to] = self.inflow_data["DE_AT_LU"+">"+country_to] / 2
					if country_to == "DE_AT_LU":
						it = 0
						self.inflow_data[country_from+">"+"DE_LU"] = self.inflow_data[country_from+">"+"DE_AT_LU"] / 2
						self.inflow_data[country_from+">"+"AT"] = self.inflow_data[country_from+">"+"DE_AT_LU"] / 2	
			bar.update()
	
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
		

	def generate_all(self, figure_output, timestamp_output, res: int=256, format="matrices"):
		# Create output directory if needed
		os.makedirs(os.path.dirname(figure_output), exist_ok=True)
		os.makedirs(os.path.dirname(timestamp_output), exist_ok=True)

		bar = tqdm(total=len(self.inflow_data.index))
		figure_list = []
		timestamp_list = []
		
		##### DEBUG #####
		for i, (index, _) in enumerate(self.inflow_data.iterrows()):
			if i % (365 * 24) == 0:
				index_str = str(index)
				timestamp = pd.Timestamp(index_str)
				unix_timestamp = int(timestamp.timestamp())
				timestamp_list.append(unix_timestamp)

				figure = None

				if format == "matrices":
					figure = self.create_flow_matrix(pd.Timestamp(index_str))
					figure_list.append(figure)

				elif format == "images":
					figure = self.plot_timestamp(pd.Timestamp(index_str))
					figure.update_coloraxes(showscale=False)
					figure.update_layout(width=res, height=res)
					buf = io.BytesIO(figure.to_image(format="png"))
					img = Image.open(buf)
					figure_array = np.asarray(img)
					figure_list.append(figure)


				bar.update()
		
		figure_array = np.expand_dims(np.array(figure_list), axis=-1)
		np.save(figure_output, figure_array)
		timestamp_array = np.array(timestamp_list, dtype='datetime64[s]')
		np.save(timestamp_output, timestamp_array)
		bar.close()