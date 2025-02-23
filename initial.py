from google.cloud import vision
import os
import requests
from math import radians, sin, cos, sqrt, atan2, degrees
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import math


# Load the .env file
load_dotenv()

# Get the API key from environment variables (Google Maps API)
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


# Step 5: Get Google Street View Image
def get_street_view_image(lat, lng, api_key):
   # Google Street View Static API URL
   street_view_url = f"https://maps.googleapis.com/maps/api/streetview?size=600x300&location={lat},{lng}&key={api_key}"
  
   # Send the request and get the image
   response = requests.get(street_view_url)
  
   if response.status_code == 200:
       # Open and save the image
       image = Image.open(BytesIO(response.content))
       image.save("street_view_image.jpg")
       print("Street view image saved as street_view_image.jpg")
       return "street_view_image.jpg"
   else:
       print("Error retrieving street view image:", response.status_code)
       return None


def analyze_image_with_vision(image_path):
    # Initialize the Vision client
    client = vision.ImageAnnotatorClient()

    # Load the image
    with open(image_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)  # No 'types' module needed here

    # Call the Vision API to perform object localization
    response = client.object_localization(image=image)

    # Check for errors
    if response.error.message:
        raise Exception(f"Error: {response.error.message}")

    # Initialize variables to track total area and blocked area
    total_area = 0
    blocked_area = 0

    # Image dimensions (width and height) - use the image size for a more accurate area calculation
    image_width = 1  # These values should be set according to your image's size
    image_height = 1

    # Iterate through the detected objects
    for object_ in response.localized_object_annotations:
        # Print the detected objects and their confidence
        print(f"Object: {object_.name}, Confidence: {object_.score}")

        # Define a list of objects that could potentially block the building
        if object_.name.lower() in ["car", "person", "tree", "sign", "bush"]:  # List of blocking objects
            # Calculate the area of the object by its bounding box (normalized coordinates)
            object_area = (object_.bounding_poly.normalized_vertices[2].x - object_.bounding_poly.normalized_vertices[0].x) * \
                          (object_.bounding_poly.normalized_vertices[2].y - object_.bounding_poly.normalized_vertices[0].y)
            blocked_area += object_area
            print(f"Blocked Object: {object_.name}, Area: {object_area}")

        # Increment total area calculation (for simplicity, we count all objects here)
        total_area += (object_.bounding_poly.normalized_vertices[2].x - object_.bounding_poly.normalized_vertices[0].x) * \
                      (object_.bounding_poly.normalized_vertices[2].y - object_.bounding_poly.normalized_vertices[0].y)

    # Calculate the blocked percentage
    if total_area > 0:
        block_percentage = (blocked_area / total_area) * 100
        print(f"Total area blocked by objects: {block_percentage:.2f}%")
    else:
        print("No objects detected in the image.")
    return block_percentage

def calculate_visibility_score(distance, angle, obstruction_percent, alpha=0.1):
    
    # Step 1: Calculate the distance factor using exponential decay
    distance_factor = math.exp(-alpha * distance)  # Exponential decay for distance
    
    # Step 2: Calculate the angle factor using cosine
    # Convert angle to radians
    angle_radians = math.radians(angle)
    angle_factor = math.cos(angle_radians)  # Cosine of the angle
    
    # Step 3: Calculate the obstruction factor
    obstruction_factor = 1 - (obstruction_percent / 100)  # Fraction of visible storefront
    
    # Step 4: Calculate the total visibility score
    visibility_score = distance_factor * angle_factor * obstruction_factor
    
    # Ensure the score is between 0 and 1
    visibility_score = max(0, min(visibility_score, 1))
    
    return visibility_score

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

          
           # Get the Street View Image for the location
           image_path = get_street_view_image(lat, lng, api_key)
           if image_path:
               # Analyze the image using Google Vision API
                obstruct = analyze_image_with_vision(image_path)
                visib = calculate_visibility_score(distance, bearing, obstruct)
                print(visib)
    
    

# Run the main function
if __name__ == "__main__":
   main()
