import requests
import xmltodict, json

# GET /api?documentType=A11&in_Domain=10YCZ-CEPS-----N&out_Domain=10YSK-SEPS-----K&periodStart=201512312300&periodEnd=201612312300

document_type="A11"
out_id = "10YGB----------A"
#out_id="10Y1001A1001A796" # Denmark SCA
in_id="10YBE----------2" # Germany
#in_id="10YDE-VE-------2" # Germany SCA
start_datetime="201701010000"
end_datetime="201712312359"
token="04f108f8-a6eb-4126-bdca-bed5fedc7717"

url_string = "https://web-api.tp.entsoe.eu/api?securityToken=" + token + "&documentType=" + document_type + "&in_Domain=" + in_id + "&out_Domain=" + out_id + "&periodStart=" + start_datetime +"&periodEnd=" + end_datetime
#url_string = "https://web-api.tp.entsoe.eu/api?securityToken=" + token + "&documentType=A11&out_Domain=10YCZ-CEPS-----N&in_Domain=10YSK-SEPS-----K&periodStart=201512312300&periodEnd=201612312300"

response = requests.get(url_string)
#print(response.content)
f = open("output.xml", "w")
f.write(str(response.content))
f.close()

o = xmltodict.parse(response.content)
json_output = json.dumps(o, indent=4)
f = open("json_output.json", "w")
f.write(json_output)
f.close()

print(type(response))

