import os
import requests
from dotenv import load_dotenv
from math import radians, sin, cos, sqrt, atan2

# Load the .env file
load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("GOOGLE_API_KEY")

# Debugging: Print the API key to verify it's loaded
if not api_key:
    print("Error: API key is not set or is empty!")
else:
    print(f"API Key: {api_key}")

# Step 1: Geocode address to get latitude and longitude
def geocode_address(address, api_key):
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(geocode_url)
    geocode_data = response.json()

    # Check if the status is OK, otherwise print the error
    if geocode_data['status'] == 'OK':
        lat = geocode_data['results'][0]['geometry']['location']['lat']
        lng = geocode_data['results'][0]['geometry']['location']['lng']
        return lat, lng
    else:
        print(f"Error geocoding address: {geocode_data['status']}")
        return None, None

# Step 2: Find nearest road using Roads API
def find_nearest_road(lat, lng, api_key):
    roads_url = f"https://roads.googleapis.com/v1/nearestRoads?points={lat},{lng}&key={api_key}"
    response = requests.get(roads_url)
    roads_data = response.json()

    # Check if snappedPoints are available in the response
    if 'snappedPoints' in roads_data:
        nearest_road = roads_data['snappedPoints'][0]
        return nearest_road['location']['latitude'], nearest_road['location']['longitude']
    else:
        print("Error finding nearest road:", roads_data)
        return None, None

# Step 3: Calculate distance using Haversine formula (if needed)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of Earth in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c  # Distance in km
    return distance

# Example usage
address = "48 5th St NW, Atlanta, GA 30332"

# Geocode the address
lat, lng = geocode_address(address, api_key)
if lat and lng:
    print(f"Latitude: {lat}, Longitude: {lng}")
    
    # Find the nearest road
    nearest_lat, nearest_lng = find_nearest_road(lat, lng, api_key)
    if nearest_lat and nearest_lng:
        print(f"Nearest Road Latitude: {nearest_lat}, Nearest Road Longitude: {nearest_lng}")
        
        # Calculate the distance between the address and the nearest road
        distance = calculate_distance(lat, lng, nearest_lat, nearest_lng)
        print(f"Distance from {address} to nearest road: {distance} km")
