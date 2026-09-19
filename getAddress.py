import requests

adress =input("Enter your address: ")
url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

params = {
    "address": adress,
    "benchmark": "Public_AR_Current",
    "format": "json"
}

response = requests.get(url, params=params)
if response.status_code == 200:
    data = response.json()
    if data['result']['addressMatches']:
        match = data['result']['addressMatches'][0]
        coordinates = match['coordinates']
        x = coordinates['x']
        y = coordinates['y']
        print(f"Latitude: {coordinates['y']}, Longitude: {coordinates['x']}")
    else:
        print("No matches found for the given address.")
floodUrl = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query?where=&text=&objectIds=&time=&timeRelation=esriTimeRelationOverlaps&geometry=%7B%22x%22%3A" + str(x) + "%2C%22y%22%3A" + str(y) + "%7D&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=FLD_ZONE%2C+ZONE_SUBTY%2C+SFHA_TF%2C+STATIC_BFE%2CDEPTH%2CVELOCITY&returnGeometry=false&returnTrueCurves=false&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&returnIdsOnly=false&returnCountOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&gdbVersion=&historicMoment=&returnDistinctValues=false&resultOffset=&resultRecordCount=&returnExtentOnly=false&sqlFormat=none&datumTransformation=&parameterValues=&rangeValues=&quantizationParameters=&featureEncoding=esriDefault&f=pjson"
responseFlood = requests.get(floodUrl)
if responseFlood.status_code == 200:
    floodData = responseFlood.json()
    if 'features' in floodData and floodData['features']:
        feature = floodData['features'][0]
        attributes = feature['attributes']
        print("Flood Zone Information:")
        print(f"    Flood Zone: {attributes.get('FLD_ZONE', 'Unknown')}")
        print(f"    Zone Subtype: {attributes.get('ZONE_SUBTY', 'Unknown')}")
        print(f"    SFHA: {attributes.get('SFHA_TF', 'Unknown')}")
        print(f"    Static BFE: {attributes.get('STATIC_BFE', 'Unknown')}")
        print(f"    Depth: {attributes.get('DEPTH', 'Unknown')}")
        print(f"    Velocity: {attributes.get('VELOCITY', 'Unknown')}")
    else:
        print("No flood zone information found for the given coordinates.")