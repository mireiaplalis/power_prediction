import logging
import os
import io
import pandas as pd
import geopandas as gpd
import plotly
from tqdm import tqdm
import plotly.express as px
from entsoe.geo.utils import load_zones
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
import time


TIMEZONE="Europe/Brussels"
MAP_TIMESTAMP = pd.Timestamp("2021-12-31 22:00:00+00:00")


class InflowPlotter:
	def __init__(self, inflow_data: str, zone_list: list[str]):
		self.log = logging.getLogger("InflowPlotter")

		# Read dataframe
		self.inflow_data: pd.DataFrame
		try:
			self.inflow_data = pd.read_csv(inflow_data, parse_dates=True, index_col=0)
		except:
			raise RuntimeError("Failed to read data from file {}".format(inflow_data))

		# Get geopandas map
		self.zone_list = zone_list
		self.geo_df = load_zones(self.zone_list, MAP_TIMESTAMP.tz_localize(None))

		# Plotting things
		mplstyle.use('fast')
		self.fig, self.ax = plt.subplots(figsize=(2.56, 2.56))
		self.fig.tight_layout()
		self.fig.set_facecolor("black")
		self.ax.set_facecolor("black")
		self.ax.axis('off')
		self.ax.set_position([0, 0, 1, 1])
		self.min_flow = self.inflow_data.min().min()
		self.max_flow = self.inflow_data.max().max()
		print("min flow: {}".format(self.min_flow))
		print("max flow: {}".format(self.max_flow))

	

	def plot_timestamp(self, timestamp: pd.Timestamp):
		comp_time = time.time()
		# Round timestamp to nearest hour
		rounded_timestamp = timestamp.floor(freq='H')
		if rounded_timestamp != timestamp:
			warn_string="Rounded timestamp {} down to {}."
			self.log.warning(warn_string.format(timestamp, rounded_timestamp))

		# Accumulate inflow for every bidding zone
		inflows = {}
		time_entry = self.inflow_data.loc[rounded_timestamp]
		for name, values in time_entry.items():
			# Cast to string because name is a hashable (whatever that may be)
			country_from, country_to = str(name).split('>')
			inflows.setdefault(country_to, 0)
			inflows[country_to] += values
		inflows = pd.Series(inflows)
		print("POLAN: ")
		print(inflows["IT_NORD"])
		
		# Plot (save and show as desired)
		inflows.name = "inflows"
		df = self.geo_df.join(inflows)
		print("Comp time: {}".format(time.time() - comp_time))
		# fig = px.choropleth(df,
		# 	geojson=df.geometry,
		# 	locations=df.index,
		# 	color="inflows",
		# 	projection="mercator",
		# 	color_continuous_scale='greys')
		# fig.update_geos(fitbounds="locations", visible=False)
		plt_time = time.time()
		df.plot(
			column="inflows",
			cmap="gray",
			vmin=self.min_flow,
			vmax=self.max_flow,
			legend=False,
			antialiased=False,
			ax=self.ax
		)
		self.fig.canvas.draw()
		print("plt time: {}".format(time.time() - plt_time))
		arr_time = time.time()
		arr = np.array(self.fig.canvas.renderer.buffer_rgba())[:, :, 0]
		print("arr shape: {}".format(arr.shape))
		self.ax.clear()
		print("arr time: {}".format(time.time() - arr_time))
		return arr
	
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
			#if i % (365 * 100) == 0:
				index_str = str(index)
				timestamp = pd.Timestamp(index_str)
				unix_timestamp = int(timestamp.timestamp())
				timestamp_list.append(unix_timestamp)

				figure = None

				if format == "matrices":
					figure = self.create_flow_matrix(pd.Timestamp(index_str))
					figure_list.append(figure)

				elif format == "images":
					iteration_time = time.time()
					plot_time = time.time()
					figure = self.plot_timestamp(pd.Timestamp(index_str))
					print("Plot time: {}".format(time.time() - plot_time))
					# update_time = time.time()
					# figure.update_coloraxes(showscale=False)
					# figure.update_layout(width=res, height=res)
					# print("Update time: {}".format(time.time()-update_time))
					# conversion_time = time.time()
					# buf = io.BytesIO(figure.to_image(format="png"))
					# img = Image.open(buf)
					# figure_array = np.asarray(img)
					# figure_list.append(figure)
					figure_list.append(figure)
					#print("Conversion time: {}".format(time.time()-conversion_time))
					print("iteration time: {}".format(time.time()-plot_time))


				bar.update()
		
		figure_array = np.expand_dims(np.array(figure_list), axis=-1)
		np.save(figure_output, figure_array)
		timestamp_array = np.array(timestamp_list, dtype='datetime64[s]')
		np.save(timestamp_output, timestamp_array)
		bar.close()