import pandas as pd
import sys
import logging
import plotly.express as px
from util import available_zones
from entsoe.geo.utils import load_zones

LOG= logging.getLogger("plot_inflow")
TIMEZONE="Europe/Brussels"

def compute_inflows(timestamp: pd.Timestamp, data: str) -> pd.Series:
	# Round timestamp to nearest hour
	rounded_timestamp = timestamp
	rounded_timestamp = timestamp.floor(freq='H')
	if rounded_timestamp != timestamp:
		warn_string="Rounded timestamp {} down to {}."
		LOG.warning(warn_string.format(timestamp, rounded_timestamp))

	# Load data from input file
	raw_data = None
	try:
		raw_data = pd.read_csv(data, parse_dates=True, index_col=0)
	except:
		raise RuntimeError("Failed to read data from file {}".format(data))

	# Accumulate inflow for every bidding zone
	inflows = {}
	time_entry = raw_data.loc[rounded_timestamp]
	time_entry = time_entry.fillna(0)
	for name, values in time_entry.items():
		# Cast to string because name is a hashable (whatever that may be)
		country_from, country_to = str(name).split('>')
		inflows.setdefault(country_to, 0)
		inflows[country_to] += values

	inflows_df = pd.Series(inflows)
	return inflows_df


def plot_inflows(inflows: pd.Series, country_list: list[str]) -> None:
	geo_df = load_zones(available_zones, pd.Timestamp(202201010000))
	inflows.name = "inflows"
	df = geo_df.join(inflows)
	print(df.loc[:, 'inflows'])


	fig = px.choropleth(df,
		geojson=df.geometry,
		locations=df.index,
		color="inflows",
		projection="mercator",
		color_continuous_scale='greys')
	fig.update_geos(fitbounds="locations", visible=False)
	fig.update_coloraxes(showscale=False)
	fig.update_layout(width=512, height=512)
	fig.write_image("test.png")
	#fig.show()

def main():
	if len(sys.argv) < 2:
		print("Usage: plot_inflow.py <data_file>") 
	inflows = compute_inflows(pd.Timestamp("20200101000000", tz=TIMEZONE), sys.argv[1])
	plot_inflows(inflows, available_zones)
		

if __name__ == "__main__":
	main()
	