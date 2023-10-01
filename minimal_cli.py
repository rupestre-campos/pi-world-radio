import requests
import sys
import subprocess
from datetime import datetime
import time

def fetch_geojson_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad requests
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error fetching GeoJSON data:", e)
        return None

def list_countries(geojson_data):
    countries = []
    for feature in geojson_data['features']:
        country = feature['properties']['country']
        if country not in countries:
            countries.append(country)
    return sorted(countries)

def list_cities(geojson_data, selected_country):
    cities = []
    for feature in geojson_data['features']:
        country = feature['properties']['country']
        if country == selected_country:
            city = feature['properties']['title']
            cities.append(city)
    return sorted(cities)

def list_stations(geojson_data, selected_country, selected_city):
    stations = []
    for feature in geojson_data['features']:
        country = feature['properties']['country']
        city = feature['properties']['title']
        if country == selected_country and city == selected_city:
            station = feature['properties']['location_id']
            response = requests.get(f"http://localhost:8001/channels/{station}")
            data = response.json()
            return data["data"]["content"][0]["items"]


def play_stream(stream_url):
    try:
        # Use subprocess to execute the MPlayer command with the stream URL
        subprocess.run(['mplayer', stream_url])
    except Exception as e:
        print(f"Error: {e}")

def main():
    geojson_url = "http://localhost:8001/public/assets/js/geo_json.min.json"
    geojson_data = fetch_geojson_data(geojson_url)
    
    if geojson_data:
        countries = list_countries(geojson_data)
        print("Countries: ", end="")
        for i, country in enumerate(countries, start=1):
            print(f"{i}. {country} ", end="")
        
        selected_country_index = int(input("\nSelect a country (enter the corresponding number): ")) - 1
        selected_country = countries[selected_country_index]
        
        cities = list_cities(geojson_data, selected_country)
        print("Cities: ", end="")
        for i, city in enumerate(cities, start=1):
            print(f"{i}. {city} ", end="")
        
        selected_city_index = int(input("\nSelect a city (enter the corresponding number): ")) - 1
        selected_city = cities[selected_city_index]
        
        stations = list_stations(geojson_data, selected_country, selected_city)
        print("Stations: ")
        for i, station in enumerate(stations, start=1):

            print(f"{i}. {station['title']} ", )
            #print(station)
        
        selected_station_index = int(input("\nSelect a station (enter the corresponding number): ")) - 1
        selected_station = stations[selected_station_index]
        channel_id = selected_station["href"].split("/")[-1]
        print(f"Selected Station ID: {selected_station}")
        #play_stream(selected_station)
        val = int(time.time() * 1000)
        stream_url = f"https://radio.garden/api/ara/content/listen/{channel_id}/channel.mp3?{val}"
        print(stream_url)
        play_stream(stream_url)
if __name__ == "__main__":
    main()
