import sys
import os
import logging
from inflow_plotter import InflowPlotter
from util import available_map_zones

def main():
	log = logging.getLogger("generate_images")
	if len(sys.argv) != 4:
		log.critical("Usage: generate_matrices.py <dataset> <figure_output> <timestamp_output>")
	dataset_path = sys.argv[1]
	figure_output = sys.argv[2]
	timestamp_output = sys.argv[3]

	plotter = InflowPlotter(dataset_path, available_map_zones)
	plotter.generate_all(figure_output, timestamp_output, format="images")
	
if __name__ == "__main__":
	main()