import os
import requests
from math import radians, sin, cos, sqrt, atan2, degrees
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("GOOGLE_API_KEY")

# Check if the API key is loaded
if not api_key:
    print("Error: API key is not set or is empty!")
else:
    print(f"API Key successfully loaded: {api_key[:5]}...")  # Print first 5 characters for validation

# Step 1: Geocode address to get latitude and longitude
def geocode_address(address, api_key):
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(geocode_url)
    geocode_data = response.json()

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

    if 'snappedPoints' in roads_data:
        nearest_road = roads_data['snappedPoints'][0]
        return nearest_road['location']['latitude'], nearest_road['location']['longitude']
    else:
        print("Error finding nearest road:", roads_data)
        return None, None

# Step 3: Calculate distance using Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of Earth in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c  # Distance in km
    return distance

# Step 4: Calculate bearing between two points
def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    delta_lon = lon2 - lon1
    x = sin(delta_lon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon)
    
    bearing = atan2(x, y)
    
    # Convert bearing from radians to degrees
    bearing = degrees(bearing)
    
    # Normalize bearing to be between 0 and 360
    bearing = (bearing + 360) % 360
    return bearing

# Main function to interact with the user
def main():
    address = input("Enter the address: ")

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
            
            # Calculate the bearing (angle) between the address and the nearest road
            bearing = calculate_bearing(lat, lng, nearest_lat, nearest_lng)
            print(f"Angle from {address} to nearest road: {bearing}°")

# Run the main function
if __name__ == "__main__":
    main()
