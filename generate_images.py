import sys
import os
import logging
from inflow_plotter import InflowPlotter
from util import available_zones

def main():
	log = logging.getLogger("generate_images")
	if len(sys.argv) != 3:
		log.critical("Usage: generate_images.py <dataset> <output_dir>")
	dataset_path = sys.argv[1]
	output_dir = sys.argv[2]
	zone_list = available_zones

	plotter = InflowPlotter(dataset_path, available_zones)
	plotter.generate_all(output_dir)
	
if __name__ == "__main__":
	main()