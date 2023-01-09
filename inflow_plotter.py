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

		# compute inflows and outflows and determine min and max
		self.inflows, self.outflows = self.aggregate_flows()
		self.min_inflow = self.inflows.min().min()
		self.max_inflow = self.inflows.max().max()
		self.min_outflow = self.outflows.min().min()
		self.max_outflow = self.outflows.max().max()

		# Get geopandas map
		self.zone_list = zone_list
		self.geo_df = load_zones(self.zone_list, MAP_TIMESTAMP.tz_localize(None))

		# Plotting details
		mplstyle.use('fast')
		self.fig, self.ax = plt.subplots(figsize=(2.56, 2.56))
		self.fig.tight_layout()
		self.fig.set_facecolor("black")
		self.ax.set_facecolor("black")
		self.ax.axis('off')
		self.ax.set_position([0, 0, 1, 1])

	def aggregate_flows(self):
		inflow_list = []
		outflow_list = []
		timestamp_list = []
		for index, _ in self.inflow_data.iterrows():
			index_str = str(index)
			timestamp = pd.Timestamp(index_str)
			inflows = {}
			outflows = {}
			for name, values in self.inflow_data.loc[timestamp].items():
				country_from, country_to = str(name).split('>')
				inflows.setdefault(country_to, 0)
				outflows.setdefault(country_from, 0)
				inflows[country_to] += values
				outflows[country_from] += values
			inflow_list.append(inflows)
			outflow_list.append(outflows)
			timestamp_list.append(timestamp)
		inflow_df = pd.DataFrame(data=inflow_list, index=timestamp_list)
		outflow_df = pd.DataFrame(data=outflow_list, index=timestamp_list)

		return inflow_df, outflow_df

	def plot_timestamp(self, timestamp: pd.Timestamp):
		# Round timestamp to nearest hour (should not be needed)
		rounded_timestamp = timestamp.floor(freq='H')
		if rounded_timestamp != timestamp:
			warn_string="Rounded timestamp {} down to {}."
			self.log.warning(warn_string.format(timestamp, rounded_timestamp))

		# Determine in- and outflows
		inflows = self.inflows.loc[timestamp]
		outflows = self.outflows.loc[timestamp]
		inflows.name = "inflows"
		outflows.name = "outflows"

		# Plot inflow
		df = self.geo_df.join(inflows)
		df.plot(
			column="inflows",
			cmap="gray",
			vmin=self.min_inflow,
			vmax=self.max_inflow,
			legend=False,
			antialiased=False,
			ax=self.ax
		)
		self.fig.canvas.draw()
		in_arr = np.array(self.fig.canvas.renderer.buffer_rgba())[:, :, 0]
		self.ax.clear()

		# Plot outflow
		df = self.geo_df.join(outflows)
		df.plot(
			column="outflows",
			cmap="gray",
			vmin=self.min_outflow,
			vmax=self.max_outflow,
			legend=False,
			antialiased=False,
			ax=self.ax
		)
		self.fig.canvas.draw()
		out_arr = np.array(self.fig.canvas.renderer.buffer_rgba())[:, :, 0]
		self.ax.clear()

		# Stack and return
		arr = np.stack((in_arr, out_arr), axis=-1)
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
				# Determine timestamp
				index_str = str(index)
				timestamp = pd.Timestamp(index_str)
				unix_timestamp = int(timestamp.timestamp())
				timestamp_list.append(unix_timestamp)

				# Generate desired format
				figure = None
				if format == "matrices":
					figure = self.create_flow_matrix(pd.Timestamp(index_str))
				elif format == "images":
					figure = self.plot_timestamp(pd.Timestamp(index_str))

				# Append
				figure_list.append(figure)
				bar.update()
		
		figure_array = np.expand_dims(np.array(figure_list), axis=-1)
		np.save(figure_output, figure_array)
		timestamp_array = np.array(timestamp_list, dtype='datetime64[s]')
		np.save(timestamp_output, timestamp_array)
		bar.close()