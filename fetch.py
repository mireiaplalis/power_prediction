import os
import pandas as pd
import numpy as np
import entsoe as ee
import progressbar as pb
import logging
import sys

TIMEZONE="Europe/Brussels"
API_KEY="04f108f8-a6eb-4126-bdca-bed5fedc7717"

def get_progressbar():
	widgets = [
		"Fetching dataset:",
		' ', 
		pb.Percentage(), 
		' ', 
		pb.Bar(),
		' ',
		pb.AdaptiveETA()
		]
	bar = pb.ProgressBar(maxval=len(ee.mappings.NEIGHBOURS.items()), widgets=widgets)
	return bar

def main():
	if len(sys.argv) != 2:
		sys.stderr.write("Usage: fetch.py <output_file>")
		exit()
	filename = sys.argv[1]
	os.makedirs(os.path.dirname(filename), exist_ok=True)
	client = ee.EntsoePandasClient(api_key=API_KEY)
	log = logging.getLogger(__name__)

	# Progressbar for fun
	bar = get_progressbar()
	bar.start()

	# Initialize and fill dataframe
	start = pd.Timestamp('201501010000', tz=TIMEZONE)
	end = pd.Timestamp('202201010000', tz=TIMEZONE)
	df = pd.DataFrame({"datetime": pd.date_range(start, end, freq="1H", inclusive="left")})
	df = df.set_index("datetime")
	for i, (country, neighbors) in enumerate(ee.mappings.NEIGHBOURS.items()):
		for neighbor in neighbors:
			country_from=country
			country_to=neighbor
			success = False
			while not success:
				try:
					result = client.query_crossborder_flows(country_from, country_to, start=start, end=end)
					result.name = country_from + ">" + country_to
					df = df.join(result)
					success = True
				except ee.entsoe.NoMatchingDataError:
					msg = "No data found for: {} to {}"
					log.warning(msg.format(country_from, country_to))
					success = True
				except ee.entsoe.InvalidBusinessParameterError:
					msg = "Invalid business parameter reported for: {} to {}"
					log.warning(msg.format(country_from, country_to))
					success = True

			bar.update(i)

	# Write dataframe to file
	df.to_csv(filename)

if __name__ == "__main__": 
	main()