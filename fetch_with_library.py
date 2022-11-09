from entsoe import EntsoePandasClient, mappings
import pandas as pd
import numpy as np

OUR_TIMEZONE="Europe/Brussels"

client = EntsoePandasClient(api_key="04f108f8-a6eb-4126-bdca-bed5fedc7717")

start = pd.Timestamp('201801010000', tz='Europe/Brussels')
end = pd.Timestamp('201901010000', tz='Europe/Brussels')
country_code = 'BE'  # Belgium
country_code_from = 'BE'  # France
country_code_to = 'NL' # Germany-Luxembourg

#import pdb; pdb.set_trace()
print(client.query_crossborder_flows(country_code_from, country_code_to, start=start, end=end))
#print(client.query_crossborder_flows(country_code_from, country_code_to, start=start, end=end))
df = pd.DataFrame(pd.date_range(start, end, freq="1H", inclusive="left"))
df.set_index(df.loc[:, 0])
print(df)
for country, neighbors in mappings.NEIGHBOURS.items():
	for neighbor in neighbors:
		country_from=country
		country_to=neighbor
		#try:
		print(country, neighbor)
		try:
			result = client.query_crossborder_flows(country_from, country_to, start=start, end=end).astype(np.float64).to_numpy()
			print(result)
			df[country_from + ">" + country_to] = result
			print(df)
			print(df.info())
		except:
			print("No data found for: {} to {}".format(country_from, country_to) )
