import pandas as pd
import entsoe as ee

API_KEY="04f108f8-a6eb-4126-bdca-bed5fedc7717"
TIMEZONE="Europe/Brussels"

client = ee.EntsoePandasClient(api_key=API_KEY)
start = pd.Timestamp('201501010000', tz=TIMEZONE)
end = pd.Timestamp('202201010000', tz=TIMEZONE)
df = pd.DataFrame({"datetime": pd.date_range(start, end, freq="1H", inclusive="left")})
df = df.set_index("datetime")
df.info()
country_to = "DE"
country_from = "BE"
result = client.query_crossborder_flows(country_from, country_to, start=start, end=end)
result.info()

