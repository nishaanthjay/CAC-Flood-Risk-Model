import math

import requests

address = input("Enter your address: ")
url = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"

params = {
    "address": address,
    "benchmark": "Public_AR_Current",
    "vintage": "Current_Current",
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

        geographies = match['geographies']
        counties = geographies.get('Counties', [])
        states = geographies.get('States', [])
        if counties and states:
            countyFips = counties[0]['GEOID']
            stateAbbr = states[0]['STUSAB']
            print(f"County FIPS: {countyFips}, State: {stateAbbr}")
        else:
            print("No county/state information found for the given address.")
            exit()
    else:
        print("No matches found for the given address.")
        exit()
else:
    print("Census geocoding request failed.")
    exit()

startFeet = 50
maxFeet = 2000
precisionFeet = 10
lowFeet = startFeet
highFeet = None
bufferFeet = startFeet
zonesAtLow = []
zonesAtHigh = []

while True:
    metersPerDegreeLat = 111320
    feetPerMeter = 3.28084
    degOffsetLat = bufferFeet / feetPerMeter / metersPerDegreeLat
    degOffsetLon = degOffsetLat / math.cos(math.radians(y))

    xmin = x - degOffsetLon
    xmax = x + degOffsetLon
    ymin = y - degOffsetLat
    ymax = y + degOffsetLat

    floodUrl = ("https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
        "?where=&text=&objectIds=&time=&timeRelation=esriTimeRelationOverlaps"
        f"&geometry=%7B%22xmin%22%3A{xmin}%2C%22ymin%22%3A{ymin}%2C%22xmax%22%3A{xmax}%2C%22ymax%22%3A{ymax}%7D"
        "&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects"
        "&distance=&units=esriSRUnit_Foot"
        "&relationParam=&outFields=FLD_ZONE%2C+ZONE_SUBTY%2C+SFHA_TF%2C+STATIC_BFE%2CDEPTH%2CVELOCITY"
        "&returnGeometry=false&returnTrueCurves=false&maxAllowableOffset=&geometryPrecision="
        "&outSR=&havingClause=&returnIdsOnly=false&returnCountOnly=false&orderByFields="
        "&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&gdbVersion="
        "&historicMoment=&returnDistinctValues=false&resultOffset=&resultRecordCount="
        "&returnExtentOnly=false&sqlFormat=none&datumTransformation=&parameterValues="
        "&rangeValues=&quantizationParameters=&featureEncoding=esriDefault&f=pjson")

    responseFlood = requests.get(floodUrl)
    if responseFlood.status_code == 200:
        floodData = responseFlood.json()
        zonesFound = [f['attributes'] for f in floodData.get('features', [])]
    else:
        zonesFound = []

    uniqueZones = set(z.get('FLD_ZONE', 'Unknown') for z in zonesFound)
    if len(uniqueZones) > 1:
        highFeet = bufferFeet
        zonesAtHigh = zonesFound
        break

    zonesAtLow = zonesFound
    if bufferFeet >= maxFeet:
        break

    lowFeet = bufferFeet
    bufferFeet = min(bufferFeet * 2, maxFeet)

hitMaxCap = highFeet is None
if highFeet is not None:
    while highFeet - lowFeet > precisionFeet:
        bufferFeet = (lowFeet + highFeet) / 2
        metersPerDegreeLat = 111320
        feetPerMeter = 3.28084
        degOffsetLat = bufferFeet / feetPerMeter / metersPerDegreeLat
        degOffsetLon = degOffsetLat / math.cos(math.radians(y))
        xmin = x - degOffsetLon
        xmax = x + degOffsetLon
        ymin = y - degOffsetLat
        ymax = y + degOffsetLat

        floodUrl = ("https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
            "?where=&text=&objectIds=&time=&timeRelation=esriTimeRelationOverlaps"
            f"&geometry=%7B%22xmin%22%3A{xmin}%2C%22ymin%22%3A{ymin}%2C%22xmax%22%3A{xmax}%2C%22ymax%22%3A{ymax}%7D"
            "&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects"
            "&distance=&units=esriSRUnit_Foot"
            "&relationParam=&outFields=FLD_ZONE%2C+ZONE_SUBTY%2C+SFHA_TF%2C+STATIC_BFE%2CDEPTH%2CVELOCITY"
            "&returnGeometry=false&returnTrueCurves=false&maxAllowableOffset=&geometryPrecision="
            "&outSR=&havingClause=&returnIdsOnly=false&returnCountOnly=false&orderByFields="
            "&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&gdbVersion="
            "&historicMoment=&returnDistinctValues=false&resultOffset=&resultRecordCount="
            "&returnExtentOnly=false&sqlFormat=none&datumTransformation=&parameterValues="
            "&rangeValues=&quantizationParameters=&featureEncoding=esriDefault&f=pjson")

        responseFlood = requests.get(floodUrl)
        if responseFlood.status_code == 200:
            zonesAtMid = [f['attributes'] for f in responseFlood.json().get('features', [])]
        else:
            zonesAtMid = []

        uniqueZones = set(z.get('FLD_ZONE', 'Unknown') for z in zonesAtMid)
        if len(uniqueZones) > 1:
            highFeet = bufferFeet
            zonesAtHigh = zonesAtMid
        else:
            lowFeet = bufferFeet

zonesFound = zonesAtHigh if highFeet is not None else zonesAtLow
boundaryDistance = highFeet if highFeet is not None else bufferFeet
if zonesFound:
    uniqueZones = set(z.get('FLD_ZONE', 'Unknown') for z in zonesFound)
    if hitMaxCap:
        print(f"No adjacent zone found within {boundaryDistance:.0f} ft.")
    elif len(uniqueZones) > 1:
        print(f"WARNING: property is near a flood zone boundary at approximately {boundaryDistance:.0f} ft: {', '.join(sorted(uniqueZones))}")

    print(f"Flood Zone Information (within approximately {boundaryDistance:.0f} ft):")
    for attributes in zonesFound:
        print(f"    Zone: {attributes.get('FLD_ZONE', 'Unknown')}, "
              f"Subtype: {attributes.get('ZONE_SUBTY', 'Unknown')}, "
              f"SFHA: {attributes.get('SFHA_TF', 'Unknown')}, "
              f"BFE: {attributes.get('STATIC_BFE', 'Unknown')}")
else:
    print("No flood zone information found for the given coordinates.")

claimsUrl = "https://www.fema.gov/api/open/v3/NfipClaims"
claimsParams = {
    "$filter": f"countyCode eq '{countyFips}' and state eq '{stateAbbr}'",
    "$select": "dateOfLoss,yearOfLoss,ratedFloodZone,causeOfDamage,netBuildingPaymentAmount,netContentsPaymentAmount,floodEvent",
    "$top": 1000,
    "$count": "true",
    "$format": "json"
}
responseClaims = requests.get(claimsUrl, params=claimsParams)
if responseClaims.status_code == 200:
    claimsData = responseClaims.json()
    claims = claimsData.get("NfipClaims", [])
    totalCount = claimsData.get("metadata", {}).get("count")

    if claims:
        totalBuilding = sum(c.get("netBuildingPaymentAmount") or 0 for c in claims)
        totalContents = sum(c.get("netContentsPaymentAmount") or 0 for c in claims)
        years = [c["yearOfLoss"] for c in claims if c.get("yearOfLoss")]
        print("NFIP Claims History (county-level):")
        print(f"    Claims on record: {len(claims)}")
        print(f"    Total paid out: ${totalBuilding + totalContents:,.2f}")
        print(f"    Years: {min(years)}–{max(years)}")

        if totalCount is not None and totalCount > len(claims):
            print(f"    WARNING: only {len(claims)} of {totalCount} total claims were pulled.")
            print(f"    Totals above are UNDERCOUNTED by {totalCount - len(claims)} claims. Add pagination ($skip) to get the full picture.")
    else:
        print("No NFIP claims found for this county.")
else:
    print("NFIP claims request failed.")