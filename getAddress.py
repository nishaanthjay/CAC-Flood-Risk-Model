import math #imports math

import requests #imports requests

address = input("Enter your address: ") #inputs address from user
url = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress" #Census geocoding API endpoint

params = {
    "address": address, 
    "benchmark": "Public_AR_Current",
    "vintage": "Current_Current", #vintage and benchmark parameters specify the dataset to use for geocoding
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

        geographies = match['geographies'] #get geographies from the match, then gets counties and states from the geographies
        counties = geographies.get('Counties', [])
        states = geographies.get('States', [])
        if counties and states:
            countyFips = counties[0]['GEOID'] #get the county FIPS code from the first county in the list
            stateAbbr = states[0]['STUSAB'] #get the state abbreviation from the first state in the list
            print(f"County FIPS: {countyFips}, State: {stateAbbr}")
        else:
            print("No county/state information found for the given address.") #for invalid address, prints no county/state information found for the given address and exits the program
            exit()
    else:
        print("No matches found for the given address.")
        exit()
else:
    print("Census geocoding request failed.")
    exit()

startFeet = 50 #starting distance in feet to check for flood zone boundaries
maxFeet = 2000 #maximum distance in feet to check for flood zone boundaries
precisionFeet = 10 #step size in feet for checking flood zone boundaries
lowFeet = startFeet
highFeet = None #maximum distance in feet where flood zones are found
bufferFeet = startFeet #buffer distance in feet
zonesAtLow = []
zonesAtHigh = []

while True:
    metersPerDegreeLat = 111320 #approximate number of meters per degree of latitude
    feetPerMeter = 3.28084 #approximate number of feet per meter
    degOffsetLat = bufferFeet / feetPerMeter / metersPerDegreeLat #convert buffer distance in feet to degrees of latitude
    degOffsetLon = degOffsetLat / math.cos(math.radians(y)) #convert buffer distance in feet to degrees of longitude, taking into account the latitude of the location

    xmin = x - degOffsetLon #calculate the minimum longitude for the bounding box
    xmax = x + degOffsetLon #calculate the maximum longitude for the bounding box
    ymin = y - degOffsetLat #calculate the minimum latitude for the bounding box
    ymax = y + degOffsetLat #calculate the maximum latitude for the bounding box

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
        "&rangeValues=&quantizationParameters=&featureEncoding=esriDefault&f=pjson") #constructs the URL for the FEMA flood zone query, including the bounding box coordinates and other parameters

    responseFlood = requests.get(floodUrl)
    if responseFlood.status_code == 200: #if the request is successful, parse the JSON response and extract the flood zone information
        floodData = responseFlood.json()
        zonesFound = [f['attributes'] for f in floodData.get('features', [])]
    else:
        zonesFound = []

    uniqueZones = set(z.get('FLD_ZONE', 'Unknown') for z in zonesFound) #extracts the unique flood zones found in the response
    if len(uniqueZones) > 1: #if more than one unique flood zone is found, set the highFeet variable to the current bufferFeet and break the loop
        highFeet = bufferFeet
        zonesAtHigh = zonesFound
        break

    zonesAtLow = zonesFound
    if bufferFeet >= maxFeet: #if the buffer distance exceeds the maximum distance, break the loop
        break

    lowFeet = bufferFeet
    bufferFeet = min(bufferFeet * 2, maxFeet) #double the buffer distance for the next iteration, but do not exceed the maximum distance

hitMaxCap = highFeet is None
if highFeet is not None:
    while highFeet - lowFeet > precisionFeet: #if the difference between highFeet and lowFeet is greater than the precisionFeet, continue to narrow down the search for flood zone boundaries
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
            "&rangeValues=&quantizationParameters=&featureEncoding=esriDefault&f=pjson") #constructs the URL for the FEMA flood zone query, including the bounding box coordinates and other parameters

        responseFlood = requests.get(floodUrl)
        if responseFlood.status_code == 200:
            zonesAtMid = [f['attributes'] for f in responseFlood.json().get('features', [])] #if the request is successful, parse the JSON response and extract the flood zone information
        else:
            zonesAtMid = []

        uniqueZones = set(z.get('FLD_ZONE', 'Unknown') for z in zonesAtMid)
        if len(uniqueZones) > 1:
            highFeet = bufferFeet
            zonesAtHigh = zonesAtMid #if more than one unique flood zone is found, set the highFeet variable to the current bufferFeet and break the loop
        else:
            lowFeet = bufferFeet

zonesFound = zonesAtHigh if highFeet is not None else zonesAtLow #if highFeet is not None, use zonesAtHigh; otherwise, use zonesAtLow
boundaryDistance = highFeet if highFeet is not None else bufferFeet #if highFeet is not None, use highFeet; otherwise, use bufferFeet
if zonesFound:
    uniqueZones = set(z.get('FLD_ZONE', 'Unknown') for z in zonesFound)
    if hitMaxCap: #if the maximum distance was hit without finding multiple flood zones, print a message indicating that no adjacent zone was found within the maximum distance
        print(f"No adjacent zone found within {boundaryDistance:.0f} ft.")
    elif len(uniqueZones) > 1: #if more than one unique flood zone is found, print a warning message indicating that the property is near a flood zone boundary and list the unique zones found
        print(f"WARNING: property is near a flood zone boundary at approximately {boundaryDistance:.0f} ft: {', '.join(sorted(uniqueZones))}")

    print(f"Flood Zone Information (within approximately {boundaryDistance:.0f} ft):")
    for attributes in zonesFound: #if attributes.get('FLD_ZONE') is not None:
        print(f"    Zone: {attributes.get('FLD_ZONE', 'Unknown')}, "
              f"Subtype: {attributes.get('ZONE_SUBTY', 'Unknown')}, "
              f"SFHA: {attributes.get('SFHA_TF', 'Unknown')}, "
              f"BFE: {attributes.get('STATIC_BFE', 'Unknown')}")
else:
    print("No flood zone information found for the given coordinates.")

claimsUrl = "https://www.fema.gov/api/open/v3/NfipClaims"
claimsParams = { #constructs the parameters for the FEMA NFIP claims query
    "$filter": f"countyCode eq '{countyFips}' and state eq '{stateAbbr}'",
    "$select": "dateOfLoss,yearOfLoss,ratedFloodZone,causeOfDamage,netBuildingPaymentAmount,netContentsPaymentAmount,floodEvent",
    "$top": 1000, #sets the maximum number of claims to retrieve in a single request
    "$count": "true", #requests the total count of claims matching the filter criteria
    "$format": "json"
}
responseClaims = requests.get(claimsUrl, params=claimsParams)
if responseClaims.status_code == 200: #if the request is successful, parse the JSON response and extract the claims information
    claimsData = responseClaims.json()
    claims = claimsData.get("NfipClaims", [])
    totalCount = claimsData.get("metadata", {}).get("count")

    if claims: #if there are claims, calculate the total building and contents payment amounts, extract the years of loss, and print the claims history information
        totalBuilding = sum(c.get("netBuildingPaymentAmount") or 0 for c in claims)
        totalContents = sum(c.get("netContentsPaymentAmount") or 0 for c in claims)
        years = [c["yearOfLoss"] for c in claims if c.get("yearOfLoss")]
        print("NFIP Claims History (county-level):")
        print(f"    Claims on record: {len(claims)}")
        print(f"    Total paid out: ${totalBuilding + totalContents:,.2f}") #print the total building and contents payment amounts
        print(f"    Years: {min(years)}–{max(years)}")

        if totalCount is not None and totalCount > len(claims): #if the total count of claims is greater than the number of claims retrieved, print a warning message indicating that the totals are undercounted and suggest adding pagination to get the full picture
            print(f"    WARNING: only {len(claims)} of {totalCount} total claims were pulled.")
            print(f"    Totals above are UNDERCOUNTED by {totalCount - len(claims)} claims. Add pagination ($skip) to get the full picture.")
    else:
        print("No NFIP claims found for this county.")
else:
    print("NFIP claims request failed.")