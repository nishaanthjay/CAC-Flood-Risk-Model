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
        print(f"Latitude: {coordinates['y']}, Longitude: {coordinates['x']}")
    else:
        print("No matches found for the given address.")