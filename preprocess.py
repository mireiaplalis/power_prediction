import sys
from entsoe.mappings import NEIGHBOURS
import pandas as pd
from tqdm import tqdm

def preprocess(input_file, output_file):
	df = pd.read_csv(input_file, parse_dates=True, index_col=0)

	print("Data preprocessing")

	### Remove odd duplicates (they are also only one-way)
	df = df.drop(["FR>IT_NORD_FR"], axis=1)
	df = df.drop(["CH>IT_NORD_CH"], axis=1)


	### SUD, CALA mess: pretend IT_CALA exists everywhere
	ts = pd.Timestamp('2021-01-01 00:00:00+00:00')

	# The columns involving CALA need to be filled
	# Where needed, divide SUD in half, and make CALA equal to half-SUD
	print("Filling IT_CALA with data from IT_SUD where possible")
	for neighbor in NEIGHBOURS["IT_CALA"]:
		to_sud = str(neighbor + ">IT_SUD")
		to_cala = str(neighbor + ">IT_CALA")
		from_sud = str("IT_SUD>" + neighbor)
		from_cala = str("IT_CALA>" + neighbor)
		try: 
			if neighbor in NEIGHBOURS["IT_SUD"]:
				# Divide flow in half if CALA neighbor also borders SUD
				df.loc[(df.index < ts), to_sud] = df.loc[(df.index < ts), to_sud] / 2
				df.loc[(df.index < ts), from_sud] = df.loc[(df.index<ts), from_sud] / 2
				df.loc[(df.index < ts), to_cala] = df.loc[(df.index < ts), to_sud]
				df.loc[(df.index < ts), from_cala] = df.loc[(df.index < ts), from_cala]
			else:
				# If neighbor did not border SUD, we don't have data
				df.loc[(df.index < ts), to_cala] = 0
				df.loc[(df.index < ts), from_cala] = 0
				pass

		except KeyError:
			# happens sometimes, e.g. NO_2 is in DE_LU but not DE_AT_LU (sad)
			pass

	# Pad SUD>CALA and CALA>SUD with 0
	df.loc[:, "IT_SUD>IT_CALA"].fillna(0, inplace=True)
	df.loc[:, "IT_CALA>IT_SUD"].fillna(0, inplace=True)


	### DE/AT/LU mess: DE_LU and AT to be filled everywhere; then del DE_AT_LU
	ts = pd.Timestamp('2018-10-01 00:00:00+00:00')

	# Fill columns involving DE_LU using data from DE_AT_LU
	print("Filling DE_LU and AT with data from DE_AT_LU")
	for neighbor in NEIGHBOURS["DE_LU"]:
		to_dal = str(neighbor + ">DE_AT_LU")
		to_dl = str(neighbor + ">DE_LU")
		from_dal = str("DE_AT_LU>" + neighbor)
		from_dl = str("DE_LU>" + neighbor)
		try: 
			# Only divide power flow by half if neighbor also borders AT
			if neighbor in NEIGHBOURS["AT"]:
				df.loc[(df.index < ts), to_dl] = df.loc[(df.index < ts), to_dal] / 2
				df.loc[(df.index < ts), from_dl] = df.loc[(df.index < ts), from_dal] / 2
			else:
				df.loc[(df.index < ts), to_dl] = df.loc[(df.index < ts), to_dal]
				df.loc[(df.index < ts), from_dl] = df.loc[(df.index < ts), from_dal]
		except KeyError:
			# happens sometimes, e.g. NO_2 is in DE_LU but not DE_AT_LU (sad)
			pass

	# Fill columns involving AT using data from DE_AT_LU
	for neighbor in NEIGHBOURS["AT"]:
		to_dal = str(neighbor + ">DE_AT_LU")
		to_dl = str(neighbor + ">AT")
		from_dal = str("DE_AT_LU>" + neighbor)
		from_dl = str("AT>" + neighbor)
		try: 
			# Only divide power flow by half if neighbor also borders DE_LU
			if neighbor in NEIGHBOURS["DE_LU"]:
				df.loc[(df.index < ts), to_dl] = df.loc[(df.index < ts), to_dal] / 2
				df.loc[(df.index < ts), from_dl] = df.loc[(df.index < ts), from_dal] / 2
			else:
				df.loc[(df.index < ts), to_dl] = df.loc[(df.index < ts), to_dal]
				df.loc[(df.index < ts), from_dl] = df.loc[(df.index < ts), from_dal]
		except KeyError:
			# happens sometimes, e.g. NO_2 is in DE_LU but not DE_AT_LU (sad)
			pass

	# Pad DE_LU>AT and AT>DE_LU columns with 0
	df.loc[:, "DE_LU>AT"].fillna(0, inplace=True)
	df.loc[:, "AT>DE_LU"].fillna(0, inplace=True)

	# Drop columns involving DE_AT_LU
	df = df.loc[:, ~df.columns.str.contains("DE_AT_LU")]


	### Handle any remaining missing values
	deleted_count = 0
	filled_count = 0
	for name, _ in df.items():
		name = str(name)
		nan_count = df[name].isna().sum()
		if df[name].empty:
			print("DROPPING empty column {}".format(name))
			df = df.drop([name], axis=1)
			deleted_count += 1
		elif nan_count > 0:
			print("Column {} contains {} NaNs, FILLING with 0...".format(name, nan_count))
			df[name] = df[name].fillna(0)
			filled_count += 1
	
	print("Deleted {} columns".format(deleted_count))
	print("Filled {} columns".format(filled_count))


	df.to_csv(output_file)

def main(): 
	if len(sys.argv) < 3:
		print("Usage: {} <input_file> <output_file>".format(sys.argv[0]))
		exit()
	
	input_file = sys.argv[1]
	output_file = sys.argv[2]
	
	preprocess(input_file, output_file)

if __name__ == "__main__":
	main()