from entsoe import EntsoePandasClient
import pandas as pd

client = EntsoePandasClient(api_key="04f108f8-a6eb-4126-bdca-bed5fedc7717")

start = pd.Timestamp('20171201', tz='Europe/Brussels')
end = pd.Timestamp('20180101', tz='Europe/Brussels')
country_code = 'BE'  # Belgium
country_code_from = 'FR'  # France
country_code_to = 'DE_LU' # Germany-Luxembourg
type_marketagreement_type = 'A01'
contract_marketagreement_type = "A01"

# methods that return Pandas Series
client.query_day_ahead_prices(country_code, start=start,end=end)